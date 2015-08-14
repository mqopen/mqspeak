import datetime

class Measurement:

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
    Convert data measurement into ThingSpeak fields
    """
    
    def __init__(self, mapping):
        """
        mapping: object for mapping DataIdentifier object to ThingSpeak channel field.
        """
        self.mapping = mapping
    
    def convert(self, measurement):
        """
        throws ConvertException: if reguired measurement item is missing
        """
        params = dict()
        for topicName in measurement.fields:
            params[self.mapping[topicName]] = measurement.fields[topicName]
        return params

class DataIdentifier:
    """
    Wrapper object to convert broker and topic into uniquie identification key 
    """
    
    def __init__(self, broker, topic):
        self.broker = broker
        self.topic = topic
    
    def __hash__(self):
        return hash((self.broker, self.topic))

class ConvertException(Exception):
    """
    Conversion error
    """
