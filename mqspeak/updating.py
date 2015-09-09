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

import datetime
import sched
import threading
import time

class ChannnelUpdateSupervisor:
    """
    Manage channel updaters. Object is responsible to delivering channel update event to
    correct Updater object.
    """

    def __init__(self, channelUpdaterMapping):
        """
        channelUpdaterMapping: mapping for {channel: updater}
        """
        self.channelUpdaterMapping = channelUpdaterMapping

    def dataAvailable(self, channel, measurement):
        """
        Deliver new update to correct Updater object.
        """
        updater = self.channelUpdaterMapping[channel]
        updater.dataAvailable(measurement)

    def setDispatcher(self, dispatcher):
        """
        Assign a dispatcher to all updaters.
        """
        for updater in self.channelUpdaterMapping.values():
            updater.setDispatcher(dispatcher)

class BaseUpdater:
    """
    Updater object base class
    """

    def __init__(self, channel):
        """
        channel: updated channel
        """
        self.channel = channel
        self.isUpdateRunning = False
        self.updateLock = threading.Semaphore(1)

    def setDispatcher(self, dispatcher):
        """
        Assign a dispatcher.

        dispatcher: dispatcher object
        """
        self.dispatcher = dispatcher

    def dataAvailable(self, measurement):
        """
        Update new data.
        """
        self.updateLock.acquire()
        self.handleAvailableData(measurement)
        self.updateLock.release()

    def handleAvailableData(self, measurement):
        """
        Handle new data in updater.

        measurement: new data measurement
        """
        raise NotImplementedError("Override this mehod in sub-class")

    def runUpdate(self, measurement):
        """
        Call this method in sub-class from handleAvailableData method.
        """
        self.isUpdateRunning = True
        self.dispatcher.updateAvailable(self.channel, measurement, self)

    def notifyUpdateResult(self, result):
        """
        Callback method with update result
        """
        self.updateLock.acquire()
        self.isUpdateRunning = False
        self.resolveUpdateResult(result)
        self.updateLock.release()

    def resolveUpdateResult(self, result):
        """
        Resolve update result in updater.

        result: TODO
        """
        raise NotImplementedError("Override this mehod in sub-class")

class TimeBasedUpdater(BaseUpdater):

    def __init__(self, channel, updateInterval):
        """
        updateInterval: timedelta object
        """
        BaseUpdater.__init__(self, channel)
        self.updateInterval = updateInterval
        self.lastUpdated = datetime.datetime.min

    def isUpdateIntervalExpired(self):
        """
        True if update interval has expired, False otherwise.
        """
        return (datetime.datetime.now() - self.lastUpdated) > self.updateInterval

    def resolveUpdateResult(self, result):
        self.lastUpdated = datetime.datetime.now()

class BlackoutUpdater(TimeBasedUpdater):
    """
    Ignore any incomming data during blackkout period. Send first data after this
    period expires.
    """

    def __init__(self, channel, updateInterval):
        TimeBasedUpdater.__init__(self, channel, updateInterval)

    def handleAvailableData(self, measurement):
        if self.isUpdateIntervalExpired() and not self.isUpdateRunning:
            self.runUpdate(measurement)

    def resolveUpdateResult(self, result):
        TimeBasedUpdater.resolveUpdateResult(self, result)

class BufferedUpdater(TimeBasedUpdater):
    """
    Implement some timer to send update is time elapses. Don't wait for incoming data
    after time expires.
    """

    def __init__(self, channel, updateInterval):
        TimeBasedUpdater.__init__(self, channel, updateInterval)
        self.scheduler = sched.scheduler(time.time, time.sleep)
        self.resetBuffer()
        self.isUpdateScheduled = False

        # Mutual exclusion for measurement buffer.
        self.bufferLock = threading.Semaphore(1)

        # Mutual exclusion for isUpdateScheduled flag.
        self.scheduleLock = threading.Semaphore(1)

    def handleAvailableData(self, measurement):
        self.scheduleLock.acquire()
        if not self.isUpdateScheduled:
            if self.isUpdateIntervalExpired() and not self.isUpdateRunning:
                self.runUpdate(measurement)
            else:
                # New data is available but update is still running.
                # Store data in buffer and schedule new update after current update is done
                self.updateBuffer(measurement)
        else:
            self.updateBuffer(measurement)
        self.scheduleLock.release()

    def resolveUpdateResult(self, result):
        TimeBasedUpdater.resolveUpdateResult(self, result)
        if self.isDataBuffered():
            self.isUpdateScheduled = True
            self.scheduler.enter(self.updateInterval.total_seconds(), 1, self.onSchedule)

    def resetBuffer(self):
        """
        Reset last stored measurement.
        """
        self.measurement = None

    def updateBuffer(self, measurement):
        """
        Update buffered measurement.
        """
        self.bufferLock.acquire()
        self.measurement = measurement
        self.bufferLock.release()

    def isDataBuffered(self):
        """
        True if some measurement is buffered, Flase otherwise.
        """
        return self.measurement is not None

    def pullMeasurement(self):
        """
        Atomically get buferred measurement and clear buffer.
        """
        d = None
        self.bufferLock.acquire()
        d = self.measurement
        self.resetBuffer()
        self.bufferLock.release()
        return d

    def onSchedule(self):
        """
        Callback method called when scheduler expires.
        """
        self.scheduleLock.acquire()
        data = self.pullMeasurement()
        self.isUpdateScheduled = False
        self.runUpdate(data)
        self.scheduleLock.release()

class AverageUpdater(BufferedUpdater):
    """
    Like BufferedUpdater but keep track all data which wasn't send and calculate
    average value while sending them.
    """

    def __init__(self, channel, updateInterval):
        BufferedUpdater.__init__(self, channel, updateInterval)
        raise NotImplementedError("Not implemented yet")

    def handleAvailableData(self, measurement):
        pass

    def resolveUpdateResult(self, result):
        pass

class OnChangeUpdater(BaseUpdater):
    """
    Send every value change.
    """

    def __init__(self, channel):
        BaseUpdater.__init__(self, channel)
        self.changeBuffer = []
        raise NotImplementedError("Not implemented yet")

    def handleAvailableData(self, measurement):
        pass

    def resolveUpdateResult(self, result):
        pass
