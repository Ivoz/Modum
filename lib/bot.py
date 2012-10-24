import os
from lib.config import Config
from lib.client import Client


class Modum(object):
    """Modum, the raurcous IRC bot"""

    def __init__(self, config_file='data/config.json'):
        config_path = os.path.join(os.path.abspath(''), config_file)
        self.conf = Config(config_path)
        self.clients = {}
        for name, client in self.conf.clients.items():
            self.clients[name] = Client(name, self.conf)
# TODO: Temporary method of seeing all commands on stdout

    def run(self):
        """Main method to start modum up"""
        print("Bootin' this bitch up...")
        instances = []
        for client in self.clients.values():
            instances.append(client.start())
        [instance.join() for instance in instances]
