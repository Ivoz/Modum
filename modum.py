import os
import gevent
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
        self.bots = []
        self.stdio = StdIO()
        self.stdio.oQ.put("Bootin' this bitch up...")
        for name in self.conf.servers.keys():
            irc = Irc(self.conf.servers[name], name)
            self.ircs[name] = irc

    def run(self):
        """Main method to start the bot up"""
        for name in self.ircs:
            self.ircs[name].connect()
            self.ircs[name].addReceiver(self.stdio.oQ)
            self.ircs[name].addSender(self.stdio.iQ)

    def stop(self):
        gevent.joinall(self.bots)
        for irc in self.ircs.values():
            irc.disconnect()
        self.stdio.stop()


if __name__ == "__main__":
    ze_bot = Modum('config.json')
    ze_bot.run()
