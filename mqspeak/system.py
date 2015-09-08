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

    @classmethod
    def initialize(cls):
        """
        Initiate system configuration.
        """
        cls.cliArgs = args.parse_args()
        cls.config = ProgramConfig(cls.cliArgs.config)
        cls.config.parse()

        cls.verbose = cls.cliArgs.verbose

    @classmethod
    def getChannelConvertMapping(cls):
        """
        Get mapping for converting measurements for each channel

        {channel: channelParamConverter}
        """
        channelConvertMapping = {}
        for channel in cls.config.channels:
            channelConvertMapping[channel] = MeasurementParamConverter(cls.config.getDataFieldMapping(channel))
        return channelConvertMapping

    @classmethod
    def getBrokerListenDescriptors(cls):
        """
        Get list of tuples (broker, ["subscribeTopic"])
        """
        listenDescriptors = []
        for broker in cls.config.brokers:
            subscribeTopic = cls.config.getBrokerSubscribtions(broker)
            listenDescriptor = (broker, subscribeTopic)
            listenDescriptors.append(listenDescriptor)
        return listenDescriptors

    @classmethod
    def getUpdateBuffers(cls):
        """
        Get list of UpdateBuffer instances.
        """
        updateBuffers = []
        for channel in cls.config.channels:
            updateBuffers.append(cls.getUpdateBuffer(channel))
        return updateBuffers

    @classmethod
    def getUpdateBuffer(cls, channel):
        """
        Get list of UpdateBuffer for particular channel
        """
        dataIdentifiers = list(cls.config.getDataFieldMapping(channel).keys())
        return UpdateBuffer(channel, dataIdentifiers)

    @classmethod
    def getChannelUpdateMapping(cls):
        """
        Get mapping {channel: updater}
        """
        channelUpdateMapping = {}
        for channel in cls.config.channels:
            channelUpdateMapping[channel] = cls.config.getChannelUpdater(channel)
        return channelUpdateMapping
