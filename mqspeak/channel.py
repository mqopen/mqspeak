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

import enum

class ChannelType(enum.Enum):
    """
    Enumeration if channel types.
    """

    thingspeak = 0
    phant = 1

class Channel:
    """
    ThingSpeak channel identification object.
    """

    def __init__(self, channelType, name, channelID, apiKey):
        """
        Initiate channel object.

        channelType: ChannelType enumeration object
        name: channel name
        channelID: channel identification
        apiKey: channel write API key
        """
        self.channelType = channelType
        self.name = name
        self.channelID = channelID
        self.apiKey = apiKey

    def __hash__(self):
        return hash((self.name, self.apiKey))

    def __str__(self):
        return "{} [{} - {}]".format(self.name, self.channelID, self.apiKey)

    def __repr__(self):
        return "<{}>".format(self.__str__())

class ThingSpeakChannel(Channel):
    """
    ThingSpeak channel identification object.
    """

    def __init__(self, name, channelID, apiKey):
        Channel.__init__(self, ChannelType.thingspeak, name, channelID, apiKey)

class PhantChannel(Channel):
    """
    Phant channel identification object.
    """

    def __init__(self, name, channelID, apiKey):
        self.checkChannelIdentification(channelID)
        Channel.__init__(self, ChannelType.phant, name, channelID, apiKey)

    def checkChannelIdentification(self, channelID):
        if channelID is None:
            raise ChannelException("Phat channel must have identification")

class ChannelException:
    """
    Channel related exceptions.
    """
