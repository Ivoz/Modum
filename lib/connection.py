import gevent
from gevent.event import Event
from gevent.queue import Queue
from gevent import socket
from gevent import ssl as SSL
from gevent.timeout import Timeout

CRLF = '\r\n'  # Line separator
ERR_TIMEOUT = 'Connection timed out'  # Timeout error message


class Connection(object):
    """ Manages a line-by-line TCP connection """

    def __init__(self, host, port, ssl=False, timeout=5, retries=False):
        self.host = host
        self.port = port
        self.ssl = ssl
        self.timeout = timeout
        self.retries = retries  # Number of times to retry connecting
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
        """Boolean representation of connection state"""
        return self._connection.is_set()

    @property
    def state(self):
        """True if connected, otherwise can contain an error message"""
        return self._state

    @state.setter
    def state(self, value):
        self._state = value
        if value is True:
            self._connection.set()
        else:
            self._connection.clear()

    def connect(self):
        """Initiate a connection; will retry if enabled"""
        if not self.connected:
            try:
                gevent.with_timeout(self.timeout,
                        self._sock.connect, (self.host, self.port))
            except socket.error as e:
                return e.strerror
            except Timeout:
                self.disconnect(ERR_TIMEOUT)
            else:
                self.state = True

    def disconnect(self, strerror=None):
        """Disconnect current connection.

        If strerror is None, then disconnect immediately;
        otherwise try to reconnect.
        """

        if not self.connected and strerror is None:
            return
        self.state = False
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
        """Completely terminate this connection"""
        self.disconnect()
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
        """The sending loop to send messages over the connection.

        Can have a timeout to report that connection might have dropped.
        """
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
        """Receiving loop to listen for messages; converts them into
        separate lines.
        """
        while self._connection.wait():
            data = self._sock.recv(4096)
            self._ibuffer += data
            while CRLF in self._ibuffer:
                line, self._ibuffer = self._ibuffer.split(CRLF, 1)
                self.receiver.put(line)
