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
from mqreceive.broker import Broker
from mqspeak.channel import ThingSpeakChannel, PhantChannel
from mqreceive.data import DataIdentifier
from mqspeak.updating import BlackoutUpdater, BufferedUpdater, AverageUpdater, OnChangeUpdater

class ProgramConfig:
    """!
    Program configuration parser.
    """

    ## @var configFile
    # Configuration file name.

    ## @var parser
    # Parser object.

    def __init__(self, configFile):
        """!
        Initiate program configuration object.

        @param configFile Path to configuration file.
        """
        self.configFile = configFile
        self.parser = configparser.ConfigParser()

    def parse(self):
        """!
        Parse config file.

        @return Configuration object.
        """
        self.parser.read(self.configFile)
        self.checkForMandatorySections()
        configCache = ConfigCache()
        for broker, subscriptions in self.getBrokers():
            configCache.addBroker(broker, subscriptions)
        for channel, updaterFactory, updateMappingFactory in self.getChannels():
            updateMapping = updateMappingFactory.build(configCache)
            updater = updaterFactory.build(channel, updateMapping)
            configCache.addChannel(channel, updater, updateMapping)
        return configCache

    def checkForMandatorySections(self):
        """!
        Check if all necessary sections are mandatory.

        @throws ConfigException if some section is missing.
        """
        self.checkForSectionList(["Brokers", "Channels"])

    def getBrokers(self):
        """!
        Get list of enabled brokers.

        @return Iterable of brokers.
        """
        section = "Brokers"
        self.checkForEnabledOption(section)
        brokerSections = self.parser.get(section, "Enabled").split()
        self.checkForSectionList(brokerSections)
        for brokerSection in brokerSections:
            self.checkForBrokerMandatoryOptions(brokerSection)
            broker = self.createBroker(brokerSection)
            subscriptions = self.getBrokerSubscribtions(brokerSection)
            yield broker, subscriptions

    def checkForBrokerMandatoryOptions(self, brokerSection):
        """!
        Check for mandatory options of broker section.

        @param brokerSection Broker section name.
        @throws ConfigException If some option is missing.
        """
        optionList = ["Topic"]
        self.checkForOptionList(brokerSection, optionList)

    def createBroker(self, brokerSection):
        """!
        Create broker object from broker section.

        @param brokerSection Broker section name.
        @return Broker object
        """
        try:
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
        """!
        Get username and password of broker.

        @param brokerSection Broker section name.
        @return Tuple of (username, password).
        @throws ConfigException If username or password is missing in configuration file.
        """
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
        """!
        Get list of broker subscribe topics.

        @param brokerSection Broker section name.
        @return List of broker subscribe topics.
        @throws ConfigException If zero topics are specified.
        """
        subscriptions = self.parser.get(brokerSection, "Topic").split()
        if len(subscriptions) == 0:
            raise ConfigException("At least one topic subscribe has to be defined")
        return subscriptions

    def getChannels(self):
        """!
        Create list of enable channels.

        @return Iterable of tuples of (channel, updaterFactory, updateMappingFactory).
        @throws ConfigException
        """
        section = "Channels"
        self.checkForEnabledOption(section)
        channelSections = self.parser.get(section, "Enabled").split()
        self.checkForSectionList(channelSections)
        for channelSection in channelSections:
            self.checkForChannelMandatoryOptions(channelSection)
            channel = self.createChannel(channelSection)
            updaterFactory = self.getChannelUpdater(channelSection)
            updateMappingFactory = self.getDataFieldMapping(channelSection)
            yield channel, updaterFactory, updateMappingFactory

    def checkForChannelMandatoryOptions(self, channelSection):
        """!
        Check if channel section has all mandatoty options.

        @param channelSection Channel section name.
        @throws ConfigException If some options are missing.
        """
        optionList = ["Key", "Type", "UpdateRate", "UpdateType", "UpdateFields"]
        self.checkForOptionList(channelSection, optionList)

    def createChannel(self, channelSection):
        """!
        Create channel object.

        @param channelSection Channel section name.
        @return Channel object.
        @throws ConfigException If configuration specifies unknown channel type.
        """
        channelID = self.parser.get(channelSection, "Id", fallback = None)
        writeKey = self.parser.get(channelSection, "Key")
        channelType = self.parser.get(channelSection, "Type")
        waitInterval = None
        try:
            waitInterval = self.parser.getint(channelSection, "WaitInterval", fallback = None)
        except ValueError as ex:
            raise ConfigException("Channel {} - WaitInterval: {}".format(channelSection, self.parser.get(channelSection, "WaitInterval")))
        if waitInterval is not None:
            waitInterval = datetime.timedelta(seconds = waitInterval)

        if channelType == "thingspeak":
            return ThingSpeakChannel(channelSection, channelID, writeKey, waitInterval)
        elif channelType == "phant":
            return PhantChannel(channelSection, channelID, writeKey, waitInterval)
        else:
            raise ConfigException("Unsupported channel type: {}".format(channelType))

    def getChannelUpdater(self, channelSection):
        """!
        Create channel updaterFactory.

        @param channelSection Channel section name.
        @return ChannelUpdaterFactory object for that channel.
        @throws ConfigException If channel specifies invalid update interval.
        """
        try:
            updateRate = datetime.timedelta(seconds = self.parser.getint(channelSection, "UpdateRate"))
            updaterName = self.parser.get(channelSection, "UpdateType")
            updaterCls, updaterArgs = self.createUpdaterFactory(updaterName, updateRate)
            return ChannelUpdaterFactory(updaterCls, updaterArgs)
        except ValueError as ex:
            raise ConfigException("Invalid update rate interval: {}".format(self.parser.get(channelSection, "UpdateRate")))

    def createUpdaterFactory(self, updaterName, updateRate):
        """!
        Create updater factory based on updater name.

        @param updaterName Updater name.
        @param updateRate Update interval.
        @return ChannelUpdaterFactory object.
        @throws ConfigException If unknown updater name is specified in config file.
        """
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
        """!
        Create field mapping for channel.

        @param channelSection Channel section name.
        @return Data field mapping.
        """
        updaterSection = self.parser.get(channelSection, "UpdateFields")
        return self.createDataFieldMapping(updaterSection)

    def createDataFieldMapping(self, updateSection):
        """!
        Create data field mapping from update section.

        @param updateSection Update section name.
        @return Data field mapping.
        """
        updateMappingFactory = UpdateMappingFactory()
        for mappingOption in self.parser.options(updateSection):
            optionValue = self.parser.get(updateSection, mappingOption).split()
            if len(optionValue) < 2:
                    raise ConfigException("{}: {} - option must contain two space separated values".format(updateSection, mappingOption))
            brokerName, topic = optionValue
            updateMappingFactory.addMapping(brokerName, topic, mappingOption)
        return updateMappingFactory

    def checkForEnabledOption(self, section):
        """!
        Check for "Enabled" option in given section.

        @param section Section name.
        @throws ConfigException If "Enabled" option is missing in section.
        """
        self.checkForOption(section, "Enabled")

    def checkForSectionList(self, sectionList):
        """!
        Check for list of sections in configuration file.

        @param sectionList
        @throws ConfigException
        """
        for section in sectionList:
            self.checkForSection(section)

    def checkForSection(self, section):
        """!
        Check for section in configuration file.

        @param section
        @throws ConfigException
        """
        if not self.parser.has_section(section):
            raise ConfigException("{} section is missing".format(section))

    def checkForOptionList(self, section, optionList):
        """!
        Check for list of options in single section.

        @param section
        @param optionList
        @throws ConfigException
        """
        for option in optionList:
            self.checkForOption(section, option)

    def checkForOption(self, section, option):
        """!
        Check for option in configuration file.

        @param section Section name.
        @param option Option name.
        @throws ConfigException If given section doesn!t contain specified option.
        """
        if not self.parser.has_option(section, option):
            raise ConfigException("Section {}: {} option is missing".format(section, option))

