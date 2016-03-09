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
import threading
import time
import queue
import sys
from mqspeak.data import Measurement

class ChannnelUpdateSupervisor:
    """!
    Manage channel updaters. Object is responsible to delivering channel update event to
    correct Updater object.
    """

    ## @var channelUpdaterMapping
    # Mapping for {channel: updater}.

    def __init__(self, channelUpdaterMapping):
        """!
        Initiate ChannnelUpdateSupervisor object.

        @param channelUpdaterMapping Mapping for {channel: updater}.
        """
        self.channelUpdaterMapping = channelUpdaterMapping

    def dataAvailable(self, channel, measurement):
        """!
        Deliver new update to correct Updater object.

        @param channel
        @param measurement
        """
        updater = self.channelUpdaterMapping[channel]
        updater.dataAvailable(measurement)

    def setDispatcher(self, dispatcher):
        """!
        Assign a dispatcher to all updaters.

        @param dispatcher
        """
        for updater in self.channelUpdaterMapping.values():
            updater.setDispatcher(dispatcher)

    def stop(self):
        """!
        Stop execution of all updaters.
        """
        for updater in self.channelUpdaterMapping.values():
            updater.stop()

class BaseUpdater:
    """!
    Updater object base class!
    """

    ## @var channel
    # Updated channel.

    ## @var updateInterval
    # Channel update interval.

    ## @var isUpdateRunning
    # Boolean variable to keep track if some update is currently running.

    ## @var lastUpdated
    # Last update time.

    ## @var updateLock
    # Mutual exclusion to running updates.

    ## @var dispatcher
    # Update dispatcher object.

    def __init__(self, channel, updateInterval):
        """!
        Initiate BaseUpdater object.

        @param channel Updated channel.
        @param updateInterval Update interval.
        """
        self.channel = channel
        self.updateInterval = updateInterval
        self.isUpdateRunning = False
        self.lastUpdated = datetime.datetime.min
        self.updateLock = threading.Semaphore(1)

    def setDispatcher(self, dispatcher):
        """!
        Assign a dispatcher.

        @param dispatcher Dispatcher object.
        """
        self.dispatcher = dispatcher

    def dataAvailable(self, measurement):
        """!
        Update new data.

        @param measurement
        """
        self.updateLock.acquire()
        self.handleAvailableData(measurement)
        self.updateLock.release()

    def runUpdate(self, measurement):
        """!
        Call this method in sub-class from handleAvailableData method.

        @param measurement
        """
        self.isUpdateRunning = True
        self.dispatcher.updateAvailable(self.channel, measurement, self)

    def runUpdateLocked(self, measurement):
        """!
        Run update. This method avoids race conditions. Do not call this method
        from handleAvailableData() metod - causes dead lock.

        @param measurement
        """
        self.updateLock.acquire()
        self.runUpdate(measurement)
        self.updateLock.release()

    def notifyUpdateResult(self, result):
        """!
        Callback method with update result

        @param result UpdateResult object.
        """
        self.updateLock.acquire()
        self.isUpdateRunning = False
        if result.wasSuccessful():
            self.restartUpdateIntervalCounter()
        self.resolveUpdateResult(result)
        self.updateLock.release()

    def stop(self):
        """!
        Override this method if updater manage some other running thread.
        """

    def isUpdateIntervalExpired(self):
        """!
        Check if Update interval has expired.

        @return True if update interval has expired, False otherwise.
        """
        return (datetime.datetime.now() - self.lastUpdated) > self.updateInterval

    def restartUpdateIntervalCounter(self):
        """!
        Restart interval counter.
        """
        self.lastUpdated = datetime.datetime.now()

    def handleAvailableData(self, measurement):
        """!
        Handle new data in updater. Override this mehod in sub-class.

        @param measurement New data measurement.
        """
        raise NotImplementedError("Override this mehod in sub-class")

    def resolveUpdateResult(self, result):
        """!
        Resolve update result in updater. Override this mehod in sub-class.

        @param result UpdateResult object.
        """
        raise NotImplementedError("Override this mehod in sub-class")

