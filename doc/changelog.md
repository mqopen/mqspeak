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

## v0.2.0

 - Mutexes are always released in finally block. Avoiding possible deadlocks.
 - Changed setup.py long description to content of README.md file.
 - Added channel waiting mechanism.
 - Logging to syslog.
 - Added `-o` option which instruct mqspek to log to stdout instead to syslog.
 - Average updater now calculates a average value from all MQTT topic updates.
    Not only from complete measurement.
 - Implemented `onchange` updater.
