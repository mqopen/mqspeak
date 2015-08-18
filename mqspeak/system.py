from mqspeak import args
from mqspeak.config import ProgramConfig
from mqspeak.channel import Channel
from mqspeak.updating import ChannnelUpdateSupervisor
from mqspeak.data import MeasurementParamConverter
from mqspeak.collecting import UpdateBuffer

class System:
    """
    System initialization object
    """

    def __init__(self):
        self.cliArgs = args.parse_args()
        self.config = ProgramConfig(self.cliArgs.config)
        self.config.parse()

    # TO DELETE
    def _getUpdateChannels(self):
        """
        Get list of update channels.
        """
        return self.config.channels

    # TO DELETE
    def _getChannelParamConverter(self, channel):
        """
        Get mapping object describing data conversion for particular channel

        {dataIdentification: "field"}
        """

    def getChannelConvertMapping(self):
        """
        Get mapping for converting measurements for each channel

        {channel: channelParamConverter}
        """
        channelConvertMapping = {}
        for channel in self.config.channels:
            channelConvertMapping[channel] = MeasurementParamConverter(self.config.getDataFieldMapping(channel))
        return channelConvertMapping

    def getBrokerListenDescriptors(self):
        """
        Get list of tuples (broker, ["subscribeTopic"])
        """
        listenDescriptors = []
        for broker in self.config.brokers:
            subscribeTopic = self.config.getBrokerSubscribtions(broker)
            listenDescriptor = (broker, subscribeTopic)
            listenDescriptors.append(listenDescriptor)
        return listenDescriptors

    def getChannelUpdateSupervisor(self):
        for channel in self.config.channels:
            pass

    def getUpdateBuffers(self):
        updateBuffers = []
        for channel in self.config.channels:
            updateBuffers.append(self.getUpdateBuffer)
        return updateBuffers

    def getUpdateBuffer(self, channel):
        """
        Get list of UpdateBuffer for particular channel
        """
        dataIdentifiers = self.config.getDataFieldMapping(channel).keys()
        return UpdateBuffer(channel, dataIdentifiers)
