import os, sys
import gevent
from gevent import queue
from lib.irc import Irc
from lib.config import Config


class Modum(object):
    """ Modum, the Super Duper IRC bot """

    def __init__(self, config_path):
        self.root_path = os.path.abspath('')
        self.config_path = config_path
        self.conf = Config(os.path.join(self.root_path, config_path))
        self.ircs = {}
        self.bots = []
        for name in self.conf.servers.keys():
            irc = Irc(self.conf.servers[name], name)
            self.ircs[name] = irc

    def run(self):
        """Main method to start the bot up"""
        i = {}
        for name in self.ircs:
            self.ircs[name].connect()
            i[name] = 0
        q = self._loop()
        while True:
            line = q.get()
            i[line['irc']] += 1
            sys.stdout.write(line['line'] + '\n')
            sys.stdout.flush()
            for name in self.ircs:
                if (i[name] == 4):
                    self.ircs[name].register()


    def stop(self):
        gevent.joinall(self.bots)
        for irc in self.ircs.values():
            irc.disconnect()

    def _loop(self):
        """Main event loop"""
        q = queue.Queue()
        for n in self.ircs:
            def _aggregate():
                while True:
                    q.put({'irc': n, 'line': self.ircs[n].receive()})
            self.bots.append(gevent.spawn(_aggregate))
        return q



if __name__ == "__main__":
    ze_bot = Modum('config.json')
    ze_bot.run()
