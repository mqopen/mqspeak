from mqspeak import args
from mqspeak.config import ProgramConfig

class System:
    """
    System initialization object
    """
    
    def __init__(self):
        self.cliArgs = args.parse_args()
        config = ProgramConfig(self.cliArgs.config)
        config.parse()
