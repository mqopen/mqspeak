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

import datetime

class Measurement:
    """!
    Measured data mapping in DataIdentifier: value format with corresponding timestamp.
    """

    ## @var fields
    # Measurement fields.

    ## @var time
    # Measurement timestamp.

    def __init__(self, fields, time):
        """!
        Initiate measurement object.

        @param fields Maping {dataIdentifier: vaue}.
        @param time  Measurement timestamp.
        @throws AttributeError If length of fields is greater than 8.
        """
        if len(fields) > 8:
            raise AttributeError("Fields must be up to length 8, {} given".format(len(fields)))
        self.fields = fields
        self.time = time

    @classmethod
    def currentMeasurement(cls, fields):
        """!
        Build measurement object with current time.

        @param cls
        @param fields Maping {dataIdentifier: vaue}.
        """
        return cls(fields, datetime.datetime.now())

    def __str__(self):
        """!
        Convert object to string.

        @return String.
        """
        return "[{}] {}".format(self.time, self.fields)

    def __repr__(self):
        """!
        Convert object to representation string.

        @return representation string.
        """
        return "<{}>".format(self.__str__())

    def __len__(self):
        """!
        Get number of measurement fields.

        @return Number of fields.
        """
        return len(self.fields)

class MeasurementParamConverter:
    """!
    Convert data measurement into ThingSpeak fields for single channel.
    """

    ## @var dataFieldsMapping
    # Mapping of data fields.

    def __init__(self, dataFieldsMapping):
        """!
        Initiate MeasurementParamConverter object.

        @param dataFieldsMapping Object for mapping DataIdentifier object to
            ThingSpeak channel field {DataIdentifier: "field"}.
        """
        self.dataFieldsMapping = dataFieldsMapping

    def convert(self, measurement):
        """!
        Convert measurement.

        @param measurement Measurement object.
        @throws ConvertException If reguired measurement item is missing.
        """
        params = dict()
        for topicName in measurement.fields:
            fieldName = self.dataFieldsMapping[topicName]
            params[fieldName] = measurement.fields[topicName]
        return params

    def __str__(self):
        """!
        Convert object to string.

        @return String.
        """
        return "<Param Converter: {}>".format(str(self.dataFieldsMapping))

    def __repr__(self):
        """!
        Convert object to representation string.

        @return representation string.
        """
        return self.__str__()

class DataIdentifier:
    """!
    Wrapper object to convert broker and topic into uniquie identification key
    """

    ## @var broker
    # Broker object.

    ## @var topic
    # Topic object.

    def __init__(self, broker, topic):
        """!
        Initiate DataIdentifier object.

        @param broker Broker object.
        @param topic Topic object.
        """
        self.broker = broker
        self.topic = topic

    def __hash__(self):
        """!
        Calculate hash of DataIdentifier object.

        @return Hash.
        """
        return hash((self.broker, self.topic))

    def __str__(self):
        """!
        Convert object to string.

        @return String.
        """
        return "<{}: {}>".format(self.broker, self.topic)

    def __repr__(self):
        """!
        Convert object to representation string.

        @return representation string.
        """
        return self.__str__()

    def __eq__(self, other):
        """!
        Check if DataIdentifier object is equal to another.

        @param other Other object.
        @return True if other object is instance of DataIdentifier and contains same values, False otherwise.
        """
        if not isinstance(other, DataIdentifier):
            return False
        return self.broker == other.broker and self.topic == other.topic

class ConvertException(Exception):
    """!
    Conversion error.
    """
