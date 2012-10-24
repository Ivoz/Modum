from lib.irc import Irc, Msg
from lib.publisher import Publisher
from lib.stdio import StdIO
import gevent
from gevent.queue import Queue


class Client(object):

    def __init__(self, name, config):
        self.name = name
        self.config = config
        self.publisher = Publisher()
        # Initialize irc connection
        server = config.clients[name]['server']
        self.server = config.servers[server]
        self.irc = Irc(config.servers[server], self.publisher)
        # Configuration
        self.nick = config.clients[name]['nick']
        self.stdio = StdIO()
        self.sending = Queue()
        self.receiving = Queue()
        self.instance = None

    def start(self):
        if self.instance is not None:
            raise
        self.publisher.subscribe(self.irc.sender, self.sending)
        self.publisher.subscribe(self.receiving, self.irc.receiver)
# TODO: Remove, debugging
        self.publisher.subscribe(self.stdio.output,
            self.irc.receiver, str)
        self.publisher.subscribe(self.stdio.output,
            self.irc.sender, str)
        self.irc.connect()
        self.instance = gevent.spawn(self._event_loop)
        return self.instance

    def _event_loop(self):
# TODO: Add cleanup stuff
        self.sending.put(Msg('NICK', self.nick))
        self.sending.put(Msg('USER',
            [self.nick, '8', '*', self.nick]))
        for msg in self.receiving:
            if msg is FinishLoop:
                break
            func = getattr(self, msg.cmd, self.unknown)
            try:
                func(msg)
            except:
                pass

    def kill(self):
        self.irc.kill()
# TODO: Remove, debugging
        self.publisher.unsubscribe(self.irc.sender, self.sending)
        self.publisher.unsubscribe(self.receiving, self.irc.receiver)
        self.publisher.unsubscribe(self.stdio.output,
            self.irc.receiver)
        self.publisher.unsubscribe(self.stdio.output,
            self.irc.sender)
        self.stdio.stop()
        self.receiving.put(FinishLoop)

    def unknown(self, msg):
        """Fallback handler"""
        if msg.cmd.isdigit():
            self.stdio.output.put("Unknown call: " + msg.cmd)

    def PING(self, msg):
        msg.cmd = 'PONG'
        self.sending.put(msg)

    def PRIVMSG(self, msg):
        if self.nick == msg.params[0]:
            if 'quit' in msg.params[1]:
                print 'quitting...'
                self.kill()


class FinishLoop(StopIteration):
    pass


class Channel(object):

    def __init__(self, name):
        self.name = name


class User(object):

    def __init__(self, nick, user='', host=''):
        self.nick = nick
        self.user = user
        self.host = host

    @classmethod
    def from_msg(cls, message):
        return cls(message.nick, message.user, message.host)
