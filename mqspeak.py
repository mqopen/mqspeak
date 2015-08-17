#!/usr/bin/env python3
from mqspeak.system import System
from mqspeak.receiving import BrokerThreadManager
from mqspeak.sending import ChannelUpdateDispatcher, ThingSpeakSender
from mqspeak.collecting import DataCollector, UpdateBuffer
from mqspeak.updating import ChannnelUpdateSupervisor, BlackoutUpdater
from mqspeak.data import MeasurementParamConverter, DataIdentifier
from mqspeak.broker import Broker
from mqspeak.channel import Channel
import datetime

def main():
    system = System()

    paramConverterMapping = {
        DataIdentifier(Broker("central-broker", "10.8.0.1", 1883), "sensors/humidity"): "field1",
        DataIdentifier(Broker("central-broker", "10.8.0.1", 1883), "sensors/temperature"): "field2"}
    paramConverter = MeasurementParamConverter(paramConverterMapping)
    channelConvertMapping = {Channel("testName", "CHANNELKEY"): paramConverter}
    sender = ThingSpeakSender(channelConvertMapping)
    updateDispatcher = ChannelUpdateDispatcher(sender)

    updaters = [BlackoutUpdater(updateDispatcher, datetime.timedelta(seconds = 20))]
    channelUpdateSupervisor = ChannnelUpdateSupervisor(updaters)

    updateBuffers = [
        UpdateBuffer(
            Channel("testName", "CHANNELKEY"),
            [DataIdentifier(Broker("central-broker", "10.8.0.1", 1883), "sensors/humidity"),
            DataIdentifier(Broker("central-broker", "10.8.0.1", 1883), "sensors/temperature")])]

    dataCollector = DataCollector(updateBuffers, channelUpdateSupervisor)

    brokerManager = BrokerThreadManager(system.config.listenDescriptors, dataCollector)

    # start sthreads
    brokerManager.start()
    updateDispatcher.run()

    # program exit
    updateDispatcher.stop()

if __name__ == '__main__':
    main()
