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

import sys
import logging
import logging.handlers
from mqspeak.config import ProgramConfig, ConfigException
from mqspeak.data import MeasurementParamConverter
from mqspeak import args

class System:
    """!
    System initialization object. This object encapsulates program configuration state
    defined by command line arguments and parsed configuration file.
    """

    @classmethod
    def initialize(cls):
        """!
        Initiate system configuration.
        """

        l = logging.getLogger()
        l.setLevel(logging.INFO)
        h = logging.handlers.SysLogHandler(address='/dev/log')

        cls.cliArgs = args.parse_args()

        # Logging destination.
        if cls.cliArgs.log_stdout:
            h = logging.StreamHandler(stream = sys.stdout)

        # Verbose.
        if cls.cliArgs.verbose:
            h.setLevel(logging.INFO)
        else:
            h.setLevel(logging.ERROR)
        l.addHandler(h)

        config = ProgramConfig(cls.cliArgs.config)
        # TODO: handle config exceptions
        try:
            cls.configCache = config.parse()
        except ConfigException as ex:
            logging.getLogger().error("Configuration error: {}".format(ex))
            exit(1)

    @classmethod
    def getChannelConvertMapping(cls):
        """!
        Get mapping for converting measurements for each channel.

        @return {channel: channelParamConverter}
        """
        channelConvertMapping = {}
        for channel, _, updateMapping in cls.configCache.channelUpdateDescribtors:
            channelConvertMapping[channel] = MeasurementParamConverter(updateMapping)
        return channelConvertMapping

    @classmethod
    def getBrokerListenDescriptors(cls):
        """!
        Get list of tuples (broker, ["subscribeTopic"]).

        @return (broker, ["subscribeTopic"])
        """
        return cls.configCache.listenDescriptors

    @classmethod
    def getUpdateBuffers(cls):
        """!
        Get list of UpdateBuffer instances.

        @return
        """
        updateBuffers = []
        for channel, _, updateMapping in cls.configCache.channelUpdateDescribtors:
            dataIdentifiers = list(updateMapping.keys())
            updateBuffer = UpdateBuffer(channel, dataIdentifiers)
            updateBuffers.append(updateBuffer)
        return updateBuffers

    @classmethod
    def getChannelUpdateMapping(cls):
        """!
        Get mapping {channel: updater}.

        @return {channel: updater}
        """
        channelUpdateMapping = {}
        for channel, updater, _ in cls.configCache.channelUpdateDescribtors:
            channelUpdateMapping[channel] = updater
        return channelUpdateMapping
