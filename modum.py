import os
from lib.irc import Irc
from lib.config import Config
from lib.stdio import StdIO
from gevent.queue import Queue

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
        dummy = Queue()
        for name in self.ircs:
            self.ircs[name].connect()
            self.ircs[name].add_receiver(self.stdio.oQ)
            self.ircs[name].add_sender(self.stdio.iQ)
            self.ircs[name].add_receiver(dummy)
        for line in dummy:
            pass

    def stop(self):
        for irc in self.ircs.values():
            irc.disconnect()
        self.stdio.stop()


if __name__ == "__main__":
    ze_bot = Modum('config.json')
    ze_bot.run()
