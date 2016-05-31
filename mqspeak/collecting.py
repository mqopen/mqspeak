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

import logging
import collections
from mqreceive.data import DataIdentifier
from mqspeak.data import Measurement

#class DataCollector:
#    """!
#    Object for collecting received data from MQTT brokers. This object is also resposible
#    to provide received data to each update buffer. If some of update buffers becomes full,
#    its content is given to ChannelUpdateSupervisor object.
#    """
#
#    ## @var updateBuffers
#    # List of UpdateBuffer objects.
#
#    ## @var channelUpdateSupervisor
#    # UpdateSupervisor object.
#
#    def __init__(self, updateBuffers, channelUpdateSupervisor):
#        """!
#        Initiate DataCollector object.
#
#        @param updateBuffers List of UpdateBuffer objects.
#        @param channelUpdateSupervisor UpdateSupervisor object.
#        """
#        self.updateBuffers = updateBuffers
#        self.channelUpdateSupervisor = channelUpdateSupervisor
#
#    def onMessage(self, broker, topic, data):
#        self.onNewData(DataIdentifier(broker, topic), data);
#
#    def onNewData(self, dataIdentifier, data):
#        """!
#        Notify data collector when new data is available.
#
#        @param dataIdentifier Data identification.
#        @param data Payload.
#        """
#        for updateBuffer in self.updateBuffers:
#            self.tryBuffer(updateBuffer, dataIdentifier, data)
#
#    def tryBuffer(self, updateBuffer, dataIdentifier, data):
#        """!
#        Try to update buffer.
#
#        @param updateBuffer Buffer to update.
#        @param dataIdentifier Data identification.
#        @param data Payload.
#        """
#        try:
#            if updateBuffer.isUpdateRelevant(dataIdentifier):
#                updateBuffer.updateReceivedData(dataIdentifier, data)
#                if updateBuffer.isComplete():
#                    d = updateBuffer.getData()
#                    updateBuffer.reset()
#                    measurement = Measurement.currentMeasurement(d)
#                    self.channelUpdateSupervisor.dataAvailable(updateBuffer.channel, measurement)
#                else:
#                    # Notify update supervisor about arrived data.
#                    self.channelUpdateSupervisor.dataAvailable(updateBuffer)
#        except TopicException as ex:
#            logging.getLogger().info("Topic exception: {}".format(ex))

#class _UpdateBuffer:
#    """!
#    Class for buffering required data set before sending them out.
#    """
#
#    ## @var channel
#    # Updated channel object.
#
#    ## @var dataIdentifiers
#    # Iterable of DataIdentifier objects.
#
#    ## @var dataMapping
#    # The {DataIdentifier: value} mapping.
#
#    def __init__(self, channel, dataIdentifiers):
#        """!
#        Initiate UpdateBuffer object.
#
#        @param channel Channel identification object.
#        @param dataIdentifiers Iterable of DataIdentifier objects.
#        """
#        self.channel = channel
#        self.dataIdentifiers = dataIdentifiers
#        self.reset()
#
#    def isComplete(self):
#        """!
#        Check if all required data are buffered.
#
#        @return True if all required data are buffered, False otherwise.
#        """
#        return not any(x is None for x in self.dataMapping.values())
#
#    def isUpdateRelevant(self, dataIdentifier):
#        """!
#        Check if update is relevant to this channel.
#
#        @param dataIdentifier Update data identifier.
#        @return True if update is relevant, False otherwise
#        """
#        return dataIdentifier in self.dataMapping
#
#    def updateReceivedData(self, dataIdentifier, value):
#        """!
#        Update received data.
#
#        @param dataIdentifier Data identification.
#        @param value Data content.
#        @throws TopicException If unwanted topic is updated.
#        """
#        if not self.isUpdateRelevant(dataIdentifier):
#            raise TopicException("Illegal topic update: {}".format(dataIdentifier))
#        else:
#            self.dataMapping[dataIdentifier] = value
#
#    def getData(self):
#        """!
#        Get dictionary with buffered data.
#
#        @return Buffered data.
#        """
#        return self.dataMapping
#
#    def reset(self):
#        """!
#        Clear buffered data.
#        """
#        self.dataMapping = {}
#        for dataIdentifier in self.dataIdentifiers:
#            self.dataMapping[dataIdentifier] = None
#
#    def __str__(self):
#        """!
#        Convert UpdateBuffer object to string.
#
#        @return String.
#        """
#        return "UpdateBuffer({}: {})".format(self.channel, self.dataIdentifiers)
#
#    def __repr__(self):
#        """!
#        Convert UpdateBuffer object to representation string.
#
#        @return Representation string.
#        """
#        return "<{}>".format(self.__str__())

