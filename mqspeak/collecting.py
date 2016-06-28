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
import copy
from mqreceive.data import DataIdentifier
from mqspeak.data import Measurement

class BaseUpdateBuffer:
    """!
    Class for buffering required data set before sending them out.
    """

    ## @var dataIdentifiers
    # Iterable of DataIdentifier objects.

    def __init__(self, dataIdentifiers):
        """!
        Initiate UpdateBuffer object.

        @param dataIdentifiers Iterable of DataIdentifier objects.
        """
        self.dataIdentifiers = dataIdentifiers

    def isComplete(self):
        """!
        Check if all required data are buffered.

        @return True if all required data are buffered, False otherwise.
        """
        raise NotImplementedError("Override this mehod in sub-class")

    def isUpdateRelevant(self, dataIdentifier):
        """!
        Check if update is relevant to this channel.

        @param dataIdentifier Update data identifier.
        @return True if update is relevant, False otherwise
        """
        return dataIdentifier in self.dataIdentifiers

    def updateReceivedData(self, dataIdentifier, value):
        """!
        Update received data.

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
        raise NotImplementedError("Override this mehod in sub-class")

    def getMissingDataIdentifiers(self):
        """!
        Get iterable of data identifiers which doesn't have stored data.
        """
        raise NotImplementedError("Override this mehod in sub-class")

    def hasAnyData(self):
        """!
        Check if udate buffer has stored any data.

        @return True if there are stored any data, False otherwise.
        """
        raise NotImplementedError("Override this mehod in sub-class")

    def reset(self):
        """!
        Clear buffered data.
        """
        raise NotImplementedError("Override this mehod in sub-class")

    def __str__(self):
        """!
        Convert UpdateBuffer object to string.

        @return String.
        """
        return "{}({})".format(self.__class__.__name__, self.dataIdentifiers)

    def __repr__(self):
        """!
        Convert UpdateBuffer object to representation string.

        @return Representation string.
        """
        return "<{}>".format(self.__str__())

class SingleValueUpdateBuffer(BaseUpdateBuffer):
    """!
    Base class for update buffers which are update over time and they store a
    single value.
    """

    ## @var dataMapping
    # The {DataIdentifier: value} mapping.

    ## @var hasData
    # Boolean inicated that buffer stores any data. Private.

    def __init__(self, dataIdentifiers):
        BaseUpdateBuffer.__init__(self, dataIdentifiers)
        self.dataMapping = {}
        for dataIdentifier in dataIdentifiers:
            self.dataMapping[dataIdentifier] = None
        self.hasData = False

    def updateReceivedData(self, dataIdentifier, value):
        if not self.isUpdateRelevant(dataIdentifier):
            raise TopicException("Illegal topic update: {}".format(dataIdentifier))
        self.handleUpdateReceivedData(dataIdentifier, value)
        self.hasData = True

    def handleUpdateReceivedData(self, dataIdentifier, value):
        """!
        Update received data.

        @param dataIdentifier Data identification.
        @param value Data content.
        """
        raise NotImplementedError("Override this mehod in sub-class")

    def isComplete(self):
        return not any(x is None for x in self.dataMapping.values())

    def getMeasurement(self):
        return Measurement.currentMeasurement(self.getData())

    def getMissingDataIdentifiers(self):
        for dataIdentifier, value in self.dataMapping.items():
            if value is None:
                yield dataIdentifier

    def hasAnyData(self):
        return self.hasData

    def reset(self):
        for dataIdentifier in self.dataMapping:
            self.dataMapping[dataIdentifier] = None
        self.hasData = False

class LastValueUpdateBuffer(SingleValueUpdateBuffer):
    """!
    Keeps only last value. When some value is updated, the preveous value is lost.

    Updater can hold any kind of data.
    """

    def handleUpdateReceivedData(self, dataIdentifier, value):
        self.dataMapping[dataIdentifier] = value

    def getData(self):
        return copy.deepcopy(self.dataMapping)

class AverageUpdateBuffer(SingleValueUpdateBuffer):
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
            raise ValueError("Can't convert data to number: {}".format(value))

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

    def __init__(self, dataIdentifiers):
        BaseUpdateBuffer.__init__(self, dataIdentifiers)
        self.lastValueMapping = {}
        for dataIdentifier in dataIdentifiers:
            self.lastValueMapping[dataIdentifier] = None
        self.measurementBuffer = collections.deque()

    def updateReceivedData(self, dataIdentifier, value):
        if self.lastValueMapping[dataIdentifier] is None or self.lastValueMapping[dataIdentifier] != value:
            self.lastValueMapping[dataIdentifier] = value
            measurement = Measurement.currentMeasurement({dataIdentifier: value})
            self.measurementBuffer.append(measurement)
        else:
            logging.getLogger().error(
                "New data are equals to previous one ({}: {}). Skipping...".format(dataIdentifier, repr(value)))

    def reset(self):
        self.measurementBuffer.popleft()

    def getMeasurement(self):
        return self.measurementBuffer[0]

    def hasAnyData(self):
        return len(self.measurementBuffer) > 0

    def isComplete(self):
        return self.hasAnyData()

class TopicException(Exception):
    """!
    Update buffer related errors.
    """
