import datetime
import threading
import urllib.parse
import http.client
import sys

class ChannelUpdateDistributor:
    """
    Object responsible for distributing data to each channel update
    """
    
    def __init__(self, sender, destinationDescriptors):
        """
        sender: sender object
        destinationDescriptors: (channel, updateDescriptor)
            channel:
            updateDescriptor:
                sendType:
                sendPeriod: timedelta object
        """
        self.dispatchers = []

    def dataAvailable(self, source, measurement):
        """
        Distribute new data to all dispatchers.
        
        source: broker object which provides new data
        measurement: new data obejct
        """
        for dispatcher in self.dispatchers:
            dispatcher.dataAvailable(source, measurement)

class SendDispatcher:

    def __init__(self, sender, sendPeriod):
        """
        sender: sender object
        sendPeriod: timedelta object
        """
        self.sender = sender
        self.sendPeriod = sendPeriod
        self.lastSend = datetime.datetime.min
        self.dispatchLock = threading.Semaphore(0)
        self.jobLock = threading.Semaphore(1)
        self.isSendJobRunning = False

    def dataAvailable(self, source, measurement):
        """
        Notify main thread when new data is available
        """
        self.jobLock.acquire()
        if not self.isSendJobRunning and self._isPeriodExpired():
            self.measurement = measurement
            self.dispatchLock.release()
        self.jobLock.release()

    def run(self):
        try:
            self.running = True
            while self.running:
                self.dispatchLock.acquire()
                # check for stop() method call
                if not self.running:
                    return
                # start send thread
                self.isSendJobRunning = True
                threading.Thread(target = SendRunner(self.sender, self.measurement, self)).start()
        except KeyboardInterrupt as ex:
            pass

    def stop():
        self.running = False
        self.dispatchLock.release()

    def sendJobDone(self, result):
        self.jobLock.acquire()
        self.isSendJobRunning = False
        self._updateSendPeriod()
        if isinstance(result, Exception):
            print("Data send error: {0}.".format(result), file = sys.stderr)
        else:
            self._checkSendResult(result)
        self.jobLock.release()

    def _isPeriodExpired(self):
        return (datetime.datetime.now() - self.lastSend) > self.sendPeriod

    def _updateSendPeriod(self):
        self.lastSend = datetime.datetime.now()

    def _checkSendResult(self, result):
        (status, reason, data) = result
        if status != 200:
            print("Response status error: {0} {1} - {2}.".format(status, reason, data), file = sys.stderr)
        elif data == "0":
            print("Data send error: ThingSpeak responded with return code 0.", file = sys.stderr)

class ThingSpeakSender:

    def __init__(self, paramConverter, writeKey):
        self.paramConverter = paramConverter
        self.writeKey = writeKey

    def send(self, measurement):
        """
        Send measurement to ThinkSpeak and return set with results:
        (responseStatus, responseReason, responseData)
        """
        params = self.paramConverter.convert(measurement)
        params.update({'api_key': self.writeKey})
        conn = http.client.HTTPSConnection("api.thingspeak.com")
        conn.request("POST", "/update", urllib.parse.urlencode(params))
        response = conn.getresponse()
        data = response.read().decode("utf-8")
        conn.close()
        return (response.status, response.reason, data)

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
