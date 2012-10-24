import gevent


class Publisher(object):
    """Links and distributes Queue messsages"""

    def __init__(self):
        self.channels = set()
        self.subscriptions = {}
        self.publications = {}

    def subscribe(self, subscriber, channel, modifier=None):
        if modifier is None:
            modifier = lambda x: x
        if channel not in self.channels:
            self._publish(channel)
        self.subscriptions[hash(channel)][hash(
            subscriber)] = (subscriber, modifier)

    def unsubscribe(self, subscriber, channel):
        del self.subscriptions[hash(channel)][hash(subscriber)]
        if len(self.subscriptions[hash(channel)]) == 0:
            self._unpublish(channel)

    def _publish(self, channel):
        self.channels.add(channel)
        self.subscriptions[hash(channel)] = {}

        def publication(chan):
            for article in chan:
                if article is Depublicise:
                    break
                for subscriber, modifier in self.subscriptions[
                        hash(channel)].values():
                    subscriber.put(modifier(article))
        self.publications[hash(channel)] = gevent.spawn(publication, channel)

    def _unpublish(self, channel):
        channel.put(Depublicise)
        del self.subscriptions[hash(channel)]
        del self.publications[hash(channel)]
        self.channels.remove(channel)

    def kill_loop(self):
        for channel in self.channels:
            self._unpublish(channel)


class Depublicise(StopIteration):
    pass