class ConfigCache:
    """!
    Cache object for storing app configuration.
    """

    ## @var listenDescriptors
    # Listen descriptors.

    ## @var channelUpdateDescribtors
    # Update descriptors.

    def __init__(self):
        """!
        Initiate configuration cache object.
        """
        self.listenDescriptors = []
        self.channelUpdateDescribtors = []

    def addBroker(self, broker, subscriptions):
        """!
        Add broker to configuration object.

        @param broker
        @param subscriptions
        """
        listenDescriptor = (broker, subscriptions)
        self.listenDescriptors.append(listenDescriptor)

    def addChannel(self, channel, updater, updateMapping):
        """!
        Add channel to configuration object.

        @param channel
        @param updater
        @param updateMapping
        @throws ConfigException When update mapping contains unknown broker.
        """
        channelUpdateDescribtor = (channel, updater, updateMapping)
        self.channelUpdateDescribtors.append(channelUpdateDescribtor)

    def check(self):
        """!
        @todo implement this method

        1. warning for unused brokers
        2. warning for not feasible topics in udate mappings.
        """

    def getBrokerByName(self, brokerName):
        """!
        Get broker object identified by its't name.

        @param @brokerName
        @throws ConfigException If the name don't match to any stored broker object.
        """
        for broker, subscriptions in self.listenDescriptors:
            if brokerName == broker.name:
                return broker
        raise ConfigException("Unknown broker name: {}".format(brokerName))

class ChannelUpdaterFactory:
    """!
    Build channel.
    """

    ## @var updaterCls
    # Updater class.

    ## @var updaterArgs
    # Arguments to call updater class.

    def __init__(self, updaterCls, updaterArgs):
        """!
        Initiate ChannelUpdaterFactory object.

        @param updaterCls
        @param updaterArgs
        """
        self.updaterCls = updaterCls
        self.updaterArgs = updaterArgs

    def build(self, channel, updateMapping):
        """!
        Build ChannelUpdater object.

        @param channel
        @return ChannelUpdater object.
        """
        return self.updaterCls(channel, updateMapping, *self.updaterArgs)

class UpdateMappingFactory:
    """!
    Build UpdateMapping object.
    """

    ## @var mapping
    # Mapping.

    def __init__(self):
        """!
        Initiate UpdateMappingFactory object.
        """
        self.mapping = {}

    def addMapping(self, brokerName, topic, field):
        """!
        Add build mapping.

        @param brokerName
        @param topic
        @param field
        """
        self.checkNewBrokerName(brokerName)
        self.mapping[brokerName].append((topic, field))

    def checkNewBrokerName(self, brokerName):
        """!
        Check if broker name exist in mapping. Create new if not.

        @param brokerName
        """
        if brokerName not in self.mapping:
            self.mapping[brokerName] = []

    def getNeededBrokers(self):
        """
        Get list of needed brokers.

        @return List of broker names.
        """
        return list(self.mapping.keys())

    def build(self, brokerNameResolver):
        """!
        Build UpdateMapping object.

        @param brokerNameResolver Object for resolving broker names into Broker objects.
        @return UpdateMapping object.
        """
        mapping = {}
        for brokerName in self.mapping.keys():
            broker = brokerNameResolver.getBrokerByName(brokerName)
            for topic, field in self.mapping[brokerName]:
                dataIdentifier = DataIdentifier(broker, topic)
                mapping[dataIdentifier] = field
        return mapping

class ConfigException(Exception):
    """!
    Exception raised during parsing configuration file
    """
