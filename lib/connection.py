import gevent
from gevent import socket, queue
from gevent import ssl as SSL

CRLF = '\r\n'


class Connection(object):
    """ Manages a line-by-line TCP connection """

# TODO: Work out how timeouts need to work...
    def __init__(self, host, port, ssl=False, timeout=10):
        self._ibuffer = ''
        self._obuffer = ''
        self.iqueue = queue.Queue()
        self.oqueue = queue.Queue()
        self.host = host
        self.port = port
        self.ssl = ssl
        self.timeout = timeout
        self._sock = self._create_socket()
        self.connected = False
        self.jobs = []

    def _create_socket(self):
        s = socket.socket()
        #s.settimeout(self.timeout)
        return SSL.wrap_socket(s) if self.ssl else s

    def connect(self):
        if not self.connected:
            err = self._sock.connect_ex((self.host, self.port))
            if (err == 0):
                self.jobs = [gevent.spawn(l) for l in [self._send, self._receive]]
                self.connected = True

    def disconnect(self):
        if self.connected:
            try:
                gevent.joinall(self.jobs)
            finally:
                gevent.killall(self.jobs)
            # Disallow further receives
            self._sock.shutdown(0)
            self._sock.close()
            self.connected = False

    def _send(self):
        while True:
            line = self.oqueue.get()
            self._obuffer += line.encode('utf-8', errors='replace') + CRLF
            while self._obuffer:
                sent = self._sock.send(self._obuffer)
                self._obuffer = self._obuffer[sent:]

    def _receive(self):
        while True:
            data = self._sock.recv(2048)
            self._ibuffer += data
            while CRLF in self._ibuffer:
                line, self._ibuffer = self._ibuffer.split(CRLF, 1)
                self.iqueue.put(line)
