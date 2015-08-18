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

class ConvertException(Exception):
    """
    Conversion error
    """