class BlackoutUpdater(BaseUpdater):
    """!
    Ignore any incomming data during blackkout period. Send first data after this
    period expires.
    """

    def handleAvailableData(self, measurement):
        """!
        @copydoc BaseUpdater::handleAvailableData()
        """
        if self.isUpdateIntervalExpired() and not self.isUpdateRunning:
            self.runUpdate(measurement)

    def resolveUpdateResult(self, result):
        """!
        @copydoc BaseUpdater::resolveUpdateResult()
        """
        pass

class SynchronousUpdater(BaseUpdater):
    """!
    Base class for all updaters which tries to update channel in synchronous fashion.
    """

    ## @var isUpdateScheduled
    # Boolean variable to track if some update is already scheduled.

    ## @var bufferLock
    # Mutual exclusion for measurement buffer.

    ## @var scheduleLock
    # Mutual exclusion for isUpdateScheduled flag.

    ## @var executors
    # Set of running executors.

    def __init__(self, channel, updateInterval):
        """!
        Initiate SynchronousUpdater object.

        @param channel
        @param updateInterval
        """
        BaseUpdater.__init__(self, channel, updateInterval)
        self.resetBuffer()
        self.isUpdateScheduled = False
        self.bufferLock = threading.Semaphore(1)
        self.scheduleLock = threading.Semaphore(1)
        # TODO: Check race conditions with this set.
        self.executors = set()

    def handleAvailableData(self, measurement):
        """!
        @copydoc BaseUpdater::handleAvailableData()
        """
        self.scheduleLock.acquire()
        if not self.isUpdateScheduled:
            if self.isUpdateRunning:
                # New data is available but update is still running.
                # Store data in buffer and schedule new update after current update is done.
                self.updateBuffer(measurement)
            else:
                self.runUpdate(measurement)
        else:
            # Update job is already scheduled. Just update buffer.
            self.updateBuffer(measurement)
        self.scheduleLock.release()

    def resolveUpdateResult(self, result):
        """!
        @copydoc BaseUpdater::resolveUpdateResult()
        """
        # Schedule new update job. Just for case that new data arrive before time
        # interval expires.
        self.scheduleLock.acquire()
        self.scheduleUpdateJob()
        self.scheduleLock.release()

    def updateBuffer(self, measurement):
        """
        Update buffered measurement.
        """
        self.bufferLock.acquire()
        self.storeUpdateData(measurement)
        self.bufferLock.release()

    def scheduleUpdateJob(self):
        """
        Schedule new update job.
        """
        self.isUpdateScheduled = True
        executor = SchedulerExecutor(
            datetime.timedelta(seconds=int(self.updateInterval.total_seconds())),
            self.onSchedule)
        threading.Thread(target=executor).start()
        self.executors.add(executor)

    def onSchedule(self, executor):
        """
        Callback method called when scheduler expires.
        """
        self.scheduleLock.acquire()
        self.executors.discard(executor)
        self.isUpdateScheduled = False
        if self.isDataBuffered():
            data = self.pullMeasurement()
            self.runUpdateLocked(data)
        self.scheduleLock.release()

    def pullMeasurement(self):
        """!
        Atomically get buferred measurement and clear buffer.

        @return Measurement.
        """
        d = None
        self.bufferLock.acquire()
        d = self.getMeasurement()
        self.resetBuffer()
        self.bufferLock.release()
        return d

    def stop(self):
        """!
        Stop all executors.
        """
        for executor in self.executors:
            executor.stop()
        self.executors = set()

    def resetBuffer(self):
        """!
        Clear internal buffer with measurements. Override this mehod in sub-class.
        """
        raise NotImplementedError("Override this mehod in sub-class")

    def storeUpdateData(self, measurement):
        """!
        Save new measurement. Override this mehod in sub-class.

        @param measurement
        """
        raise NotImplementedError("Override this mehod in sub-class")

    def isDataBuffered(self):
        """!
        Check if there are some stored measurements. Override this mehod in sub-class.
        """
        raise NotImplementedError("Override this mehod in sub-class")

    def getMeasurement(self):
        """!
        Get stored measurement. Override this mehod in sub-class.
        """
        raise NotImplementedError("Override this mehod in sub-class")

