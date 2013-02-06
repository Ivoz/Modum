import gevent
from gevent.queue import Queue
from lib.irc import Irc
from lib.publisher import Publisher


class Client(object):
    """An IRC Client, designed to be pluggable"""

    def __init__(self, name, config):
        self.name = name
        self.config = config  # Overall config
        self.options = config.clients[name]  # Client options
        self.publisher = Publisher()
        # Initialize Irc connection object
        self.server = config.servers[self.options['server']]
        self.irc = Irc(self.server, self.publisher)
        # Configuration
        self.nick = self.options['nick']
        self.sending = Queue()
        self.receiving = Queue()
        # Plugins
        self.instance = None

    def start(self):
        if self.instance is not None:
            raise
        self.instance = gevent.spawn(self._event_loop)
        self.publisher.subscribe(self.irc.sender, self.sending)
        self.publisher.subscribe(self.irc.receiver, self.receiving)
        return self.instance

    def kill(self):
        """Completely close connection to server"""
        while not self.sending.empty():
            gevent.sleep(0.5)
        self.irc.kill()
        self.publisher.unsubscribe(self.irc.sender, self.sending)
        self.publisher.unsubscribe(self.irc.receiver, self.receiving)
        self.receiving.put(FinishLoop)
# TODO: Remove, debugging

    def _event_loop(self):
        for msg in self.receiving:
            if msg is FinishLoop:
                break


class FinishLoop(StopIteration):
    pass
