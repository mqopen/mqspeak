#!/usr/bin/env python3
from mqspeak.system import System
from mqspeak.receiving import BrokerThreadManager
from mqspeak.sending import ChannelUpdateDispatcher
from mqspeak.collecting import DataCollector, UpdateBuffer
from mqspeak.updating import ChannnelUpdateSupervisor, BlackoutUpdater
from mqspeak.data import MeasurementParamConverter, DataIdentifier
from mqspeak.broker import Broker
from mqspeak.channel import Channel
import datetime

def main():
    system = System()

    channelConvertMapping = system.getChannelConvertMapping()
    updateDispatcher = ChannelUpdateDispatcher.createThingSpeakUpdateDispatcher(channelConvertMapping)

    # params: updateBuffers, channelUpdateSupervisor
    dataCollector = DataCollector(system.getUpdateBuffers, None)

    brokerManager = BrokerThreadManager(system.getBrokerListenDescriptors(), None)

    # run all MQTT client threads
    brokerManager.start()

    # run main thread
    updateDispatcher.run()

    # program exit
    updateDispatcher.stop()

if __name__ == '__main__':
    main()
