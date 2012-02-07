import gevent
from gevent.queue import Queue
from lib.connection import Connection
from lib.publisher import Publisher
from lib.replycodes import replycodes

# Constants for IRC special chars
SPACE = ' '
NULL = '\0'
DELIM = ':'


class Irc(object):
    """ Handles the IRC protocol """

    def __init__(self, server, name):
        self.name = name
        self._conn = Connection(server['host'], server['port'],
                    server['ssl'], server['timeout'])
        self.wait_for_connection = self._conn.connection.wait
        # The canonical channels of IRC to subscribe / publish
        # Receives input to send to irc server
        self.input = Queue()
        # Receives output to publish
        self.output = Queue()
        self.publisher = Publisher()
        self.publisher.publish(self.input, str)
        self.publisher.publish(self._conn.receiver, Msg)

    @property
    def connected(self):
        return self._conn.connected

    def connect(self):
        if self.connected:
            return True
        err = self._conn.connect()
        if self.connected:
            # Suscribe my output to receive data from connection
            self.publisher.subscribe(self.output, self._conn.receiver)
            # Subscribe connection to send data from my input
            self.publisher.subscribe(self._conn.sender, self.input)
            gevent.spawn_later(2, self._register)
            return True
        else:
            return err

    def disconnect(self):
        self._conn.disconnect()
        return self.connected

# TODO: Temporary. This stuff should be moved to the client
    def _register(self):
        nick = 'bob459'
        channels = '#bots,#bananaboat'
        self.input.put(Msg(cmd='NICK', params=[nick]))
        self.input.put(Msg(cmd='USER', params=[nick, '8', '*', ':' + nick]))
        self.input.put(Msg(cmd='JOIN', params=[channels]))


class Msg(object):
    """ Represents an IRC message to be sent or decoded """

    def __init__(self, msg=None, prefix='', cmd='', params=None):
        self.prefix = prefix
        self.cmd = cmd
        self.params = params if params is not None else []
        if msg is not None:
            self.decode(msg)

    def decode(self, msg):
# TODO: remove this debugging print
        print msg
        if msg.startswith(DELIM):
            self.prefix, msg = msg[1:].split(SPACE, 1)
            msg = msg.lstrip(SPACE)
        self.cmd, msg = msg.split(SPACE, 1)
        if self.cmd in replycodes:
            self.cmd = replycodes[self.cmd]
        while (len(msg) > 0):
            msg = msg.lstrip(SPACE)
            if msg.startswith(DELIM):
                self.params.append(msg[1:])
                break
            p, msg = msg.split(SPACE, 1)
            self.params.append(p)

    def encode(self):
        msg = ''
        if (len(self.prefix) > 0):
            msg += DELIM + self.prefix + SPACE
        msg += self.cmd
        for p in self.params:
            msg += SPACE
            if SPACE in p:
                msg += DELIM + p
                break
            else:
                msg += p
        return msg

    def __repr__(self):
        return self.encode()

    def __str__(self):
        return self.encode()
