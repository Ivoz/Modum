import gevent
from gevent import socket
from gevent.queue import Queue
from gevent import ssl as SSL

CRLF = '\r\n'


class Connection(object):
    """ Manages a line-by-line TCP connection """

# TODO: Work out how timeouts need to work...
    def __init__(self, host, port, ssl=False, timeout=10):
        self.receiver = Queue()
        self.sender = Queue()
        self.host = host
        self.port = port
        self.ssl = ssl
        self.timeout = timeout
        self.connected = False
        self._sock = self._create_socket()
        self._ibuffer = ''
        self._obuffer = ''
        self._send_loop = None
        self._recv_loop = None

    def _create_socket(self):
        s = socket.socket()
        #s.settimeout(self.timeout)
        return SSL.wrap_socket(s) if self.ssl else s

    def connect(self):
        if not self.connected:
            err = self._sock.connect_ex((self.host, self.port))
            if (err == 0):
                self._send_loop = gevent.spawn(self._send)
                self._recv_loop = gevent.spawn(self._receive)
                self.connected = True
            else:
                return err

    def disconnect(self):
        if self.connected:
            gevent.killall([self._send_loop, self._recv_loop])
            # Disallow further receives
            self._sock.shutdown(0)
            gevent.sleep(1)
            self._sock.close()
            self._ibuffer = ''
            self._obuffer = ''
            self.connected = False

    def _send(self):
        while True:
            line = self.sender.get()
            self._obuffer += line.encode('utf_8', errors='replace') + CRLF
            while self._obuffer:
                sent = self._sock.send(self._obuffer)
                self._obuffer = self._obuffer[sent:]

    def _receive(self):
        while True:
            data = self._sock.recv(4096)
            self._ibuffer += data
            while CRLF in self._ibuffer:
                line, self._ibuffer = self._ibuffer.split(CRLF, 1)
                self.receiver.put(line)
