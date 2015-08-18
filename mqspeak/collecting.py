class DataCollector:
    """
    Object for collecting received data from MQTT brokers. This object is also resposible
    to provide received data to each update buffer. If some of update buffers becomes full,
    its content is given to ChannelUpdateSupervisor object.
    """

    def __init__(self, updateBuffers, channelUpdateSupervisor):
        """
        updateBuffers: list of UpdateBuffer objects
        channelUpdateSupervisor: update supervisor
        """
        self.updateBuffers = updateBuffers
        self.channelUpdateSupervisor = channelUpdateSupervisor

    def onNewData(self, dataIdentifier, data):
        for updateBuffer in self.updateBuffers:
            updateBuffer.updateReceivedData(dataIdentifier, data)
            if updateBuffer.isComplete():
                data = updateBuffer.getData()
                updateBuffer.reset()
                self.channelUpdateSupervisor.dataAvailable(updateBuffer.channel, data)

class UpdateBuffer:
    """
    Object for buffering reqired data set before delivering them to ThingSpeak.
    """

    def __init__(self, channel, dataIdentifiers):
        """
        channel: channel identification object
        dataIdentifiers: iterable of DataIdentifier objects
        """
        self.channel = channel
        self.dataIdentifiers = dataIdentifiers
        self.reset()

    def isComplete(self):
        return not any(x is None for x in self.dataDict.values())

    def updateReceivedData(self, dataIdentifier, value):
        """
        throws TopicException: if unnessesary topic is updated
        """
        if dataIdentifier not in self.dataDict:
            raise TopicException("Illegal topic update: {0}".format(dataIdentifier))
        else:
            self.dataDict[dataIdentifier] = value

    def getData(self):
        if not self.isComplete():
            raise TopicException("Some topic data is missing")
        else:
            return self.dataDict

    def reset(self):
        self.dataDict = dict()
        for dataIdentifier in self.dataIdentifiers:
            self.dataDict[dataIdentifier] = None


class TopicException(Exception):
    pass
