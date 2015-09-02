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
    """
    Measured data mapping in DataIdentifier: value format with corresponding timestamp
    """

    def __init__(self, fields, time):
        """
        throws AttributeError: if length of fields is greater than 8
        """
        if len(fields) > 8:
            raise AttributeError("Fields must be up to length 8, {0} given".format(len(fields)))
        self.fields = fields
        self.time = time

    @classmethod
    def currentMeasurement(cls, fields):
        """
        Build measurement object with current time.
        """
        return cls(fields, datetime.datetime.now())

    def __len__(self):
        return len(self.fields)

class MeasurementParamConverter:
    """
    Convert data measurement into ThingSpeak fields for single channel.
    """

    def __init__(self, dataFieldsMapping):
        """
        dataFieldsMapping: object for mapping DataIdentifier object to ThingSpeak channel field.
            {DataIdentifier: "field"}
        """
        self.dataFieldsMapping = dataFieldsMapping

    def convert(self, measurement):
        """
        throws ConvertException: if reguired measurement item is missing
        """
        params = dict()
        for topicName in measurement.fields:
            params[self.dataFieldsMapping[topicName]] = measurement.fields[topicName]
        return params

    def __str__(self):
        return "<Param Converter: {0}>".format(str(self.dataFieldsMapping))

    def __repr__(self):
        return self.__str__()

class DataIdentifier:
    """
    Wrapper object to convert broker and topic into uniquie identification key
    """

    def __init__(self, broker, topic):
        self.broker = broker
        self.topic = topic

    def __hash__(self):
        return hash((self.broker, self.topic))

    def __str__(self):
        return "<{0}: {1}>".format(self.broker, self.topic)

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        if not isinstance(other, DataIdentifier):
            return False
        return self.broker == other.broker and self.topic == other.topic

class ConvertException(Exception):
    """
    Conversion error
    """