class BaseUpdateBuffer:
    """!
    Class for buffering required data set before sending them out.
    """

    ## @var dataIdentifiers
    # Iterable of DataIdentifier objects.

    ## @var dataMapping
    # The {DataIdentifier: value} mapping.

    def __init__(self, dataIdentifiers):
        """!
        Initiate UpdateBuffer object.

        @param dataIdentifiers Iterable of DataIdentifier objects.
        """
        self.dataIdentifiers = dataIdentifiers
        self.reset()

    def isComplete(self):
        """!
        Check if all required data are buffered.

        @return True if all required data are buffered, False otherwise.
        """
        return not any(x is None for x in self.dataMapping.values())

    def isUpdateRelevant(self, dataIdentifier):
        """!
        Check if update is relevant to this channel.

        @param dataIdentifier Update data identifier.
        @return True if update is relevant, False otherwise
        """
        return dataIdentifier in self.dataMapping

    def updateReceivedData(self, dataIdentifier, value):
        """!
        Update received data. Override in subclass.

        @param dataIdentifier Data identification.
        @param value Data content.
        @throws TopicException If unwanted topic is updated.
        """
        if not self.isUpdateRelevant(dataIdentifier):
            raise TopicException("Illegal topic update: {}".format(dataIdentifier))
        else:
            self.handleUpdateReceivedData(dataIdentifier, value)
            self.hasData = True

    def handleUpdateReceivedData(self, dataIdentifier, value):
        """!
        Update received data. Override in subclass.

        @param dataIdentifier Data identification.
        @param value Data content.
        @throws TopicException If unwanted topic is updated.
        """
        raise NotImplementedError("Override this mehod in sub-class")

    def getData(self):
        """!
        Get dictionary with buffered data. Override in subclass.

        @return Buffered data.
        """
        raise NotImplementedError("Override this mehod in sub-class")

    def getMeasurement(self):
        """!
        Get current measurement with stored data.

        @return Measureent object.
        """
        return Measurement.currentMeasurement(self.getData())

    def getMissingDataIdentifiers(self):
        """!
        Get iterable of data identifiers which doesn't have stored data.
        """
        for dataIdentifier, value in self.dataMapping.items():
            if value is None:
                yield dataIdentifier

    def hasAnyData(self):
        """!
        Check if udate buffer has stored any data.

        @return True if there are stored any data, False otherwise.
        """
        return self.hasData

    def reset(self):
        """!
        Clear buffered data.
        """
        self.dataMapping = {}
        for dataIdentifier in self.dataIdentifiers:
            self.dataMapping[dataIdentifier] = None
        self.hasData = False

    def __str__(self):
        """!
        Convert UpdateBuffer object to string.

        @return String.
        """
        return "{}({})".format(self.__class__.__name__, self.dataMapping)

    def __repr__(self):
        """!
        Convert UpdateBuffer object to representation string.

        @return Representation string.
        """
        return "<{}>".format(self.__str__())

class LastValueUpdateBuffer(BaseUpdateBuffer):
    """!
    Keeps only last value. When some value is updated, the preveous value is lost.

    Updater can hold any kind of data.
    """

    def handleUpdateReceivedData(self, dataIdentifier, value):
        self.dataMapping[dataIdentifier] = value

    def getData(self):
        return self.dataMapping

class AverageUpdateBuffer(BaseUpdateBuffer):
    """!
    Calculate arithmetic average value. Each new value is stored in internal buffer.
    getData() method returns data mapping with calculated average value.
    """

    def handleUpdateReceivedData(self, dataIdentifier, value):
        try:
            value = float(value)
            if self.dataMapping[dataIdentifier] is None:
                self.dataMapping[dataIdentifier] = []
            self.dataMapping[dataIdentifier].append(value)
        except ValueError as ex:
            logging.getLogger().info("Can't data convert to number: {}".format(value))

    def getData(self):
        mapping = {}
        for dataIdentifier, valueList in self.dataMapping.items():
            if valueList is not None:
                mapping[dataIdentifier] = float(sum(valueList)) / len(valueList)
            else:
                mapping[dataIdentifier] = None
        return mapping

class ChangeValueBuffer(BaseUpdateBuffer):
    """!
    Store all change updates.
    """
    def handleUpdateReceivedData(self, dataIdentifier, value):
        if self.dataMapping[dataIdentifier] is None:
            self.dataMapping[dataIdentifier] = collections.deque()
        if len(self.dataMapping[dataIdentifier]) > 1 and self.dataMapping[dataIdentifier][-1] != value:
            self.dataMapping[dataIdentifier].append(value)

    def getData(self):
        mapping = {}
        for dataIdentifier, valueList in self.dataMapping.items():
            if valueList is not None and len(valueList) > 1:
                mapping[dataIdentifier] = valueList[0]
            else:
                mapping[dataIdentifier] = None
        return mapping

    def reset(self):
        """!
        Reset will not delete all data.
        """
        hasData = False
        for valueList in self.dataMapping.values():
            if valueList is not None and len(valueList) > 1:
                valueList.popleft()
            if not hasData and len(valueList) > 1:
                hasData = True
        self.hasData = hasData

class TopicException(Exception):
    """!
    Update buffer related errors.
    """
