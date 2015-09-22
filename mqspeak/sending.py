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
import sys
import threading
import urllib.parse
from mqspeak.system import System

class ChannelUpdateDispatcher:
    """
    Dispatching new update threads.
    """

    def __init__(self, sender):
        """
        sender: sender object
        """
        self.sender = sender
        self.dispatchLock = threading.Semaphore(0)
        self.running = False
        self.updateQueue = collections.deque()

    @classmethod
    def createThingSpeakUpdateDispatcher(cls, channelConvertMapping):
        """
        channelConvertMapping: mapping {channel: channelParamConverter}
        """
        return cls(ThingSpeakSender(channelConvertMapping))

    def updateAvailable(self, channel, measurement, resultNotify):
        """
        Notify main thread when new data is available
        """
        self.updateQueue.append((channel, measurement, resultNotify))
        self.dispatchLock.release()

    def sendJobDone(self, result):
        """
        notify updater
        """
        (returnCode, updater) = result
        updater.notifyUpdateResult(returnCode)

    def run(self):
        """
        Start update dispatcher main loop.
        """
        self.running = True
        while self.running:
            self.dispatchLock.acquire()

            # check for stop() method call
            if not self.running:
                return

            # start send thread
            (channel, measurement, resultNotify) = self.updateQueue.popleft()
            self.dispatch(channel, measurement, resultNotify)

    def stop(self):
        """
        Stop dispatcher thread.
        """
        self.running = False
        self.dispatchLock.release()

    def dispatch(self, channel, measurement, updater):
        """
        Dispatch new ThingSpeak update thread.

        channel: updated channel
        measurement: update data
        updater: notified object with update results
        """
        sendThread = threading.Thread(
            target = SendRunner(
                self.sender,
                channel,
                measurement,
                updater,
                self))
        sendThread.start()

class ThingSpeakSender:
    """
    Class for sending data to ThingSpeak. This class send measurements to URL api.thingspeak.com
    using HTTPS method. It also parses send result and checks if transfer was successful.
    """

    def __init__(self, channelConvertMapping):
        """
        channelConvertMapping: mapping {channel: channelParamConverter}
        """
        self.channelConvertMapping = channelConvertMapping

    def send(self, channel,  measurement):
        """
        Send measurement to ThinkSpeak and return set with results:
        (responseStatus, responseReason, responseData)
        """
        try:
            params = self.channelConvertMapping[channel].convert(measurement)
            params.update({'api_key': channel.apiKey})
            conn = http.client.HTTPSConnection("api.thingspeak.com")
            conn.request("POST", "/update", urllib.parse.urlencode(params))
            response = conn.getresponse()

            # catch UnicodeDecodeError when some mess is received
            data = None
            responseRaw = response.read()
            try:
                data = responseRaw.decode("utf-8")
            except UnicodeError as ex:
                print("Can't decode response data: {0}".format(responseRaw), file=sys.stderr)
                data = "<Decode error>"
            conn.close()
            status = response.status
            reason = response.reason

            if System.verbose:
                print("Channel {0} response: {1} {2}: {3}".format(channel, status, reason, data))
            result = (status, reason, data)
            success = self._checkSendResult(result)
            return UpdateResult(success)
        except BaseException as ex:
            print("Send exception: {0}".format(ex), file = sys.stderr)
            return UpdateResult(False)

    def _checkSendResult(self, result):
        (status, reason, data) = result
        if status != 200:
            print("Response status error: {0} {1} - {2}.".format(status, reason, data), file = sys.stderr)
            return False
        elif data == "0":
            print("Data send error: ThingSpeak responded with return code 0.", file = sys.stderr)
            return False
        return True

class SendRunner:
    """
    Callable wrapper class for sending data to ThingSpeak in separate thread.
    """

    def __init__(self, sender, channel, measurement, updater, jobNotify):
        """
        sender: sender object. This object must implement send(channel,  measurement) method.
        channel: channel description object
        measurement: measured data
        updater: updater object which will be called by dispatcher after send job is done
        jobNotify: listener object called after data send.
        """
        self.sender = sender
        self.channel = channel
        self.measurement = measurement
        self.updater = updater
        self.jobNotify = jobNotify

    def __call__(self):
        """
        Thread code.
        """
        try :
            result = (self.sender.send(self.channel, self.measurement), self.updater)
            self.jobNotify.sendJobDone(result)
        except Exception as ex:
            self.jobNotify.sendJobDone(ex)

class UpdateResult:
    """
    Encapsulate update result.
    """

    def __init__(self, success):
        """
        Initiate update result.

        success: indicate if update was successful or not
        """
        self.success = success

    def wasSuccessful(self):
        return self.success
