import gevent


class Publisher(object):

    def __init__(self):
        self.channels = set()
        self.subscriptions = {}
        self.publications = {}

    def subscribe(self, subscriber, channel, modifier=None):
        if modifier is None:
            modifier = lambda x: x
        if channel not in self.channels:
            self.publish(channel)
        self.subscriptions[hash(channel)][hash(
            subscriber)] = (subscriber, modifier)

    def unsubscribe(self, subscriber, channel):
        del self.subscriptions[hash(channel)][hash(subscriber)]
        if len(self.subscriptions[hash(channel)]) == 0:
            self.unpublish(channel)

    def publish(self, channel):
        self.channels.add(channel)
        self.subscriptions[hash(channel)] = {}

        def publication():
            for article in channel:
                for subscriber, modifier in self.subscriptions[
                        hash(channel)].values():
                    subscriber.put(modifier(article))
        self.publications[hash(channel)] = gevent.spawn(publication)

    def unpublish(self, channel):
        del self.subscriptions[hash(channel)]
        channel.put(StopIteration)
        self.publications[hash(channel)].kill()
        del self.publications[hash(channel)]
        self.channels.remove(channel)

    def kill_loop(self):
        for channel in self.channels:
            self.unpublish(channel)
