import configparser
from mqspeak.broker import Broker

class ProgramConfig:

    def __init__(self, configFile):
        self.configFile = configFile
        self.parser = configparser.ConfigParser()
    
    def parse(self):
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
            pass
    
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
        subscriptions = []
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
