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

from mqspeak.collecting import UpdateBuffer
from mqspeak.config import ProgramConfig
from mqspeak.data import MeasurementParamConverter
from mqspeak import args

class System:
    """
    System initialization object. This object encapsulates program configuration state
    defined by command line arguments and parsed configuration file.
    """

    def __init__(self):
        """
        Initiate system configuration.
        """
        self.cliArgs = args.parse_args()
        self.config = ProgramConfig(self.cliArgs.config)
        self.config.parse()

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

    def getUpdateBuffers(self):
        """
        Get list of UpdateBuffer instances.
        """
        updateBuffers = []
        for channel in self.config.channels:
            updateBuffers.append(self.getUpdateBuffer(channel))
        return updateBuffers

    def getUpdateBuffer(self, channel):
        """
        Get list of UpdateBuffer for particular channel
        """
        dataIdentifiers = self.config.getDataFieldMapping(channel).keys()
        return UpdateBuffer(channel, dataIdentifiers)

    def getChannelUpdateMapping(self):
        """
        Get mapping {channel: updater}
        """
        channelUpdateMapping = {}
        for channel in self.config.channels:
            channelUpdateMapping[channel] = self.config.getChannelUpdater(channel)
        return channelUpdateMapping
