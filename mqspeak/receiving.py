from mqspeak.data import DataIdentifier
import threading
import paho.mqtt.client as mqtt

class BrokerThreadManager:
    """
    Manage broker receiving threads
    """

    def __init__(self, listenDescriptors, dataCollector):
        """
        listenDescriptors: listen descriptor iterable object
            broker: broker descriptor object
            subsriptionIterable:
        dataCollector: DataCollector object
        """
        self.clients = [BrokerReceiver(x, dataCollector) for x in listenDescriptors]
        self.isThreadsRunning = False

    def start(self):
        """
        Start all receiving threads.
        """
        if self.isThreadsRunning:
            raise ThreadManagerException("Broker threads are already running")
        self.isThreadsRunning = True
        for client in self.clients:
            threading.Thread(target = client).start()

    def stop(self):
        """
        Stop all receving threads.
        """
        if not self.isThreadsRunning:
            raise ThreadManagerException("Broker threads are already stopped")
        self.isThreadsRunning = False
        for client in self.clients:
            client.stop()

class BrokerReceiver:
    """
    Broker receiving thread
    """

    def __init__(self,  listenDescriptor, dataCollector):
        """
        listenDescriptor: set containing following fields: (broker, subscription, updateCollector)
            broker: broker descriptor object
            subscription:
        dataCollector: listener object to deliver received updates
        """
        (self.broker, self.subsciption) = listenDescriptor
        self.dataCollector = dataCollector
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
        print("Broker {0} [{1}:{2}] connected with result code: {3}.".format(self.broker.name, self.broker.host, self.broker.port, rc))
        for sub in self.subsciption:
            self.client.subscribe(sub)

    def on_message(self, client, userdata, msg):
        """
        The callback for when a PUBLISH message is received from the server.
        """
        dataID = DataIdentifier(self.broker, msg.topic)
        print("received: {0} - {1}".format(dataID, msg.payload.decode("utf-8")))
        self.dataCollector.onNewData(dataID, msg.payload.decode("utf-8"))

    def stop(self):
        self.client.disconnect()

class ThreadManagerException(Exception):
    """
    Indicate BrokerThreadManager error
    """
