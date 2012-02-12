import os
from lib.irc import Irc
from lib.config import Config
from lib.stdio import StdIO
from lib.publisher import Publisher
from lib.client import Client


class Modum(object):
    """Modum, the Super Duper IRC bot"""

    def __init__(self, config_path='config.json'):
        self.root_path = os.path.abspath('')
        self.config_path = config_path
        self.conf = Config(os.path.join(self.root_path, config_path))
        self.conf.load()
        self.clients = {}
        self.stdio = StdIO()
        self.publisher = Publisher()
        for name, client in self.conf.clients.items():
            server = self.conf.servers[client['server']]
            irc = Irc(server, client['server'],
                self.publisher)
            self.clients[name] = Client(irc, client, self.stdio)
# TODO: Temporary method of seeing all commands on stdout
            self.publisher.subscribe(self.stdio.output,
                irc.receiver, str)
            self.publisher.subscribe(self.stdio.output,
                irc.sender, str)

    def run(self):
        """Main method to start modum up"""
        self.stdio.output.put("Bootin' this bitch up...")
        instances = []
        for client in self.clients.values():
            client.start()
            instances.append(client.instance)
        import gevent
        gevent.joinall(instances)
