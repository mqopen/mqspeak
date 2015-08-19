#!/usr/bin/env python3
from mqspeak.system import System
from mqspeak.receiving import BrokerThreadManager
from mqspeak.sending import ChannelUpdateDispatcher
from mqspeak.collecting import DataCollector
from mqspeak.updating import ChannnelUpdateSupervisor

def main():
    system = System()

    # Channel update dispatcher object
    channelConvertMapping = system.getChannelConvertMapping()
    updateDispatcher = ChannelUpdateDispatcher.createThingSpeakUpdateDispatcher(channelConvertMapping)

    channelUpdateSupervisor = ChannnelUpdateSupervisor(system.getChannelUpdateMapping())
    channelUpdateSupervisor.setDispatcher(updateDispatcher)
    dataCollector = DataCollector(system.getUpdateBuffers(), channelUpdateSupervisor)

    # MQTT cliens
    brokerManager = BrokerThreadManager(system.getBrokerListenDescriptors(), dataCollector)

    # run all MQTT client threads
    brokerManager.start()

    # run main thread
    try:
        updateDispatcher.run()
    except KeyboardInterrupt as ex:

        # program exit
        brokerManager.stop()
        updateDispatcher.stop()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt as ex:
        pass
