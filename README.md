# mqspeak - MQTT bridge

mqspeak is [MQTT](http://mqtt.org/) client which collect data and transforms
them into [ThingSpeak](https://thingspeak.com/) channel updates or [Phant](http://phant.io/)
data streams. It is able to handle multiple MQTT connections and independetly update
multiple channels.

This is part of my IoT project. You can
read more about it on my [blog](http://buben19.blogspot.com/).

## Install

Application can be installed with following command:

    $ sudo pip3 install mqspeak

## Configuration

mqspeak is configured using configuration file specified with `-c` or `--config`
option (default `/etc/mqspeak.conf`). This is sample configuration file:

    [Brokers]
    Enabled = temperature-broker humidity-broker door-broker

    [temperature-broker]
    Host = temperatureBrokerHostname
    Port = 1883
    User = brokerUser
    Password = brokerPass
    Topic = sensors/temperature sensors/something

    [humidity-broker]
    Host = humidityBrokerHostname
    Port = 1883
    User = brokerUser
    Password = brokerPass
    Topic = sensors/humidity

    [door-broker]
    Host = doorBrokerHostname
    Port = 1883
    User = brokerUser
    Password = brokerPass
    Topic = #

    [Channels]
    Enabled = channel1 channel2 channel3 channel4

    [channel1]
    Id = CHANNELID
    Key = CHANNELKEY
    Type = thingspeak
    UpdateRate = 15
    UpdateType = blackout
    UpdateFields = dht-update

    [channel2]
    Id = CHANNELID
    Key = CHANNELKEY
    Type = thingspeak
    UpdateRate = 15
    UpdateType = buffered
    UpdateFields = dht-update

    [channel3]
    Id = CHANNELID
    Key = CHANNELKEY
    Type = thingspeak
    UpdateRate = 15
    UpdateType = average
    UpdateFields = dht-update

    [channel4]
    Id = CHANNELID
    Key = CHANNELKEY
    Type = phant
    UpdateRate = 15
    UpdateType = onchange
    UpdateFields = door-update

    [dht-update]
    field1 = humidity-broker sensors/humidity
    field2 = temperature-broker sensors/temperature

    [door-update]
    state = door-broker sensors/door

Configuration file has two mandatory sections: `[Brokers]` and `[Channels]`, each with
one `Enabled` option. These options contains space separated broker and channel
section names.

### Broker section

Broker section has to define one mandatory `[Topic]` option, which is space separated
list of MQTT topic subscriptions. Full list of possible options in broker section:

 - `Host` - Broker IP address or hostname (default 127.0.0.1).
 - `Port` - Broker port (default 1883).
 - `User` - Username.
 - `Password` - Password.
 - `Topic` - Space separated list of topic subscriptions. Mandatory option.

### Channel section

Each channel section has to define `Key`, `UpdateRate` and `UpdateType` options.

 - `Id` - Channel ID. This field is mandatory for Phant channels.
 - `Key` - Channel API write key. Mandatory option.
 - `Type` - Specify channel type. Mandatory option. Following types are supported:
   - `thingspeak` - [ThinkSpeak](https://thingspeak.com/) channel.
   - `phant` - [Phant](http://phant.io/) channel.
 - `UpdateRate` - Channel update interval in seconds. Currently, ThinkSpeak allows
   interval 15 seconds or greater. Mandatory option.
 - `WaitInterval` - Maximum interval to wait for remaining data to arrive. When set to
    zero, wait forever (default). See **Update waiting** for more details.
 - `UpdateType` - Channel update type. Possible values are `blackout`, `buffered`,
   `average` and `onchange`. Mandatory option.
   - `blackout` - Until `UpdateRate` interval is expired, any incoming data are
     ignored. First data received after interval expiration are sent to ThingSpeak.
   - `buffered` - Incoming data are buffered during `UpdateRate` interval. After
     this interval expires, most recent values are immediately sent.
   - `average` - Similar to `buffered` but mqspeak calculates average value of these
     data. Any data which cannot be converted into real numbers are ignored. Channel
     is immediately updated after `UpdateRate` interval is expired.
   - `onchange` - Data are marked with timestamp and stored in queue. Each item is
     sent after `UpdateRate` interval expires. **_Not implemented yet._**
 - `UpdateFields` - Specify section which defines updates for this channel. Mandatory option.

#### Update waiting

When channel update consists of data from multiple sensors, it may happen that one
sensor die. By default channel never will be updated until data from all sensors arrives.
Inactive sensor causes channel update will be stalled.

When update waiting enabled, mqspeak will wait defined amount of seconds and then sends
out even incomplete channel update.

Waiting scenario can be divided into following cases:

 - **`UpdateRate` condition is met but there are no data.** Wait mechanism is not activated
    until some data arrives. After it received first part of channel update, mqspeak will wait
    defined time and tries collect remaining data. After `WaitInterval` expires,
    data will be send.
 - **Partial data arrives before `UpdateRate` condition is met.** Waiting is delayed
    until `UpdateRate` condition is met. After it expires and there are still not
    all required data, waiting is triggered. After `WaitInterval` expires, data
    will be send.
 - **All required data are collected before `UpdateRate` condition is met.** There is no
    need to activate update waiting. Simply send data.

### UpdateFields section

UpdateFields section consists of any number of options. Each option key specifies
field name. Its value must be space separated name of broker section and topic.

For ThinkSpeak channel, only option keys `Field1` ... `Field8` are valid.

## Questions

 - **mqspeak runs in foreground only.** - Yes, there is no double fork combo to run
   mqspeak in background. I use systemd init and I prefer to run all services as simple
   systemd units, which runs in foreground. Sorry about that.
 - **It uses python3. Is python 2.x supported?** - No, I don't plan to support python 2.x.
