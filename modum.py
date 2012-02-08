import os
import gevent
from lib.irc import Irc
from lib.config import Config
from lib.stdio import StdIO
from lib.publisher import Publisher
from lib.client import Client

plugin_paths = ['lib/plugins', 'plugins']


class Modum(object):
    """ Modum, the Super Duper IRC bot """

    def __init__(self, config_path='config.json', plugins=None):
        self.root_path = os.path.abspath('')
        self.config_path = config_path
        self.conf = Config(os.path.join(self.root_path, config_path))
        self.plugin_paths = plugins if plugins is not None else plugin_paths
        self.connections = {}
        self.stdio = StdIO()
        self.stdio.output.put("Bootin' this bitch up...")
        self.publisher = Publisher()
        for name in self.conf.servers.keys():
            conf = self.conf.servers[name]
            irc = Irc(conf, name, self.publisher)
            client = Client(irc, conf, self.stdio)
            self.connections[name] = (irc, client)

    def run(self):
        """Main method to start the bot up"""
        clients = []
        for (irc, client) in self.connections.values():
            err = irc.connect()
            if err != True:
                self.stdio.put("Error connecting to {0}: {1}".format(irc.name, err))
                name = irc.name
                del self.connections[name]
                continue
            clients.append(client.instance)
# TODO: Temporary method of seeing all commands on stdout
# TODO: Work why the fuck this grinds everything to a half
            #self.publisher.subscribe(self.stdio.output, irc.receiver, str)
            #self.publisher.subscribe(self.stdio.output, irc.sender, str)
        gevent.joinall(clients)
        self.stop()

    def stop(self):
        for irc, _ in self.connections.values():
            irc.disconnect()
        self.stdio.stop()


if __name__ == "__main__":
    ze_bot = Modum('config.json')
    ze_bot.run()
