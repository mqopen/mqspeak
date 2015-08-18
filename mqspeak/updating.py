import sched
import datetime
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

    def dataAvailable(self, channelIdentifier, measurement):
        """
        Deliver new update to correct Updater object.
        """
        print("Update received: {0}: {1}".format(channelIdentifier, measurement))
        return
        updater = self.channelUpdaterMapping[channelIdentifier]
        updater.update()

class BaseUpdater:
    """
    Updater object base class
    """

    def __init__(self):
        self.isUpdateRunning = False

    def setDispatcher(self, dispatcher):
        self.dispatcher = dispatcher

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

    def __init__(self, updateInterval):
        """
        updateInterval: timedelta object
        """
        BaseUpdater.__init__(self)
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

    def __init__(self, updateInterval):
        TimeBasedUpdater.__init__(self, updateInterval)

    def dataAvailable(self, channelIdentifier, measurement):
        if self.isUpdateIntervalExpired() or self.isUpdateRunning:
            print("New data: {0} - {1}".format(channelIdentifier, measurement))
            #self.dispatcher.dispatch(channelIdentifier, measurement, self)

    def notifyUpdateResult(self, result):
        self.updateDone()

class BufferedUpdater(TimeBasedUpdater):
    """
    Implement some timer to send update is time elapses. Don't wait for incoming data
    after time expires.
    """

    def __init__(self, updateInterval):
        TimeBasedUpdater.__init__(self, updateInterval)
        self.scheduler = sched.scheduler(time.time, time.sleep)

class AverageUpdater(BufferedUpdater):
    """
    Like BufferedUpdater but keep track all data which wasn't send and calculate
    average value while sending them.
    """

    def __init__(self, updateInterval):
        BufferedUpdater.__init__(self, updateInterval)

class OnChangeUpdater(BaseUpdater):
    """
    Send every value change.
    """

    def __init__(self):
        BaseUpdater.__init__(self)
        self.changeBuffer = []
