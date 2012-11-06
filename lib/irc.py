import gevent
import re
import sys
from gevent.queue import Queue
from gevent.event import Event
from lib.connection import Connection
from lib.replycodes import numerics
if sys.version > '3':
    basestring = str


RE_CTCP = '\001([^\001 ]+)(?: ((?<= )[^\001]*))?\001'
M_QUOTE = '\020'
# Order important
CTCP_QUOTES = [
        (M_QUOTE, M_QUOTE * 2),
        ('\000', M_QUOTE + '0'),
        ('\n', M_QUOTE + 'n'),
        ('\r', M_QUOTE + 'r'),
        ]


def ctcp_quote(msg):
    for esc, quote in CTCP_QUOTES:
        msg = msg.replace(esc, quote)
    return msg


def ctcp_dequote(msg):
    for esc, quote in CTCP_QUOTES[::-1]:
        msg = msg.replace(quote, esc)
    return msg


class Irc(object):
    """Handles a client connection to the IRC protocol"""

    def __init__(self, server, publisher, flood_prevention=1):
        self.server = server
        self.publisher = publisher
        self.flood_prevention = flood_prevention
        self._conn = Connection(server['host'], server['port'],
                    server['ssl'], server['timeout'])  # Internal connection
        # Timer to prevent flooding
        self.timer = Event()
        self.timer.set()
        # The canonical channels of IRC to subscribe / publish
        # Receives input to send to irc server
        self.sender = Queue()
        # Receives output to publish
        self.receiver = Queue()
        # Suscribe my output to receive data from connection
        self.publisher.subscribe(self.receiver,
                self._conn.receiver, Msg.from_msg)
        # Subscribe connection to send data from my input
        self.publisher.subscribe(self._conn.sender,
                self.sender, self._prevent_flood)

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

    def kill(self):
        """Completely terminate the irc connection"""
        self.publisher.unsubscribe(self.receiver, self._conn.receiver)
        self.publisher.unsubscribe(self._conn.sender, self.sender)
        self._conn.kill()

    def _prevent_flood(self, msg):
        """Used to prevent sending messages extremely quickly"""
        if self.flood_prevention > 0 and msg.cmd != 'PONG':
            self.timer.wait()
            self.timer.clear()
            gevent.spawn_later(self.flood_prevention, self.timer.set)
        return str(msg)


class Msg(object):
    """ Represents an IRC message to be sent or decoded """

    def __init__(self, cmd='', params=None, prefix='', ctcp=None, msg=None):
        """Params should be a string or list of strings"""
        self.cmd = cmd
        self.cmdnumber = None
        params = params if params is not None else []
        params = [params] if isinstance(params, basestring) else params
        self.params = [x for x in params if len(x) > 0]
        self.prefix = prefix
        self.ctcp = ctcp
        self.server = False
        self.nick = prefix
        self.user = None
        self.host = None
        if msg is not None:
            self.decode(msg)

    @classmethod
    def from_msg(cls, message):
        """Conveinance method"""
        return cls(msg=message)

    def decode(self, msg):
        """Store params of IRC msg string into this object"""
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
            trailing = ctcp_dequote(trailing)
            m = re.search(RE_CTCP, trailing)
            if m is not None:
                self.ctcp = m.groups()
                trailing = re.sub(RE_CTCP, '', trailing)
            if len(trailing) > 0:
                self.params.append(trailing)

    def encode(self):
        """Encode current Msg object into an IRC message string"""
        msg = ''
        if len(self.prefix) > 0:
            msg += ':' + self.prefix + ' '
        msg += self.cmd
        params = self.params[:]
        if self.ctcp is not None:
            ctcp = [s for s in self.ctcp if s is not None]
            ctcp = '\001' + ' '.join(ctcp) + '\001'
            params.append(ctcp)
        if len(params) == 0:
            return msg
        if len(params) > 1:
            msg += ' ' + ' '.join(params[:-1])
        msg += ' :' + ctcp_quote(params[-1])
        return msg

    def __str__(self):
        return self.encode()
