import gevent
from gevent import socket, queue, ssl

CRLF  = '\r\n'

class Connection(object):
    """ Manages a line-by-line TCP connection """

#TODO: Work out how timeouts need to work...
    def __init__(self, host, port, ssl = False, timeout = 10):
        self._ibuffer = ''
        self._obuffer = ''
        self.iqueue = queue.Queue()
        self.oqueue = queue.Queue()
        self.host = host
        self.port = port
        self.ssl = ssl
        self.timeout = timeout
        self._sock = self._create_socket(ssl)
        self.connected = False

    def _create_socket(self, ssl):
        s = socket.socket()
        #s.settimeout(self.timeout)
        if (ssl):
            return ssl.wrap_socket(s)
        return s
    
    def connect(self):
        if not self.connected:
            self._sock.connect((self.host, self.port))
            jobs = [gevent.spawn(l) for l in [self._send, self._receive]]
            self.connected = True

    def disconnect(self):
        if self.connected:
            try:
                gevent.joinall(jobs)
            finally:
                gevent.killall(jobs)
            self._sock.close()
            self.connected = False

    def _send(self):
        while True:
            line = self.oqueue.get()
            self._obuffer += line.encode('utf-8', 'replace') + CRLF
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
