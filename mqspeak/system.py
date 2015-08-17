from mqspeak import args
from mqspeak.config import ProgramConfig
from mqspeak.channel import Channel

class System:
    """
    System initialization object
    """

    def __init__(self):
        self.cliArgs = args.parse_args()
        self.config = ProgramConfig(self.cliArgs.config)
        self.config.parse()

    def getChannelConvertMapping(self):
        return {}
