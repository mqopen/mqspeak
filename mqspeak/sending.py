import datetime
import threading
import urllib.parse
import http.client
import sys

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

    @classmethod
    def createThingSpeakUpdateDispatcher(cls, channelConvertMapping):
        """
        channelConvertMapping: mapping {channel: channelParamConverter}
        """
        return cls(channelConvertMapping)

    def updateAvailable(self, channelIdentifier, measurement, resultNotify):
        """
        Notify main thread when new data is available
        """

    def sendJobDone(self, result):
        """
        notify updater
        """

    def _checkSendResult(self, result):
        (status, reason, data) = result
        if status != 200:
            print("Response status error: {0} {1} - {2}.".format(status, reason, data), file = sys.stderr)
        elif data == "0":
            print("Data send error: ThingSpeak responded with return code 0.", file = sys.stderr)

    def run(self):
        self.running = True
        while self.running:
            self.dispatchLock.acquire()
            # check for stop() method call
            if not self.running:
                return
            # start send thread

    def stop(self):
        self.running = False
        self.dispatchLock.release()

    def dispatch(self, channel, measurement, updater):
        """
        Dispatch new ThingSpeak update thread

        channel: updated channel
        measurement: update data
        updater: notified object with update results
        """
        threading.Thread(
                target = SendRunner(self.sender, channel, self.measurement, updater)
            ).start()

class ThingSpeakSender:

    def __init__(self, channelConvertMapping):
        """
        channelConvertMapping: mapping {channel: channelParamConverter}
        """
        self.channelConvertMapping = channelConvertMapping

    def send(self, measurement):
        """
        Send measurement to ThinkSpeak and return set with results:
        (responseStatus, responseReason, responseData)
        """
        #params = self.paramConverter.convert(measurement)
        #params.update({'api_key': self.writeKey})
        #conn = http.client.HTTPSConnection("api.thingspeak.com")
        #conn.request("POST", "/update", urllib.parse.urlencode(params))
        #response = conn.getresponse()
        #data = response.read().decode("utf-8")
        #conn.close()
        #return (response.status, response.reason, data)

class SendRunner:
    """
    Callable wrapper class for sending data to ThingSpeak in separae thread.
    """

    def __init__(self, sender, measurement, jobNotify):
        """
        jobNotify: listener object called after data send.
        """
        self.sender = sender
        self.measurement = measurement
        self.jobNotify = jobNotify

    def __call__(self):
        try :
            result = self.sender.send(self.measurement)
            self.jobNotify.sendJobDone(result)
        except Exception as ex:
            self.jobNotify.sendJobDone(ex)
