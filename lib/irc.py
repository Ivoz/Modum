import gevent
from gevent.queue import Queue
from gevent.event import Event
from lib.connection import Connection
from lib.replycodes import numerics


class Irc(object):
    """ Handles the IRC protocol """

    def __init__(self, server, name, publisher):
        self.name = name
        self.server = server
        self._conn = Connection(server['host'], server['port'],
                    server['ssl'], server['timeout'])
        # Timer to prevent flooding
        self.timer = Event()
        self.timer.set()
        # The canonical channels of IRC to subscribe / publish
        # Receives input to send to irc server
        self.sender = Queue()
        # Receives output to publish
        self.receiver = Queue()
        self.publisher = publisher
        # Suscribe my output to receive data from connection
        self.publisher.subscribe(self.receiver,
                self._conn.receiver, Msg.from_msg)
        # Subscribe connection to send data from my input
        self.publisher.subscribe(self._conn.sender,
                self.sender, self._prevent_flood)

    def __del__(self):
        self.publisher.unsubscribe(self.receiver, self._conn.receiver)
        self.publisher.subscribe(self._conn.sender, self.sender)
        del self._conn

    @property
    def connected(self):
        return self._conn.connected

    def connect(self):
        if self.connected:
            return True
        self._conn.connect()
        if self.connected:
            return True
        else:
            return self._conn.state

    def disconnect(self):
        self._conn.disconnect()
        return self.connected

    def _prevent_flood(self, msg):
        self.timer.wait()
        self.timer.clear()
        gevent.spawn_later(1, self.timer.set)
        return str(msg)


class Msg(object):
    """ Represents an IRC message to be sent or decoded """

    def __init__(self, cmd='', params=None, prefix='', msg=None):
        """Params should be a string or list of strings"""
        self.prefix = prefix
        self.cmd = cmd
        self.cmdnumber = None
        params = params if params is not None else []
        self.params = [params] if isinstance(params, basestring) else params
        self.params = filter(lambda x: len(x) > 0, self.params)
        self.server = False
        self.nick = prefix
        self.user = None
        self.host = None
        if msg is not None:
            self.decode(msg)

    @classmethod
    def from_msg(cls, message):
        return cls(msg=message)

    def decode(self, msg):
        if msg.startswith(':'):
            self.prefix, msg = msg[1:].split(' ', 1)
        self.cmd, msg = msg.split(' ', 1)
        msg = ' ' + msg
        #Needed to properly split 1 argument
        if self.cmd in numerics:
            # Should be a server reply
            self.cmdnumber = self.cmd
            self.cmd = numerics[self.cmd]
            self.server = True
            self.host = self.prefix
            self.nick = self.prefix
        else:
            try:
                self.nick, left = self.prefix.split('!', 1)
                self.user, self.host = left.split('@', 1)
            except ValueError:
                self.nick = self.prefix
        trailing = None
        if msg.find(' :') != -1:
            msg, trailing = msg.split(' :', 1)
        self.params = filter(lambda x: len(x) > 0, msg.split(' '))
        if trailing is not None:
            self.params.append(trailing)

    def encode(self):
        msg = ''
        if len(self.prefix) > 0:
            msg += ':' + self.prefix + ' '
        msg += self.cmd
        if len(self.params) == 0:
            return msg
        if len(self.params) > 1:
            msg += ' ' + ' '.join(self.params[:-1])
        msg += ' :' + self.params[-1]
        return msg

    def __str__(self):
        return self.encode()
