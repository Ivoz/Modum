import os, sys
import gevent
from lib.irc import Irc
from lib.config import Config
from lib.stdio import StdIO
from lib.publisher import Publisher
from lib.client import Client

class Modum(object):
    """ Modum, the Super Duper IRC bot """

    def __init__(self, config_path='config.json'):
        self.root_path = os.path.abspath('')
        self.config_path = config_path
        self.conf = Config(os.path.join(self.root_path, config_path))
        self.connections = {}
        self.stdio = StdIO()
        self.stdio.output.put("Bootin' this bitch up...")
        self.publisher = Publisher()
        for name, server in self.conf.servers.items():
            if not server['enabled']:
                continue
            irc = Irc(server, name, self.publisher)
            client = Client(irc, server, self.stdio)
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
# TODO: Work out why the fuck this grinds everything to a half
            self.publisher.subscribe(self.stdio.output, irc.receiver, str)
            self.publisher.subscribe(self.stdio.output, irc.sender, str)
        gevent.joinall(clients)
        self.stop()

    def stop(self):
        for irc, _ in self.connections.values():
            irc.disconnect()
        self.stdio.stop()
        self.publisher.kill_loop()
        sys.exit()


if __name__ == "__main__":
    ze_bot = Modum('config.json')
    ze_bot.run()
