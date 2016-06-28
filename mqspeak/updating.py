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
import logging
from mqspeak.collecting import LastValueUpdateBuffer, AverageUpdateBuffer, ChangeValueBuffer
from mqreceive.collecting import DataCollector
from mqspeak.data import Measurement

class ChannnelUpdateSupervisor(DataCollector):
    """!
    Manage channel updaters. Object is responsible to delivering channel update event to
    correct Updater object.
    """

    ## @var channelUpdaterMapping
    # Mapping for {channel: updater}.

    ## @var waitingChannels
    # Mapping of channels which has some data wainting.

    def __init__(self, channelUpdaterMapping):
        """!
        Initiate ChannnelUpdateSupervisor object.

        @param channelUpdaterMapping Mapping for {channel: updater}.
        """
        self.channelUpdaterMapping = channelUpdaterMapping
        self.waitingChannels = {}
        self.waintingUpdater = SchedulerExecutor(
            datetime.timedelta(seconds = 1),
            self.updateWaitingData)
        threading.Thread(target = self.waintingUpdater).start()

    def updateWaitingData(self, executor):
        """!
        Do partitial update. Clear waiting data.
        """
        for updater in self.channelUpdaterMapping.values():
            updater.notifyUpdateWaiting()
        threading.Thread(target = self.waintingUpdater).start()

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
        self.waintingUpdater.stop()
        for updater in self.channelUpdaterMapping.values():
            updater.stop()

    def onNewData(self, dataIdentifier, data):
        try:
            data = data.decode("utf-8")
        except UnicodeError as ex:
            logging.getLogger().info("Can't decode received message payload: {}".format(repr(data)))

        for updater in self.channelUpdaterMapping.values():
            if updater.isUpdateRelevant(dataIdentifier):

                # Notify updater in separate thread for case that updater will
                # block for some reason.
                threading.Thread(
                    target = updater.updateReceivedData,
                    args = (dataIdentifier, data)).start()

class BaseUpdater:
    """!
    Updater base class.

    Before use of any instance of this class, call setDispatcher() method to
    assign a update disatcher. Update dispather is object which runs an update
    in its separate thread and notifies back an updater, when update finishes.
    """

    ## @var channel
    # Updated channel.

    ## @var updateInterval
    # Channel update interval.

    ## @var isUpdateRunning
    # Boolean variable to keep track if some update is currently running.

    ## @var lastUpdated
    # Last update time.

    ## @var waitingStarted
    # Timestamp of started waiting (when updater has some data and is in
    # waiting state) or None if updater doesn't wait for any remaning data.

    ## @var updateLock
    # Mutual exclusion to running updates.

    ## @var dispatcher
    # Update dispatcher object.

    ## @var updateBuffer
    # Channel UpdateBuffer object.

    def __init__(self, channel, updateInterval, updateBuffer):
        """!
        Initiate BaseUpdater object.

        @param channel Update Channel object.
        @param updateInterval timedelta object defining update interval.
        @param updateBuffer UpdateBuffer object.
        """
        self.channel = channel
        self.updateInterval = updateInterval
        self.isUpdateRunning = False
        self.lastUpdated = datetime.datetime.min
        self.waitingStarted = None
        self.updateLock = threading.Semaphore(1)
        self.updateBuffer = updateBuffer

    def setDispatcher(self, dispatcher):
        """!
        Assign a dispatcher.

        @param dispatcher Dispatcher object.
        """
        self.dispatcher = dispatcher

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

    def isUpdateRelevant(self, dataIdentifier):
        """!
        Check if update is relevant to this channel.

        @param dataIdentifier Update data identifier.
        @return True if update is relevant, False otherwise
        """
        return self.updateBuffer.isUpdateRelevant(dataIdentifier)

    def updateReceivedData(self, dataIdentifier, value):
        """!
        Update received data.

        @param dataIdentifier Data identification.
        @param value Data content.
        @throws TopicException If unwanted topic is updated.
        """
        # TODO: execute this code in separate thread. If one channel blocks, all
        # other channels will be also blocked.
        self.updateLock.acquire()
        try:
            self.updateBuffer.updateReceivedData(dataIdentifier, value)
            if not self.isUpdateRunning:
                if self.updateBuffer.isComplete():
                    self.dataComplete()
                else:
                    if self.isUpdateIntervalExpired() and \
                            self.channel.hasWaiting() and \
                            self.waitingStarted is None:
                        self.waitingStarted = datetime.datetime.now()
        except Exception as ex:
            logging.getLogger().error("Channel <{}>: {}".format(self.channel, ex))
        finally:
            self.updateLock.release()

    def notifyUpdateWaiting(self):
        """!
        Call this method periodically to chech if waiting interval has been
        exceeded.
        """
        if self.channel.hasWaiting():
            self.updateLock.acquire()
            try:
                if not self.isUpdateRunning:
                    if self.waitingStarted is not None :
                        delta = datetime.datetime.now() - self.waitingStarted
                        if self.updateBuffer.hasAnyData() and delta > self.channel.waiting:
                            logging.getLogger().warning(
                                "Waiting timeouted, data items {} hasn't any data.".format(
                                    ", ".join(str(x) for x in self.updateBuffer.getMissingDataIdentifiers())))
                            self.runUpdate()
                            self.updateBuffer.reset()
                    elif self.updateBuffer.hasAnyData() and self.isUpdateIntervalExpired():
                        # Update buffer store some data. Start waiting for a case that no
                        # more data will be received in the future.
                        self.waitingStarted = datetime.datetime.now()
            finally:
                self.updateLock.release()

    def dataComplete(self):
        """!
        Notify that all data needed for update is complete.
        """
        raise NotImplementedError("Override this mehod in sub-class")

    def runUpdate(self):
        """!
        Call this method in sub-class from handleAvailableData method.

        @param measurement
        """
        self.isUpdateRunning = True
        self.waitingStarted = None
        measurement = self.updateBuffer.getMeasurement()
        self.updateBuffer.reset()
        self.dispatcher.updateAvailable(self.channel, measurement, self)

    def runUpdateLocked(self):
        """!
        Run update. This method avoids race conditions. Do not call this method
        from handleAvailableData() metod - causes dead lock.

        @param measurement
        """
        self.updateLock.acquire()
        try:
            self.runUpdate()
        finally:
            self.updateLock.release()

    def notifyUpdateResult(self, result):
        """!
        Callback method with update result

        @param result UpdateResult object.
        """
        self.updateLock.acquire()
        try:
            self.isUpdateRunning = False
            if result.wasSuccessful():
                self.restartUpdateIntervalCounter()
            self.resolveUpdateResult(result)
        finally:
            self.updateLock.release()

    def resolveUpdateResult(self, result):
        """!
        Resolve update result in updater.

        @param result UpdateResult object.
        """
        raise NotImplementedError("Override this mehod in sub-class")

