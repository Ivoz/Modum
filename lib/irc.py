from gevent.queue import Queue
from lib.connection import Connection
from lib.replycodes import numerics


class Irc(object):
    """ Handles the IRC protocol """

    def __init__(self, server, name, publisher):
        self.name = name
        self._conn = Connection(server['host'], server['port'],
                    server['ssl'], server['timeout'])
        self.wait_for_connection = self._conn.connection.wait
        # The canonical channels of IRC to subscribe / publish
        # Receives input to send to irc server
        self.sender = Queue()
        # Receives output to publish
        self.receiver = Queue()
        self.publisher = publisher
        # Suscribe my output to receive data from connection
        self.publisher.subscribe(self.receiver, self._conn.receiver, Msg.from_msg)
        # Subscribe connection to send data from my input
        self.publisher.subscribe(self._conn.sender, self.sender, str)

    @property
    def connected(self):
        return self._conn.connected

    def connect(self):
        if self.connected:
            return True
        err = self._conn.connect()
        if self.connected:
            return True
        else:
            return err

    def disconnect(self):
        self._conn.disconnect()
        return self.connected


class Msg(object):
    """ Represents an IRC message to be sent or decoded """

    def __init__(self, cmd='', params=None, prefix=None, msg=None):
        self.prefix = prefix
        self.cmd = cmd
        self.params = params if params is not None else []
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
        #Needed to properly split 1 argument
        msg = ' ' + msg
        if self.cmd in numerics:
            # Should be a server reply
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
        if ' :' in msg:
            msg, trailing = msg.split(' :', 1)
        self.params = filter(lambda x: len(x) > 0, msg.split(' '))
        if trailing is not None:
            self.params.append(trailing)

    def encode(self):
        msg = ''
        if self.prefix is not None:
            msg += ':' + self.prefix + ' '
        msg += self.cmd
        if len(self.params) == 0:
            return msg
        self.params[-1] = ':' + self.params[-1]
        for p in self.params:
            msg += ' '
            msg += p
        return msg

    def __str__(self):
        return self.encode()
