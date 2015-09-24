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

import configparser
import datetime
from mqspeak.broker import Broker
from mqspeak.channel import Channel
from mqspeak.data import DataIdentifier
from mqspeak.updating import BlackoutUpdater, BufferedUpdater, AverageUpdater, OnChangeUpdater

class ProgramConfig:
    """
    Program configuration parser.
    """

    def __init__(self, configFile):
        """
        configFile: path to configuration file
        """
        self.configFile = configFile
        self.parser = configparser.ConfigParser()

    def parse(self):
        """
        Parse config file.
        """
        self.parser.read(self.configFile)
        self.checkForMandatorySections()
        configCache = ConfigCache()
        for broker, subscribtions in self.getBrokers():
            configCache.addBroker(broker, subscribtions)
        for channel, updater, updateMapping in self.getChannels():
            configCache.addChannel(channel, updater, updateMapping)

    def checkForMandatorySections(self):
        self._checkForSectionList(["Brokers", "Channels"])

    def getBrokers(self):
        """
        Get list of enabled brokers.
        """
        brokerSections = self.parser.get("Brokers", "Enabled").split()
        self._checkForSectionList(brokerSections)
        for brokerSection in brokerSections:
            broker = self.createBroker(brokerSection)
            subscribtions = self.getBrokerSubscribtions(brokerSection)
            yield broker, subscribtions

    def createBroker(self, brokerSection):
        self._checkForOptionList(brokerSection, ["Topic"])
        options = self.parser.options(brokerSection)
        broker = Broker(brokerSection,
                        self.parser.get(brokerSection, "Host", fallback = "127.0.0.1"),
                        self.parser.getint(brokerSection, "Port", fallback = 1883))
        if "user" in options or "password" in options:
            (user, password) = self.getBrokerCredentials(brokerSection)
            broker.setCredentials(user, password)
        return broker

    def getBrokerCredentials(self, brokerSection):
        user = None
        password = None
        try:
            user = self.parser.get(brokerSection, "User")
        except configparser.NoOptionError as ex:
            raise ConfigException("Section {}: User option is missing".format(brokerSection))
        try:
            password = self.parser.get(brokerSection, "Password")
        except configparser.NoOptionError as ex:
            raise ConfigException("Section {}: Password option is missing".format(brokerSection))
        return user, password

    def getBrokerSubscribtions(self, brokerSection):
        subscriptions = self.parser.get(brokerSection, "Topic").split()
        if len(subscriptions) == 0:
            raise ConfigException("At least one topic subscribe has to be defined")
        return subscriptions

    def getChannels(self):
        """
        Create list of enable channels.
        """
        channelSections = self.parser.get("Channels", "Enabled").split()
        self._checkForSectionList(channelSections)
        for channelSection in channelSections:
            channel = self.createChannel(channelSection)
            updaterFactory = self.getChannelUpdater(channelSection)
            updateMappingFactory = self.getDataFieldMapping(channelSection)
            yield channel, updaterFactory, updateMappingFactory

    def createChannel(self, channelSection):
        writeKey = self.parser.get(channelSection, "Key")
        return Channel(channelSection, writeKey)

    def getChannelUpdater(self, channelSection):
        updateRate = datetime.timedelta(seconds = self.parser.getint(channelSection, "UpdateRate"))
        updaterName = self.parser.get(channelSection, "UpdateType")
        updaterCls = None
        updaterArgs = None
        if updaterName == "blackout":
            updaterCls = BlackoutUpdater
            updaterArgs = updateRate
        elif updaterName == "buffered":
            updaterCls = BufferedUpdater
            updaterArgs = updateRate
        elif updaterName == "average":
            updaterCls = AverageUpdater
            updaterArgs = updateRate
        elif updaterName == "onchange":
            updaterCls = OnChangeUpdater
            updaterArgs = updateRate
        else:
            raise ConfigException("Unknown UpdateType: {}".format(updaterName))
        return ChannelUpdaterFactory(updaterCls, updaterArgs)

    def getDataFieldMapping(self, channelSection):
        updateMappingFactory = UpdateMappingFactory(channelSection)
        for mappingOption in ["Field1", "Field2", "Field3", "Field4", "Field5", "Field6", "Field7", "Field8"]:
            if self.parser.has_option(channelSection, mappingOption):
                optionValue = self.parser.get(channelSection, mappingOption).split()
                if len(optionValue) < 2:
                    raise ConfigException("{0}: {1} - option must contain two space separated values".format(channelSection, mappingOption))
                brokerName, topic = optionValue
                updateMappingFactory.addMapping(brokerName, topic, mappingOption.lower())
        return updateMappingFactory

    def _checkForSectionList(self, sectionList):
        for section in sectionList:
            self._checkForSection(section)

    def _checkForSection(self, section):
        if not self.parser.has_section(section):
            raise ConfigException("{} section is missing".format(section))

    def _checkForOptionList(self, section, optionList):
        for option in optionList:
            self._checkForOption(section, option)

    def _checkForOption(self, section, option):
        if not self.parser.has_option(section, option):
            raise ConfigException("Section {}: {} option is missing".format(section, option))

class ConfigCache:
    """
    Cache object for storing app configuration.
    """

    def addBroker(self, broker, subscribtions):
        """
        """

    def addChannel(self, channel, updater, updateMapping):
        """
        raises: ConfigException when update mapping contains unknown broker
        """
        print("{} : {} : {}".format(channel, updater, updateMapping))

    def check(self):
        """
        1. warning for unused brokers
        2. warning for not feasible topics in udate mappings.
        """

    def getBrokerByName(self, brokerName):
        """
        Get broker object identified by its't name.

        raises KeyError if the name don't match to any stored broker object.
        """
        for broker in self.brokers:
            if brokerName == broker.name:
                return broker
        raise KeyError("Unknown broker name: {}".format(brokerName))

class ChannelUpdaterFactory:
    def __init__(self, updaterCls, updaterArgs):
        self.updaterCls = updaterCls
        self.updaterArgs = updaterArgs

    def build(self, channel):
        return self.updaterCls(channel, *self.updaterArgs)

class UpdateMappingFactory:
    def __init__(self, channelName):
        self.channelName = channelName
        self.mapping = {}

    def addMapping(self, brokerName, topic, field):
        self.mapping[(brokerName, topic)] = field

    def build(self, broker):
        pass

class ConfigException(Exception):
    """
    Exception raised during parsing configuration file
    """
