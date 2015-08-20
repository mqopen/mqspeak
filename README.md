# mqspeak - MQTT to ThingSpeak bridge

mqspeak is MQTT client which collect data and transforms them into ThingSpeak channel
updates. It is able to handle multiple MQTT connections and independetly update
multiple ThingSpeak channels.

### Configuration

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
    Key = CHANNELKEY
    UpdateRate = 15
    UpdateType = blackout
    Field1 = humidity-broker sensors/humidity
    Field2 = temperature-broker sensors/temperature

    [channel2]
    Key = CHANNELKEY
    UpdateRate = 15
    UpdateType = buffered
    Field1 = humidity-broker sensors/humidity
    Field2 = temperature-broker sensors/temperature

    [channel3]
    Key = CHANNELKEY
    UpdateRate = 15
    UpdateType = average
    Field1 = humidity-broker sensors/humidity
    Field2 = temperature-broker sensors/temperature

    [channel4]
    Key = CHANNELKEY
    UpdateRate = 15
    UpdateType = onchange
    Field1 = door-broker sensors/door

Configuration file has two mandatory sections: `[Brokers]` and `[Channels]`, each with
one `[Enabled]` option. These options contains space separated broker and channel
section names.

#### Broker section

Broker section has to define one mandatory `[Topic]` option, which is space separated
list of MQTT topic subscriptions. Full list of possible options in broker section:

- `Host` - Broker IP address or hostname (default 127.0.0.1).
- `Port` - Broker port (default 1883).
- `User` - Username.
- `Password` - Password.
- `Topic` - Space separated list of topic subscriptions (mandatory).

#### Channel section

Each channel section has to define `Key`, `UpdateRate` and `UpdateType` options.

- `Key` - Channel API write key.
- `UpdateRate` - Channel update interval in seconds. Currently, ThinkSpeak allows
  at least 15 seconds.
- `UpdateType` - Channel update type. Possible values are `blackout`, `buffered`,
  `average` and `onchange`
  - `blackout` - Until `UpdateRate` interval is expired, any incoming data are
    ignored. First data received after interval expiration are sent to ThingSpeak .
  - `buffered` - Incoming data are buffered during `UpdateRate` interval. After
    this interval expires, most recent values are immediately sent. **_Not implemented yet._**
  - `average` - Similar to `buffered` but mqspeak calculates average value of these
    data. Any data which cannot be converted into real numbers are ignored. Channel
    is immediately updated after `UpdateRate` interval is expired. **_Not implemented yet._**
  - `onchange` - Data are marked with timestamp and stored in queue. Each item is
    sent after `UpdateRate` interval expires. **_Not implemented yet._**
- `Field1` ... `Field8` - ThingSpeak field updates. This value contains space separated
  name of broker section and topic.

### Questions

- **mqspeak runs in foreground only.** - Yes, there is no double fork combo to run mqspeak in background. I use systemd init and I prefer to run all services as simple systemd units, which runs in foreground. Sorry about that.
- **It uses python3. Is python 2.x supported?** - No, I don't plan to support python 2.x.
