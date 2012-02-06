import os
import gevent
from lib.irc import Irc
from lib.config import Config
from lib.stdio import StdIO
from lib.publisher import Publisher

class Modum(object):
    """ Modum, the Super Duper IRC bot """

    def __init__(self, config_path):
        self.root_path = os.path.abspath('')
        self.config_path = config_path
        self.conf = Config(os.path.join(self.root_path, config_path))
        self.ircs = {}
        self.stdio = StdIO()
        self.stdio.output.put("Bootin' this bitch up...")
        self.publisher = Publisher()
        for name in self.conf.servers.keys():
            irc = Irc(self.conf.servers[name], name)
            self.ircs[name] = irc

    def run(self):
        """Main method to start the bot up"""
        self.publisher.publish(self.stdio.input)
        for irc in self.ircs.values():
            irc.connect()
            self.publisher.publish(irc.conn.input)
            self.publisher.subscribe(self.stdio.output, irc.conn.input)
            self.publisher.subscribe(irc.conn.output, self.stdio.input)
        gevent.joinall(self.publisher.publications.values())

    def stop(self):
        for irc in self.ircs.values():
            irc.disconnect()
        self.stdio.stop()


if __name__ == "__main__":
    ze_bot = Modum('config.json')
    ze_bot.run()
