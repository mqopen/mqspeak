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
    """!
    Enumeration of channel types.
    """

    thingspeak = 0
    phant = 1

class Channel:
    """!
    ThingSpeak channel identification object.
    """

    ## @var channelType
    # Type of channel.

    ## @var name
    # Channel name.

    ## @var channelID
    # Channel ID or None.

    ## @var apiKey
    # Channel API write key.

    ## @var waiting
    # Channel waiting timedelta object or None if waiting is disabled.

    def __init__(self, channelType, name, channelID, apiKey, waiting):
        """!
        Initiate channel object.

        @param channelType ChannelType enumeration object.
        @param name Channel name.
        @param channelID Channel identification.
        @param apiKey Channel write API key.
        @param waiting Channel waiting timedelta object of None
        """
        self.channelType = channelType
        self.name = name
        self.channelID = channelID
        self.apiKey = apiKey
        self.waiting = waiting

    def __hash__(self):
        """!
        Calculate hash from channel name and API key.

        @return Hash.
        """
        return hash((self.name, self.apiKey))

    def __str__(self):
        """!
        Convert Channel to string.

        @return String.
        """
        return "{} [Id: {}, Key: {}]".format(self.name, self.channelID, self.apiKey)

    def __repr__(self):
        """!
        Convert Channel to representation string.

        @return Representation string.
        """
        return "<{}>".format(self.__str__())

    def hasWaiting(self):
        """!
        Check if channel has waiting enabled.

        @return True if waiting is enabled, False otherwise.
        """
        return self.waiting is not None

class ThingSpeakChannel(Channel):
    """!
    ThingSpeak channel identification object.
    """

    def __init__(self, name, channelID, apiKey, waiting):
        """!
        Initiate ThingSpeak channel object.

        @param name Channel name.
        @param channelID Channel identification.
        @param apiKey Channel write key.
        """
        Channel.__init__(self, ChannelType.thingspeak, name, channelID, apiKey, waiting)

class PhantChannel(Channel):
    """
    Phant channel identification object.
    """

    def __init__(self, name, channelID, apiKey, waiting):
        """!
        Initiate Phant channel object.

        @param name Channel name.
        @param channelID Channel identification.
        @param apiKey Channel write key.
        """
        self.checkChannelIdentification(channelID)
        Channel.__init__(self, ChannelType.phant, name, channelID, apiKey, waiting)

    def checkChannelIdentification(self, channelID):
        """!
        Check if channelID is not None

        @throws ChannelException if channelID is None.
        """
        if channelID is None:
            raise ChannelException("Phant channel must have identification")

class ChannelException:
    """!
    Channel related exceptions.
    """
