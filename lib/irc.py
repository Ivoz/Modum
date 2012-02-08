from gevent.queue import Queue
from lib.connection import Connection
from lib.replycodes import replycodes

# Constants for IRC special chars
SPACE = ' '
NULL = '\0'
DELIM = ':'


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
        self.publisher.subscribe(self.receiver, self._conn.receiver, Msg)
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

    def __init__(self, msg=None, prefix='', cmd='', params=None):
        self.prefix = prefix
        self.cmd = cmd
        self.params = params if params is not None else []
        self.server = False
        self.nick = prefix
        self.user = None
        self.host = None
        if msg is not None:
            self.decode(msg)

    def decode(self, msg):
        if msg.startswith(DELIM):
            self.prefix, msg = msg[1:].split(SPACE, 1)
            msg = msg.lstrip(SPACE)
        self.cmd, msg = msg.split(SPACE, 1)
        if self.cmd in replycodes:
            self.cmd = replycodes[self.cmd]
        if (self.cmd.startswith('RPL_') or self.cmd.startswith('ERR_')):
            self.server = True
            self.host = self.prefix
            self.nick = self.prefix
        else:
            try:
                self.nick, left = self.prefix.split('!', 1)
                self.user, self.host = left.split('@', 1)
            except ValueError:
                self.nick = self.prefix
        while (len(msg) > 0):
            if msg.startswith(DELIM):
                self.params.append(msg[1:])
                break
            if SPACE in msg:
                p, msg = msg.split(SPACE, 1)
            else:
                p = msg
                msg = ''
            self.params.append(p.strip(SPACE))

    def encode(self):
        msg = ''
        if (len(self.prefix) > 0):
            msg += DELIM + self.prefix + SPACE
        msg += self.cmd
        self.params[-1] = ':' + self.params[-1]
        for p in self.params:
            msg += SPACE
            msg += p
        return msg

    def __repr__(self):
        return self.encode()

    def __str__(self):
        return self.encode()