class BufferedUpdater(SynchronousUpdater):
    """!
    Implement some timer to send update is time elapses. Don't wait for incoming data
    after time expires.
    """

    ## @var measurement
    # Stored measurement.

    def resetBuffer(self):
        """!
        @copydoc SynchronousUpdater::resetBuffer()
        """
        self.measurement = None

    def storeUpdateData(self, measurement):
        """!
        @copydoc SynchronousUpdater::storeUpdateData()
        """
        self.measurement = measurement

    def isDataBuffered(self):
        """
        @copydoc SynchronousUpdater::isDataBuffered()
        """
        return self.measurement is not None

    def getMeasurement(self):
        """!
        @copydoc SynchronousUpdater::getMeasurement()
        """
        return self.measurement

class AverageUpdater(SynchronousUpdater):
    """!
    Like BufferedUpdater but keep track all data which wasn't send and calculate
    average value while sending them.
    """

    ## @var intervalMeasurements
    # Stored measurements to compute average values.

    def storeUpdateData(self, measurement):
        """!
        @copydoc SynchronousUpdater::storeUpdateData()
        """
        if self.isAllMeasurementValuesValid(measurement):
            self.intervalMeasurements.append(measurement)
        else:
            print("Can't convert all measured values to numbers: {}".format(measurement), file=sys.stderr)

    def resetBuffer(self):
        """!
        @copydoc SynchronousUpdater::resetBuffer()
        """
        self.intervalMeasurements = []

    def isDataBuffered(self):
        """!
        @copydoc SynchronousUpdater::isDataBuffered()
        """
        return len(self.intervalMeasurements) > 0

    def getMeasurement(self):
        """!
        @copydoc SynchronousUpdater::getMeasurement()
        """
        return self.createAverageMeasurement()

    def createAverageMeasurement(self):
        """!
        Create measurement from collected data during update interval period.
        """
        averageData = {}
        for measurement in self.intervalMeasurements:
            for dataIdentifier, value in measurement.fields.items():
                if dataIdentifier not in averageData:
                    averageData[dataIdentifier] = 0
                averageData[dataIdentifier] += float(value)
        for dataIdentifier, value in averageData.items():
            averageData[dataIdentifier] = averageData[dataIdentifier] / float(len(self.intervalMeasurements))
        lastTime = self.intervalMeasurements[-1]
        return Measurement(averageData, lastTime)

    def isAllMeasurementValuesValid(self, measurement):
        """!
        Check if all measurement data can be converted to floating point numbers.

        @param measurement Measurement object.
        """
        for dataIdentifier, value in measurement.fields.items():
            try:
                float(value)
            except ValueError as ex:
                return False
        return True

class OnChangeUpdater(BaseUpdater):
    """!
    Send every value change.
    """

    ## @var changeBuffer
    # Store data which needs to be send.

    def __init__(self, channel):
        """!
        Initiate OnChangeUpdater object.

        @param channel
        """
        BaseUpdater.__init__(self, channel)
        self.changeBuffer = []
        raise NotImplementedError("Not implemented yet")

    def handleAvailableData(self, measurement):
        """!
        @copydoc BaseUpdater::handleAvailableData()
        """
        raise NotImplementedError("Not implemented yet")

    def resolveUpdateResult(self, result):
        """!
        @copydoc BaseUpdater::resolveUpdateResult()
        """
        raise NotImplementedError("Not implemented yet")

class SchedulerExecutor:
    """!
    Execute scheduler object in separate thread.
    """

    ## @var event
    # Event object.

    ## @var scheduleTime
    # Schedule time.

    ## @var action
    # Scheduled action.

    def __init__(self, scheduleTime, action):
        """!
        Initiate scheduler executor.

        @param scheduleTime Timedelta object.
        @param action Callable object executed after schedule time expires. Action takes one argument,
            which is reference to this executor.
        """
        self.event = threading.Event()
        self.scheduleTime = scheduleTime
        self.action = action

    def __call__(self):
        """!
        Run schedule execution.
        """
        scheduleExpires = not self.event.wait(self.scheduleTime.total_seconds())
        if scheduleExpires:
            self.action(self)

    def stop(self):
        """!
        Stop scheduler execution.
        """
        self.event.set()
