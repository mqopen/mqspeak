# Copyright (C) Ivo Slanina <ivo.slanina@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import collections
import datetime
import http.client
import threading
import logging
import urllib.parse
from mqspeak.channel import ChannelType

class ChannelUpdateDispatcher:
    """!
    Dispatching new update threads.
    """

    ## @var channelSenders
    # Channel sendres mapping.

    ## @var dispatchLock
    # Mutual exclusion for update job dispatching.

    ## @var running
    # Keep track if dispatcher is running.

    ## @var updateQueue
    # Queue of pending updates.

    def __init__(self, channelConvertMapping):
        """!
        Initiate ChannelUpdateDispatcher object.

        @param channelConvertMapping Mapping {channel: channelParamConverter}.
        """
        self.channelSenders = self.createChannelSenders(channelConvertMapping)
        self.dispatchLock = threading.Semaphore(0)
        self.running = False
        self.updateQueue = collections.deque()

    def createChannelSenders(self, channelConvertMapping):
        """!
        Crate channel senders mapping.

        @param channelConvertMapping ChannelConvertMapping object.
        @return Senders mapping.
        """
        channelSenders = {}
        channelSenders[ChannelType.thingspeak] = ThingSpeakSender(channelConvertMapping)
        channelSenders[ChannelType.phant] = PhantSender(channelConvertMapping)
        return channelSenders

    def updateAvailable(self, channel, measurement, resultNotify):
        """!
        Notify main thread when new data is available.

        @param channel
        @param measurement
        @param resultNotify
        """
        self.updateQueue.append((channel, measurement, resultNotify))
        self.dispatchLock.release()

    def sendJobDone(self, result):
        """!
        Notify updater.

        @param result
        """
        (returnCode, updater) = result
        updater.notifyUpdateResult(returnCode)

    def run(self):
        """!
        Start update dispatcher main loop.
        """
        self.running = True
        while self.running:
            self.dispatchLock.acquire()

            # check for stop() method call
            if not self.running:
                return

            # start send thread
            channel, measurement, resultNotify = self.updateQueue.popleft()
            self.dispatch(channel, measurement, resultNotify)

    def stop(self):
        """!
        Stop dispatcher thread.
        """
        if self.running:
            self.running = False
            self.dispatchLock.release()

    def dispatch(self, channel, measurement, updater):
        """!
        Dispatch new ThingSpeak update thread.

        @param channel Updated channel.
        @param measurement Update data.
        @param updater Notified object with update results.
        """
        sendThread = threading.Thread(
            target = SendRunner(
                self.channelSenders[channel.channelType],
                channel,
                measurement,
                updater,
                self))
        sendThread.start()

class BaseSender:
    """!
    Sender base class.
    """

    ## @var channelConvertMapping
    # Mapping {channel: channelParamConverter}.

    def __init__(self, channelConvertMapping):
        """!
        Initiate Sender base class.

        @param channelConvertMapping Mapping {channel: channelParamConverter}.
        """
        self.channelConvertMapping = channelConvertMapping

    def send(self, channel, measurement):
        """!
        Send measurement.

        @param channel Updated channel object.
        @param measurement Measured data.
        """
        success = False
        try:
            logging.getLogger().info(
                "Sending data to channel {}: {}...".format(channel, measurement))
            status, reason, responseBytes = self.fetch(channel, measurement)
            response = self.decodeResponseData(responseBytes)
            logging.getLogger().info(
                "Channel {} response: {} {}: {}".format(channel, status, reason, response))
            result = (status, reason, response)
            success = self.checkSendResult(result)
        except BaseException as ex:
            logging.getLogger().info("Send exception: {}".format(ex))
        finally:
            return UpdateResult(success)

    def decodeResponseData(self, responseBytes):
        """!
        Decode response data.

        @param responseBytes
        @return Decoded data or decode error message.
        """
        data = None
        try:
            data = responseBytes.decode("utf-8").strip()
        except UnicodeError as ex:
            logging.getLogger().error("Can't decode response data: {}".format(responseBytes))
            data = "<Decode error>"
        finally:
            return data

    def fetch(self, channel, measurement):
        """!
        Upload data to channel.

        @param channel Channel identification object.
        @param measurement Uploaded data.
        """
        raise NotImplementedError("Override this mehod in sub-class")

    def checkSendResult(self, result):
        """!
        Check if data upload was succcessful.

        @param result Tuple of (status, reason, response).
        """
        raise NotImplementedError("Override this mehod in sub-class")

