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
        self._checkForMandatorySections()
        self.listenDescriptors = self.getListenDescriptors()
        self.channelUpdateDescriptors = self.getChannelUpdateDescriptors()

    def getListenDescriptors(self):
        """
        Create list of listen descriptor objects - (broker, topicIterable)
        """
        brokerSections = self.parser.get("Brokers", "Enabled").split()
        self._checkForSectionList(brokerSections)
        listenDescriptors = []
        for brokerSection in brokerSections:
            broker = self._createBroker(brokerSection)
            subscriptions = self._getBrokerSubscribtions(brokerSection)
            listenDescriptors.append((broker, subscriptions))
        return listenDescriptors

    def getChannelUpdateDescriptors(self):
        """
        Create list of channel update descriptor objects
        """
        channelSections = self.parser.get("Channels", "Enabled").split()
        self._checkForSectionList(channelSections)
        for channelSection in channelSections:
            self._createChannel(channelSection)
            self._createChannelMapping(channelSection)

    def _createChannel(self, channelSection):
        writeKey = self.parser.get(channelSection, "Key")
        return Channel(channelSection, writeKey)

    def _createChannelMapping(self, channelSection):
        """
        Returns {DataIdentifier: "field"} mapping
        """
        channelMapping = {}
        for mappingOption in ["Field1", "Field2", "Field3", "Field4", "Field5", "Field6", "Field7", "Field8"]:
            if self.parser.has_option(channelSection, mappingOption):
                optionValue = self.parser.get(channelSection, mappingOption).split()
                if len(optionValue) < 2:
                    raise ConfigException("{0}: {1} - option must contain two space separated values".format(channelSection, mappingOption))
                (brokerName, topic) = optionValue
                broker = self._getBrokerByName(brokerName)
                if broker is None:
                    raise ConfigException("Broker section {0} is not defined or enabled".format(brokerName))
                channelMapping[DataIdentifier(broker, topic)] = mappingOption.lower()
        return channelMapping

    def _createUpdaters(self, channelSection):
        updateRate = datetime.timedelta(seconds = self.parser.getint(channelSection, "UpdateRate"))
        updaterName = self.parser.get(channelSection, "UpdateType")
        if updaterName == "blackout":
            return BlackoutUpdater(updateRate)
        elif updaterName == "buffered":
            return BufferedUpdater(updateRate)
        elif updaterName == "average":
            return AverageUpdater(updateRate)
        elif updaterName == "onchange":
            return OnChangeUpdater()
        else:
            raise ConfigException("Unknown UpdateType: {0}".format(updaterName))

    def _getBrokerByName(self, brokerName):
        for broker, subscriptions in self.listenDescriptors:
            if brokerName == broker.name:
                return broker
        return None

    def _createBroker(self, brokerSection):
        self._checkForOptionList(brokerSection, ["Topic"])
        options = self.parser.options(brokerSection)
        broker = Broker(brokerSection,
                        self.parser.get(brokerSection, "Host", fallback = "127.0.0.1"),
                        self.parser.getint(brokerSection, "Port", fallback = 1883))
        if "user" in options or "password" in options:
            (user, password) = self._getBrokerCredentials(brokerSection)
            broker.setCredentials(user, password)
        return broker

    def _getBrokerCredentials(self, brokerSection):
        user = None
        password = None
        try:
            user = self.parser.get(brokerSection, "User")
        except configparser.NoOptionError as ex:
            raise ConfigException("Section {0}: User option is missing")
        try:
            password = self.parser.get(brokerSection, "Password")
        except configparser.NoOptionError as ex:
            raise ConfigException("Section {0}: Password option is missing")
        return (user, password)

    def _getBrokerSubscribtions(self, brokerSection):
        subscriptions = self.parser.get(brokerSection, "Topic").split()
        if len(subscriptions) == 0:
            raise ConfigException("At least one topic subscribe has to be defined")
        return subscriptions

    def _checkForMandatorySections(self):
        self._checkForSectionList(["Brokers", "Channels"])

    def _checkForSectionList(self, sectionList):
        for section in sectionList:
            self._checkForSection(section)

    def _checkForSection(self, section):
        if not self.parser.has_section(section):
            raise ConfigException("{0} section is missing".format(section))

    def _checkForOptionList(self, section, optionList):
        for option in optionList:
            self._checkForOption(section, option)

    def _checkForOption(self, section, option):
        if not self.parser.has_option(section, option):
            raise ConfigException("Section {0}: {1} option is missing".format(section, option))

class ConfigException(Exception):
    """
    Exception raised during parsing configuration file
    """
