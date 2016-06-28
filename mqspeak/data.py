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
        """
        self.fields = fields
        self.time = time

    @classmethod
    def currentMeasurement(cls, fields):
        """!
        Build measurement object with current time.

        @param fields Maping {dataIdentifier: vaue}.
        """
        return cls(fields, datetime.datetime.utcnow())

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
            if measurement.fields[topicName] is not None:
                fieldName = self.dataFieldsMapping[topicName]
                params[fieldName] = measurement.fields[topicName]
        return params

    def __str__(self):
        """!
        Convert object to string.

        @return String.
        """
        return "Param Converter: {}".format(str(self.dataFieldsMapping))

    def __repr__(self):
        """!
        Convert object to representation string.

        @return representation string.
        """
        return "<{}>".format(self.__str__())

class ConvertException(Exception):
    """!
    Conversion error.
    """
