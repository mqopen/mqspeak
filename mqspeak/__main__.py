#!/usr/bin/env python3
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

from mqreceive.receiving import BrokerThreadManager
from mqspeak.sending import ChannelUpdateDispatcher
from mqspeak.system import System
from mqspeak.updating import ChannnelUpdateSupervisor

def main():
    System.initialize()

    # Channel update dispatcher object
    channelConvertMapping = System.getChannelConvertMapping()
    updateDispatcher = ChannelUpdateDispatcher(channelConvertMapping)

    channelUpdateSupervisor = ChannnelUpdateSupervisor(System.getChannelUpdateMapping())
    channelUpdateSupervisor.setDispatcher(updateDispatcher)

    # MQTT cliens
    brokerManager = BrokerThreadManager(System.getBrokerListenDescriptors(), channelUpdateSupervisor)

    # run all MQTT client threads
    brokerManager.start()

    # run main thread
    try:
        updateDispatcher.run()
    except KeyboardInterrupt as ex:

        # program exit
        channelUpdateSupervisor.stop()
        brokerManager.stop()
        updateDispatcher.stop()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt as ex:
        pass
