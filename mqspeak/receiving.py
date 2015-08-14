import threading
import paho.mqtt.client as mqtt
from mqspeak.data import Measurement

class BrokerThreadPoolManager:
    """
    Manage broker receiving threads
    """
    
    def __init__(self, listenDescriptors, dataListener):
        """
        listenDescriptors: listen descriptor iterable object
        dataListener: listener object to deliver received updates
        """
        self.listenDescriptors = listenDescriptors
        self.dataListener = dataListener
        self.clients = []
    
    def start(self):
        """
        Start all receiving threads.
        """
        for listenDescriptor in self.listenDescriptors:
            client = BrokerReceiver(listenDescriptor, self.dataListener)
            self.clients.append(client)
            threading.Thread(target = client).start()

    def stop(self):
        """
        Stop all receving threads.
        """
        for client in self.clients:
            client.stop()

class BrokerReceiver:
    """
    Broker receiving thread
    """
    
    def __init__(self,  listenDescriptor, dataListener):
        """
        listenDescriptor: set containing following fields: (broker, subscription, updateCollector)
            broker: broker descriptor object
            updateCollector: decsriptor for topic subscribe
            updateCollector: object which describes which data have to be received before to call dataListener
        dataListener: listener object to deliver received updates
        """
        (self.broker, self.subsciption, self.updateCollector) = listenDescriptor
        self.dataListener = dataListener
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        if self.broker.isAuthenticationRequired():
            self.client.username_pw_set(self.broker.user, self.broker.password)
    
    def __call__(self):
        keepAliveInterval = 60
        self.client.connect(self.broker.host, self.broker.port, keepAliveInterval)
        self.client.loop_forever()
    
    def on_connect(self, client, userdata, flags, rc):
        """
        The callback for when the client receives a CONNACK response from the server.
        """
        print("Broker {0} connected with result code: {1}.".format(self.broker.name, rc))
        for sub in self.subsciption:
            self.client.subscribe(sub)

    def on_message(self, client, userdata, msg):
        """
        The callback for when a PUBLISH message is received from the server.
        """
        try:
            self.updateCollector.updateReceivedData(msg.topic, msg.payload.decode("utf-8"))
            if self.updateCollector.isComplete():
                data = self.updateCollector.getData()
                self.updateCollector.reset()
                self.dataListener.dataAvailable(Measurement.currentMeasurement(data))
        except TopicException as ex:
            # not relevant topic update, do nothing
            pass
    
    def stop(self):
        self.client.disconnect()

class UpdateCollector:
    """
    Object for describing required data fields before delivering them to ThingSpeak.
    """

    def __init__(self, dataIdentifierIterable):
        """
        dataIdentifierIterable: iterable of DataIdentifier objects
        """
        self.dataIdentifierIterable = dataIdentifierIterable
        self.reset()
    
    def isComplete(self):
        return not any(x is None for x in self.dataDict.values())
    
    def updateReceivedData(self, dataIdentifier, value):
        """
        throws TopicException: if unnessesary topic is updated
        """
        if dataIdentifier not in self.dataDict:
            raise TopicException("Illegal topic update: {}".format(dataIdentifier))
        else:
            self.dataDict[dataIdentifier] = value
    
    def getData(self):
        if not self.isComplete():
            raise TopicException("Some topic data is missing")
        else:
            return self.dataDict
    
    def reset(self):
        self.dataDict = dict()
        for dataIdentifier in self.dataIdentifierIterable:
            self.dataDict[dataIdentifier] = None

class TopicException(Exception):
    pass
