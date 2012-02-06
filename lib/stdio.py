import sys
import os
import fcntl
import gevent
from gevent import socket
from gevent.queue import Queue


class StdIO(object):
    """Handles input and output from stdin/stdout."""

    def __init__(self):
        fcntl.fcntl(sys.stdin, fcntl.F_SETFL, os.O_NONBLOCK)
        fcntl.fcntl(sys.stdout, fcntl.F_SETFL, os.O_NONBLOCK)
        self.iQ = Queue()
        self.oQ = Queue()
        self._i = gevent.spawn(self._input)
        self._o = gevent.spawn(self._output)

    def _input(self):
        buff = ''
        while True:
            socket.wait_read(sys.stdin.fileno())
            buff += sys.stdin.read()
            while '\n' in buff:
                line, buff = buff.split('\n', 1)
                self.iQ.put(line)

    def _output(self):
        try:
            for line in self.oQ:
                sys.stdout.write(line)
        finally:
            sys.stdout.flush()

    def stop(self):
        self._o.kill()
        self._i.kill()
