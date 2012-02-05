import os
import gevent
from lib.irc import Irc
from lib.config import Config


class Modum(object):
    """ Modum, the Super Duper IRC bot """

    def __init__(self, config_path):
#TODO: Change '/' to OS dependant directory-separator
        self.root_path = os.path.abspath('') + '/'
        self.config_path = config_path
        self.conf = Config(self.root_path + config_path)
        self.ircs = {}
        for name in self.conf.servers.keys():
            irc = Irc(self.conf.servers[name], name)
            self.ircs[name] = irc

    """ Main method to start the bot up """
    def run(self):
        for irc in self.ircs.values():
            irc.connect()
        self.bot = gevent.spawn(self._loop)
        self.bot.join()

    """ Main event loop """
    def _loop(self):
        while True:
            for irc in self.ircs.values():
                print irc.receive()


if __name__ == "__main__":
    ze_bot = Modum('config.json')
    ze_bot.run()
