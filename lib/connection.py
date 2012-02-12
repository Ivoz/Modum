import gevent
from gevent.event import Event
from gevent.queue import Queue
from gevent import socket
from gevent import ssl as SSL
from gevent.timeout import Timeout

CRLF = '\r\n'
ERR_TIMEOUT = 'Connection timed out'


class Connection(object):
    """ Manages a line-by-line TCP connection """

    def __init__(self, host, port, ssl=False, timeout=5, retries=False):
        self.host = host
        self.port = port
        self.ssl = ssl
        self.timeout = timeout
        self.retries = retries
        self._connection = Event()
        self._state = False
        self.receiver = Queue()
        self.sender = Queue()
        self._sock = self._create_socket()
        self._ibuffer = ''
        self._obuffer = ''
        self._send_loop = gevent.spawn(self._send)
        self._recv_loop = gevent.spawn(self._receive)

    def _create_socket(self):
        s = socket.socket()
        return SSL.wrap_socket(s) if self.ssl else s

    @property
    def connected(self):
        return self._connection.is_set()

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, value):
        self._state = value
        if value == True:
            self._connection.set()
        else:
            self._connection.clear()

    def connect(self):
        if not self.connected:
            try:
                gevent.with_timeout(self.timeout,
                        self._sock.connect, (self.host, self.port))
            except socket.error as (_, strerror):
                return strerror
            except Timeout:
                self.disconnect(ERR_TIMEOUT)
            else:
                self.state = True

    def disconnect(self, strerror=None):
        if not self.connected and strerror is None:
            return
        self.state = False
        print strerror
        if strerror is not None:
            # Not been told to disconnect
            self.state = strerror
            if self.retries:
                if isinstance(self.retries, int):
                    self.retries -= 1
                self.connect()
                return
        self._finalise()

    def kill(self):
        self._finalise()
        self._send_loop.kill()
        self._recv_loop.kill()

    def _finalise(self):
        """Finalise a disconnect"""
        self.state = False
        self._sock.shutdown(2)
        self._sock.close()
        self._ibuffer = ''
        self._obuffer = ''

    def _send(self):
        while self._connection.wait():
            line = self.sender.get()
            self._obuffer += line.encode('utf_8',
                    errors='replace') + CRLF
            while self._obuffer:
                try:
                    sent = gevent.with_timeout(self.timeout,
                            self._sock.send, self._obuffer)
                except Timeout:
                    self.disconnect(ERR_TIMEOUT)
                else:
                    self._obuffer = self._obuffer[sent:]

    def _receive(self):
        while self._connection.wait():
            data = self._sock.recv(4096)
            self._ibuffer += data
            while CRLF in self._ibuffer:
                line, self._ibuffer = self._ibuffer.split(CRLF, 1)
                self.receiver.put(line)
