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

from mqreceive.data import DataIdentifier
from mqspeak.data import Measurement

class DataCollector:
    """!
    Object for collecting received data from MQTT brokers. This object is also resposible
    to provide received data to each update buffer. If some of update buffers becomes full,
    its content is given to ChannelUpdateSupervisor object.
    """

    ## @var updateBuffers
    # List of UpdateBuffer objects.

    ## @var channelUpdateSupervisor
    # UpdateSupervisor object.

    def __init__(self, updateBuffers, channelUpdateSupervisor):
        """!
        Initiate DataCollector object.

        @param updateBuffers List of UpdateBuffer objects.
        @param channelUpdateSupervisor UpdateSupervisor object.
        """
        self.updateBuffers = updateBuffers
        self.channelUpdateSupervisor = channelUpdateSupervisor

    def onMessage(self, broker, topic, data):
        self.onNewData(DataIdentifier(broker, topic), data);

    def onNewData(self, dataIdentifier, data):
        """!
        Notify data collector when new data is available.

        @param dataIdentifier Data identification.
        @param data Payload.
        """
        for updateBuffer in self.updateBuffers:
            self.tryBuffer(updateBuffer, dataIdentifier, data)

    def tryBuffer(self, updateBuffer, dataIdentifier, data):
        """!
        Try to update buffer.

        @param updateBuffer Buffer to update.
        @param dataIdentifier Data identification.
        @param data Payload.
        """
        try:
            updateBuffer.updateReceivedData(dataIdentifier, data)
            if updateBuffer.isComplete():
                d = updateBuffer.getData()
                updateBuffer.reset()
                measurement = Measurement.currentMeasurement(d)
                self.channelUpdateSupervisor.dataAvailable(updateBuffer.channel, measurement)
        except TopicException as ex:
            pass

class UpdateBuffer:
    """!
    Object for buffering reqired data set before delivering them to ThingSpeak.
    """

    ## @var channel
    # Updated channel.

    ## @var dataIdentifiers
    # Iterable of DataIdentifier objects.

    ## @var dataDict
    # The {DataIdentifier: value} mapping.

    def __init__(self, channel, dataIdentifiers):
        """!
        Initiate UpdateBuffer object.

        @param channel Channel identification object.
        @param dataIdentifiers Iterable of DataIdentifier objects.
        """
        self.channel = channel
        self.dataIdentifiers = dataIdentifiers
        self.reset()

    def isComplete(self):
        """!
        Check if all required data are buffered.

        @return True if all required data are buffered, False otherwise.
        """
        return not any(x is None for x in self.dataDict.values())

    def updateReceivedData(self, dataIdentifier, value):
        """!
        Update received data.

        @param dataIdentifier Data identification.
        @param value Data content.
        @throws TopicException If unnessesary topic is updated.
        """
        if dataIdentifier not in self.dataDict:
            raise TopicException("Illegal topic update: {}".format(dataIdentifier))
        else:
            self.dataDict[dataIdentifier] = value

    def getData(self):
        """!
        Get dictionary with buffered data.

        @return Buffered data.
        """
        if not self.isComplete():
            raise TopicException("Some topic data is missing")
        else:
            return self.dataDict

    def reset(self):
        """!
        Clear buffered data.
        """
        self.dataDict = dict()
        for dataIdentifier in self.dataIdentifiers:
            self.dataDict[dataIdentifier] = None

    def __str__(self):
        """!
        Convert UpdateBuffer object to string.

        @return String.
        """
        return "UpdateBuffer({}: {})".format(self.channel, self.dataIdentifiers)

    def __repr__(self):
        """!
        Convert UpdateBuffer object to representation string.

        @return Representation string.
        """
        return "<{}>".format(self.__str__())

class TopicException(Exception):
    """!
    Update buffer related errors.
    """
