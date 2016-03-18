# mqspeak changelog

## v0.1.0

 - Initial release.
 - Implemented sending data to [TingSpeak](https://thingspeak.com/) servers.
 - Implemented sending data to [phant](http://phant.io/) servers.
 - blackout, average and buffered updates.
 - Supported MQTT user authentication.
 - Supported updating multiple channels.
 - Supported receiving data from multiple brokers.
 - Configured with .ini style config file.

## v0.1.1

 - Mutexes are always released in finally block. Avoiding possible deadlocks.
