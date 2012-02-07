import gevent
from gevent.queue import Queue
from lib.connection import Connection
from lib.publisher import Publisher
#import replycodes

# Constants for IRC special chars
SPACE = ' '
NULL = '\0'
DELIM = ':'


class Irc(object):
    """ Handles the IRC protocol """

    def __init__(self, server, name):
        self.name = name
        self._nick = server['nick']
        self._channels = server['channels']
        self._conn = Connection(server['host'], server['port'],
                    server['ssl'], server['timeout'])
        # The canonical channels of IRC to subscribe / publish
        # Receives input to send
        self.input = Queue()
        # Receives output to publish
        self.output = Queue()
        self.publisher = Publisher([self._conn.receiver, self.input])

    @property
    def nick(self):
        return self._nick

    @nick.setter
    def nick(self, value):
        self.send(Msg(cmd='NICK', params=value))
# TODO: Check that nick is not taken
        self._nick = value

    @property
    def channels(self):
        return self._channels

    @property
    def connected(self):
        return self._conn.connected

    def connect(self):
        if self.connected:
            return True
        self._conn.connect()
        if self.connected:
            # Suscribe my output to receive data from connection
            self.publisher.subscribe(self.output, self._conn.receiver)
            # Subscribe connection to send data from my input
            self.publisher.subscribe(self._conn.sender, self.input)
            gevent.spawn_later(2, self._register)
        return self.connected

    def disconnect(self):
        if not self.connected:
            return False
        self._conn.disconnect()
        return self.connected

    def _register(self):
        self.nick = self._nick
        self.send(Msg(cmd='USER', params=[self.nick, '+i+s+w', '*', ':' + self.nick]))
        self.send(Msg(cmd='JOIN', params=','.join(self._channels)))

# TODO: Not totally sure about this interface yet.
    def send(self, msg):
        self.input.put(str(msg))


# TODO: allow for saving new params to the config, e.g nick changes
    #def save(config)


class Msg(object):
    """ Represents an IRC message to be sent or decoded """

    def __init__(self, prefix='', cmd='', params='', msg=None):
        self.prefix = prefix
        self.cmd = cmd
        self.params = [params] if (type(params) != list) else params
        if msg != None:
            self.decode(msg)

    def decode(self, msg):
        if msg.startswith(DELIM):
            self.prefix, msg = msg[1:].split(SPACE, 1)
            msg = msg.lstrip(SPACE)
        self.cmd, msg = msg.split(SPACE, 1)
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


class User(object):

    def __init__(self, userstring):
        self.prefix = ''
        self.name = ''
        self.host = ''
        self.server = ''
        self.real = ''
