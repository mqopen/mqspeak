import sched
import datetime
import time

class ChannnelUpdateSupervisor:
    """
    Manage channel updaters.
    """

    def __init__(self, updaters):
        """
        updaters: Updater object iterable
        """
        self.updaters = updaters

    def dataAvailable(self, channelIdentifier, measurement):
        updater = self.updater[channelIdentifier]
        updater.update()

class BaseUpdater:
    """
    Updater object base class
    """

    def __init__(self, dispatcher):
        self.dispatcher = dispatcher
        self.isUpdateRunning = False

    def update(self, measurement):
        """
        Update new data.
        """
        raise NotImplementedError("Override this mehod in sub-class")

    def notifyUpdateResult(self, result):
        """
        Callback method with update result
        """
        raise NotImplementedError("Override this mehod in sub-class")

class TimeBasedUpdater(BaseUpdater):

    def __init__(self, dispatcher, updateInterval):
        """
        updateInterval: timedelta object
        """
        BaseUpdater.__init__(self, dispatcher)
        self.updateInterval = updateInterval
        self.lastUpdated = datetime.datetime.min

    def isUpdateIntervalExpired(self):
        """
        true if update interval has expired, flase otherwise
        """
        return (datetime.datetime.now() - self.lastUpdated) > self.updateInterval

    def updateDone(self):
        self.lastUpdated = datetime.datetime.now()

class BlackoutUpdater(TimeBasedUpdater):

    def __init__(self, dispatcher, updateInterval):
        TimeBasedUpdater.__init__(self, dispatcher, updateInterval)

    def dataAvailable(self, channelIdentifier, measurement):
        print("Data available: {0}".format(measurement))
        return
        if self.isUpdateIntervalExpired() or self.isUpdateRunning:
            self.dispatcher.dispatch(channelIdentifier, measurement, self)

    def notifyUpdateResult(self, result):
        self.updateDone()

class BufferedUpdater(TimeBasedUpdater):
    """
    Implement some timer to send update is time elapses. Don't wait for incoming data
    after time expires.
    """

    def __init__(self, dispatcher, updateInterval):
        TimeBasedUpdater.__init__(self, dispatcher, updateInterval)
        self.scheduler = sched.scheduler(time.time, time.sleep)

class AverageUpdater(BufferedUpdater):
    """
    Like BufferedUpdater but keep track all data which wasn't send and calculate
    average value while sending them.
    """

    def __init__(self, dispatcher, updateInterval):
        BufferedUpdater.__init__(self, dispatcher, updateInterval)

class OnChangeUpdater(BaseUpdater):
    """
    Send every value change.
    """

    def __init__(self, dispatcher):
        BaseUpdater.__init__(self, dispatcher)
        self.changeBuffer = []
