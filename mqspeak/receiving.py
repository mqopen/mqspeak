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

from mqspeak.data import DataIdentifier
import threading
import socket
import os
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

    receiverID = 0

    def __init__(self,  listenDescriptor, dataCollector):
        """
        listenDescriptor: set containing following fields: (broker, subscription)
            broker: broker descriptor object
            subscription:
        dataCollector: listener object to deliver received updates
        """
        (self.broker, self.subsciption) = listenDescriptor
        self.dataCollector = dataCollector
        self.clientID = self._createClientID()
        self.client = mqtt.Client(client_id = self.clientID)
        self._registerCallbacks()
        if self.broker.isAuthenticationRequired():
            self.client.username_pw_set(self.broker.user, self.broker.password)

    def _createClientID(self):
        clientID = "mqspeak-{0}-{1}-{2}".format(socket.gethostname(), os.getpid(), BrokerReceiver.receiverID)
        BrokerReceiver.receiverID += 1
        return clientID

    def _registerCallbacks(self):
        self.client.on_connect = self.onConnect
        self.client.on_disconnect = self.onDisconnect
        self.client.on_message = self.onMessage
        self.client.on_subscribe = self.onSubscribe
        self.client.on_unsubscribe = self.onUnsubscribe
        self.client.on_log = self.onLog

    def __call__(self):
        keepAliveInterval = 60
        self.client.connect(self.broker.host, self.broker.port, keepAliveInterval)
        self.client.loop_forever()

    def onConnect(self, client, userdata, flags, rc):
        """
        The callback for when the client receives a CONNACK response from the server.
        """
        print("Client {0} ({1} [{2}:{3}]): [{4}] {5}.".format(self.clientID, self.broker.name, self.broker.host, self.broker.port, rc, self._getClientConnectionStatus(rc)))
        for sub in self.subsciption:
            (result, mid) = self.client.subscribe(sub)

    def _getClientConnectionStatus(self, rc):
        if rc == 0:
            return "Connection successful"
        elif rc == 1:
            return "Connection refused - incorrect protocol version"
        elif rc == 2:
            return "Connection refused - invalid client identifier"
        elif rc == 3:
            return "Connection refused - server unavailable"
        elif rc == 4:
            return "Connection refused - bad username or password"
        elif rc == 5:
            return "Connection refused - not authorised"
        else:
            return "Unknown return code: {0}".format(rc)

    def onDisconnect(self, client, userdata, rc):
        print("Client dicsconnect: {0}".format(rc))

    def onMessage(self, client, userdata, msg):
        """
        The callback for when a PUBLISH message is received from the server.
        """
        dataID = DataIdentifier(self.broker, msg.topic)
        data = msg.payload.decode("utf-8")
        self.dataCollector.onNewData(dataID, data)

    def onSubscribe(self, client, userdata, mid, granted_qos):
        pass

    def onUnsubscribe(self, client, userdata, mid):
        pass

    def onLog(self, client, userdata, level, buf):
        pass

    def stop(self):
        self.client.disconnect()

class ThreadManagerException(Exception):
    """
    Indicate BrokerThreadManager error
    """
