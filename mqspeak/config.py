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
        for channel, updaterFactory, updateMappingFactory in self.getChannels():
            updater = updaterFactory.build(channel)
            updateMapping = updateMappingFactory.build(configCache)
            configCache.addChannel(channel, updater, updateMapping)
        return configCache

    def checkForMandatorySections(self):
        self.checkForSectionList(["Brokers", "Channels"])

    def getBrokers(self):
        """
        Get list of enabled brokers.
        """
        brokerSections = self.parser.get("Brokers", "Enabled").split()
        self.checkForSectionList(brokerSections)
        for brokerSection in brokerSections:
            broker = self.createBroker(brokerSection)
            subscribtions = self.getBrokerSubscribtions(brokerSection)
            yield broker, subscribtions

    def createBroker(self, brokerSection):
        try:
            self.checkForOptionList(brokerSection, ["Topic"])
            options = self.parser.options(brokerSection)
            host = self.parser.get(brokerSection, "Host", fallback = "127.0.0.1")
            port = self.parser.getint(brokerSection, "Port", fallback = 1883)
            broker = Broker(brokerSection, host, port)
            if "user" in options or "password" in options:
                (user, password) = self.getBrokerCredentials(brokerSection)
                broker.setCredentials(user, password)
            return broker
        except ValueError as ex:
            raise ConfigException("Invalid broker port number: {}".format(self.parser.get(brokerSection, "Port")))

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
        self.checkForSectionList(channelSections)
        for channelSection in channelSections:
            channel = self.createChannel(channelSection)
            updaterFactory = self.getChannelUpdater(channelSection)
            updateMappingFactory = self.getDataFieldMapping(channelSection)
            yield channel, updaterFactory, updateMappingFactory

    def createChannel(self, channelSection):
        writeKey = self.parser.get(channelSection, "Key")
        return Channel(channelSection, writeKey)

    def getChannelUpdater(self, channelSection):
        try:
            updateRate = datetime.timedelta(seconds = self.parser.getint(channelSection, "UpdateRate"))
            updaterName = self.parser.get(channelSection, "UpdateType")
            updaterCls, updaterArgs = self.createUpdaterFactory(updaterName, updateRate)
            return ChannelUpdaterFactory(updaterCls, updaterArgs)
        except ValueError as ex:
            raise ConfigException("Invalid update rate interval: {}".format(self.parser.get(channelSection, "UpdateRate")))

    def createUpdaterFactory(self, updaterName, updateRate):
        updaterCls = None
        if updaterName == "blackout":
            updaterCls = BlackoutUpdater
        elif updaterName == "buffered":
            updaterCls = BufferedUpdater
        elif updaterName == "average":
            updaterCls = AverageUpdater
        elif updaterName == "onchange":
            updaterCls = OnChangeUpdater
        else:
            raise ConfigException("Unknown UpdateType: {}".format(updaterName))
        updaterArgs = (updateRate,)
        return updaterCls, updaterArgs

    def getDataFieldMapping(self, channelSection):
        # TODO: check for section
        updaterSection = self.parser.get(channelSection, "UpdateFields")
        return self.createDataFieldMapping(updaterSection)

    def createDataFieldMapping(self, updateSection):
        updateMappingFactory = UpdateMappingFactory()
        for mappingOption in self.parser.options(updateSection):
            optionValue = self.parser.get(updateSection, mappingOption).split()
            if len(optionValue) < 2:
                    raise ConfigException("{}: {} - option must contain two space separated values".format(updateSection, mappingOption))
            brokerName, topic = optionValue
            updateMappingFactory.addMapping(brokerName, topic, mappingOption)
        return updateMappingFactory

    def checkForSectionList(self, sectionList):
        for section in sectionList:
            self.checkForSection(section)

    def checkForSection(self, section):
        if not self.parser.has_section(section):
            raise ConfigException("{} section is missing".format(section))

    def checkForOptionList(self, section, optionList):
        for option in optionList:
            self.checkForOption(section, option)

    def checkForOption(self, section, option):
        if not self.parser.has_option(section, option):
            raise ConfigException("Section {}: {} option is missing".format(section, option))

class ConfigCache:
    """
    Cache object for storing app configuration.
    """

    def __init__(self):
        self.listenDescriptors = []
        self.channelUpdateDescribtors = []

    def addBroker(self, broker, subscribtions):
        """
        """
        listenDescriptor = (broker, subscribtions)
        self.listenDescriptors.append(listenDescriptor)

    def addChannel(self, channel, updater, updateMapping):
        """
        raises: ConfigException when update mapping contains unknown broker
        """
        channelUpdateDescribtor = (channel, updater, updateMapping)
        self.channelUpdateDescribtors.append(channelUpdateDescribtor)

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
        for broker, subscribtions in self.listenDescriptors:
            if brokerName == broker.name:
                return broker
        raise ConfigException("Unknown broker name: {}".format(brokerName))

class ChannelUpdaterFactory:
    def __init__(self, updaterCls, updaterArgs):
        self.updaterCls = updaterCls
        self.updaterArgs = updaterArgs

    def build(self, channel):
        return self.updaterCls(channel, *self.updaterArgs)

class UpdateMappingFactory:
    def __init__(self):
        self.mapping = {}

    def addMapping(self, brokerName, topic, field):
        self.checkNewBrokerName(brokerName)
        self.mapping[brokerName].append((topic, field))

    def checkNewBrokerName(self, brokerName):
        if brokerName not in self.mapping:
            self.mapping[brokerName] = []

    def getNeededBrokers(self):
        return list(self.mapping.keys())

    def build(self, brokerNameResolver):
        mapping = {}
        for brokerName in self.mapping.keys():
            broker = brokerNameResolver.getBrokerByName(brokerName)
            for topic, field in self.mapping[brokerName]:
                dataIdentifier = DataIdentifier(broker, topic)
                mapping[dataIdentifier] = field
        return mapping

class ConfigException(Exception):
    """
    Exception raised during parsing configuration file
    """
