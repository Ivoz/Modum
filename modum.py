import os
import gevent
from gevent.queue import Queue
from lib.irc import Irc
from lib.config import Config
from lib.stdio import StdIO

class Modum(object):
    """ Modum, the Super Duper IRC bot """

    def __init__(self, config_path):
        self.root_path = os.path.abspath('')
        self.config_path = config_path
        self.conf = Config(os.path.join(self.root_path, config_path))
        self.ircs = {}
        self.stdio = StdIO()
        self.stdio.oQ.put("Bootin' this bitch up...")
        for name in self.conf.servers.keys():
            irc = Irc(self.conf.servers[name], name)
            self.ircs[name] = irc

    def run(self):
        """Main method to start the bot up"""
        dups = {name : Queue() for name in self.ircs}
        loop = self.queue_dup(self.stdio.iQ, dups.values())
        for name in self.ircs:
            self.ircs[name].connect()
            self.ircs[name].add_receiver(self.stdio.oQ)
            self.ircs[name].add_sender(dups[name])
        loop.join()

    def queue_dup(self, q, dups):
        def _dup():
            for line in q:
                for dup in dups:
                    dup.put(line)
        return gevent.spawn(_dup)

    def stop(self):
        for irc in self.ircs.values():
            irc.disconnect()
        self.stdio.stop()


if __name__ == "__main__":
    ze_bot = Modum('config.json')
    ze_bot.run()
