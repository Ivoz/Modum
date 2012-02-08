import gevent
from gevent.event import Event
from gevent.queue import Queue
from gevent import socket
from gevent import ssl as SSL
from gevent.timeout import Timeout

CRLF = '\r\n'


class Connection(object):
    """ Manages a line-by-line TCP connection """

    def __init__(self, host, port, ssl=False, timeout=10):
        self.receiver = Queue()
        self.sender = Queue()
        self.host = host
        self.port = port
        self.ssl = ssl
        self.timeout = timeout
        self.connection = Event()
        self._sock = self._create_socket()
        self._ibuffer = ''
        self._obuffer = ''
        self._send_loop = None
        self._recv_loop = None

    def _create_socket(self):
        s = socket.socket()
        return SSL.wrap_socket(s) if self.ssl else s

    @property
    def connected(self):
        return self.connection.is_set()

    def connect(self):
        if not self.connected:
            try:
                self._sock.connect((self.host, self.port))
            except socket.error as (errno, strerror):
                return strerror
            else:
                self._send_loop = gevent.spawn(self._send)
                self._recv_loop = gevent.spawn(self._receive)
                self.connection.set()
                return True

    def disconnect(self):
        if self.connected:
            gevent.killall([self._send_loop, self._recv_loop])
            # Disallow further receives
            self._sock.shutdown(0)
            gevent.sleep(1)
            self._sock.close()
            self._ibuffer = ''
            self._obuffer = ''
            self.connection.clear()

    def _send(self):
        while True:
            line = self.sender.get()
            print line
            self._obuffer += line.encode('utf_8', errors='replace') + CRLF
            while self._obuffer:
                try:
                    sent = gevent.with_timeout(self.timeout,
                            self._sock.send,self._obuffer)
                except Timeout:
                    self.disconnect()
                else:
                    self._obuffer = self._obuffer[sent:]

    def _receive(self):
        while True:
            data = self._sock.recv(4096)
            self._ibuffer += data
            while CRLF in self._ibuffer:
                line, self._ibuffer = self._ibuffer.split(CRLF, 1)
                print line
                self.receiver.put(line)
