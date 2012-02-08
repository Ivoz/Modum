import gevent

class Publisher(object):

    def __init__(self):
        self.channels = set()
        self.subscribers = set()
        self.subscriptions = {}
        self.publications = {}

    def subscribe(self, subscriber, channel, modifier=lambda x: x):
        self.subscriptions[hash(channel)][hash(subscriber)] = (subscriber, modifier)
        self.subscribers.add(subscriber)

    def unsubscribe(self, subscriber, channel):
        del self.subscriptions[hash(channel)][hash(subscriber)]
        self.subscribers.remove(subscriber)

    def publish(self, channel):
        self.channels.add(channel)
        self.subscriptions[hash(channel)] = {}
        def publication():
            for article in channel:
                for subscriber, modifier in self.subscriptions[hash(channel)].values():
                    subscriber.put(modifier(article))
        self.publications[hash(channel)] = gevent.spawn(publication)

    def unpublish(self, channel):
        self.publications[hash(channel)].kill()
        del self.subscriptions[hash(channel)]
        self.channels.remove(channel)

    def join_loop(self):
        gevent.joinall(self.publications.values())

    def kill_loop(self):
        for channel in self.channels:
            self.unpublish(channel)
