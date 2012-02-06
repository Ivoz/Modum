import os
import gevent
from lib.irc import Irc
from lib.config import Config


class Modum(object):
    """ Modum, the Super Duper IRC bot """

    def __init__(self, config_path):
        self.root_path = os.path.abspath('')
        self.config_path = config_path
        self.conf = Config(os.path.join(self.root_path, config_path))
        self.ircs = {}
        self.bot = gevent.Greenlet(self._loop)
        for name in self.conf.servers.keys():
            irc = Irc(self.conf.servers[name], name)
            self.ircs[name] = irc

    def run(self):
        """Main method to start the bot up"""
        for irc in self.ircs.values():
            irc.connect()
        self.bot.start()
        self.bot.join()

    def _loop(self):
        """Main event loop"""
        while True:
            for irc in self.ircs.values():
                print irc.receive()


if __name__ == "__main__":
    ze_bot = Modum('config.json')
    ze_bot.run()
