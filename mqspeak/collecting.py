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

from mqspeak.data import Measurement

class DataCollector:
    """
    Object for collecting received data from MQTT brokers. This object is also resposible
    to provide received data to each update buffer. If some of update buffers becomes full,
    its content is given to ChannelUpdateSupervisor object.
    """

    def __init__(self, updateBuffers, channelUpdateSupervisor):
        """
        updateBuffers: list of UpdateBuffer objects
        channelUpdateSupervisor: update supervisor
        """
        self.updateBuffers = updateBuffers
        self.channelUpdateSupervisor = channelUpdateSupervisor

    def onNewData(self, dataIdentifier, data):
        for updateBuffer in self.updateBuffers:
            updateBuffer.updateReceivedData(dataIdentifier, data)
            if updateBuffer.isComplete():
                data = updateBuffer.getData()
                updateBuffer.reset()

                measurement = Measurement.currentMeasurement(data)
                self.channelUpdateSupervisor.dataAvailable(updateBuffer.channel, measurement)

class UpdateBuffer:
    """
    Object for buffering reqired data set before delivering them to ThingSpeak.
    """

    def __init__(self, channel, dataIdentifiers):
        """
        channel: channel identification object
        dataIdentifiers: iterable of DataIdentifier objects
        """
        self.channel = channel
        self.dataIdentifiers = dataIdentifiers
        self.reset()

    def isComplete(self):
        return not any(x is None for x in self.dataDict.values())

    def updateReceivedData(self, dataIdentifier, value):
        """
        throws TopicException: if unnessesary topic is updated
        """
        if dataIdentifier not in self.dataDict:
            raise TopicException("Illegal topic update: {0}".format(dataIdentifier))
        else:
            self.dataDict[dataIdentifier] = value

    def getData(self):
        if not self.isComplete():
            raise TopicException("Some topic data is missing")
        else:
            return self.dataDict

    def reset(self):
        self.dataDict = dict()
        for dataIdentifier in self.dataIdentifiers:
            self.dataDict[dataIdentifier] = None


class TopicException(Exception):
    pass