class ThingSpeakSender(BaseSender):
    """!
    Class for sending data to ThingSpeak. This class send measurements to URL api.thingspeak.com
    using HTTPS method. It also parses send result and checks if transfer was successful.
    """

    def fetch(self, channel, measurement):
        """!
        @copydoc BaseSender::fetch()
        """
        body = self.channelConvertMapping[channel].convert(measurement)
        body.update({'created_at': measurement.time.isoformat(sep = ' ')})
        body.update({'api_key': channel.apiKey})
        bodyEncoded = urllib.parse.urlencode(body)
        conn = http.client.HTTPSConnection("api.thingspeak.com", timeout = 30)
        conn.request("POST", "/update", bodyEncoded)
        response = conn.getresponse()
        status = response.status
        reason = response.reason
        responseBytes = response.read()
        conn.close()
        return status, reason, responseBytes

    def checkSendResult(self, result):
        """!
        @copydoc BaseSender::checkSendResult()
        """
        status, reason, data = result
        if status != 200:
            logging.getLogger().error("Response status error: {} {} - {}.".format(status, reason, data))
            return False
        try:
            entries = int(data)
            if entries == 0:
                logging.getLogger().error("Data send error: ThingSpeak responded with return code 0.")
                return False
        except ValueError as ex:
            logging.getLogger().error("Data send error: ThingSpeak responded with unexpected response: {}".format(repr(data)))
            return False
        return True

class PhantSender(BaseSender):
    """!
    Send data to Phant server.
    """

    def fetch(self, channel, measurement):
        """!
        @copydoc BaseSender::fetch()
        """
        body = self.channelConvertMapping[channel].convert(measurement)
        bodyEncoded = urllib.parse.urlencode(body)
        headers = {"Phant-Private-Key": channel.apiKey,
                    "Content-Type": "application/x-www-form-urlencoded"}
        conn = http.client.HTTPConnection("data.sparkfun.com", timeout = 30)
        conn.request("POST", "/input/{}".format(channel.channelID), bodyEncoded, headers=headers)
        response = conn.getresponse()
        status = response.status
        reason = response.reason
        responseBytes = response.read()
        conn.close()
        return status, reason, responseBytes

    def checkSendResult(self, result):
        """!
        @copydoc BaseSender::checkSendResult()
        """
        (status, reason, data) = result
        if status != 200:
            logging.getLogger().error("Response status error: {} {} - {}.".format(status, reason, data))
            return False
        return True

class SendRunner:
    """!
    Callable wrapper class for sending data to ThingSpeak in separate thread.
    """

    ## @var sender
    # Sender object. This object must implement send(channel,  measurement) method.

    ## @var channel
    # Channel description object.

    ## @var measurement
    # Measured data.

    ## @var updater
    # Updater object which will be called by dispatcher after send job is done.

    ## @var jobNotify
    # Listener object called after data send.

    def __init__(self, sender, channel, measurement, updater, jobNotify):
        """!
        Initiate SendRunner object.

        @param sender Sender object. This object must implement send(channel,  measurement) method.
        @param channel Channel description object.
        @param measurement Measured data.
        @param updater Updater object which will be called by dispatcher after send job is done.
        @param jobNotify Listener object called after data send.
        """
        self.sender = sender
        self.channel = channel
        self.measurement = measurement
        self.updater = updater
        self.jobNotify = jobNotify

    def __call__(self):
        """!
        Thread code.
        """
        try :
            result = (self.sender.send(self.channel, self.measurement), self.updater)
            self.jobNotify.sendJobDone(result)
        except Exception as ex:
            self.jobNotify.sendJobDone(ex)

class UpdateResult:
    """!
    Encapsulate update result.
    """

    ## @var success
    # Flag if update was successful.

    def __init__(self, success):
        """!
        Initiate update result.

        @param success Indicate if update was successful or not
        """
        self.success = success

    def wasSuccessful(self):
        """!
        Check if UpdateResul was successful.

        @return True if was sucessful, False otherwise.
        """
        return self.success
