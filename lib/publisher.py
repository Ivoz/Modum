import gevent

class Publisher(object):

    def __init__(self):
        self.channels = set()
        self.subscribers = set()
        self.subscriptions = {}
        self.publications = {}

    def subscribe(self, subscriber, channel):
        self.subscriptions[hash(channel)].add(subscriber)
        self.subscribers.add(subscriber)

    def unsubscribe(self, subscriber, channel):
        self.subscriptions[hash(channel)].remove(subscriber)
        self.subscribers.remove(subscriber)

    def publish(self, channel, modify=lambda x: x):
        self.channels.add(channel)
        self.subscriptions[hash(channel)] = set()
        def publication():
            for article in channel:
                for sub in self.subscriptions[hash(channel)]:
                    sub.put(modify(article))
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