class BlackoutUpdater(BaseUpdater):
    """!
    Ignore any incomming data during blackout period. Send first data which arriver
    after blackout period expires.
    """

    def __init__(self, channel, updateMapping, updateInterval):
        BaseUpdater.__init__(
            self,
            channel,
            updateInterval,
            LastValueUpdateBuffer(updateMapping.keys()))

    def dataComplete(self):
        if self.isUpdateIntervalExpired() and not self.isUpdateRunning:
            self.runUpdate()

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

    ## @var scheduleLock
    # Mutual exclusion for isUpdateScheduled flag.

    ## @var executors
    # Set of running executors.

    def __init__(self, channel, updateInterval, updateBuffer):
        """!
        Initiate SynchronousUpdater object.

        @param channel
        @param updateInterval
        """
        BaseUpdater.__init__(self, channel, updateInterval, updateBuffer)
        self.isUpdateScheduled = False
        self.scheduleLock = threading.Semaphore(1)
        # TODO: Check race conditions with this set.
        self.executors = set()

    def dataComplete(self):
        self.scheduleLock.acquire()
        try:
            if not self.isUpdateScheduled:
                # There is no update sheduled. It is first run or data was unavailable
                # for the long time. Also, an another update is running.
                if not self.isUpdateRunning:
                    # No other update is running. Update immidiatelly.
                    self.runUpdate()
        finally:
            self.scheduleLock.release()

    def resolveUpdateResult(self, result):
        """!
        @copydoc BaseUpdater::resolveUpdateResult()
        """
        # An update just finished. Wait for configured time and run new update.
        self.scheduleLock.acquire()
        try:
            self.scheduleUpdateJob()
        finally:
            self.scheduleLock.release()

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
        try:
            self.executors.discard(executor)
            self.isUpdateScheduled = False
            if self.updateBuffer.isComplete():
                self.runUpdateLocked()
        finally:
            self.scheduleLock.release()

    def stop(self):
        """!
        Stop all executors.
        """
        for executor in self.executors:
            executor.stop()
        self.executors = set()

class BufferedUpdater(SynchronousUpdater):
    """!
    Implement some timer to send update is time elapses. Don't wait for incoming data
    after time expires.
    """

    def __init__(self, channel, updateMapping, updateInterval):
        SynchronousUpdater.__init__(
            self,
            channel,
            updateInterval,
            LastValueUpdateBuffer(updateMapping.keys()))

class AverageUpdater(SynchronousUpdater):
    """!
    Like BufferedUpdater but keep track all data which wasn't send and calculate
    average value while sending them.
    """

    def __init__(self, channel, updateMapping, updateInterval):
        SynchronousUpdater.__init__(
            self,
            channel,
            updateInterval,
            AverageUpdateBuffer(updateMapping.keys()))

class OnChangeUpdater(SynchronousUpdater):
    """!
    Send every value change.
    """

    def __init__(self, channel, updateMapping, updateInterval):
        SynchronousUpdater.__init__(
            self,
            channel,
            updateInterval,
            ChangeValueBuffer(updateMapping.keys()))

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
