import os
from lib.config import Config
from lib.client import Client


__version__ = '0.1-dev'


class Modum(object):
    """Modum, the raurcous IRC bot"""

    def __init__(self, args, filepath):
        file_dir = os.path.dirname(os.path.realpath(filepath))
        config_path = os.path.join(file_dir, args.config)
        data_path = os.path.join(file_dir, args.data)
        self.conf = Config(config_path, data_path)
        self.daemonized = args.daemon
        self.clients = {}
        for name, client in self.conf.clients.items():
            self.clients[name] = Client(name, self.conf)

    def run(self):
        """Main method to start modum up"""
        print("Bootin' this bitch up...")
        instances = []
        for client in self.clients.values():
            instances.append(client.start())
        [instance.join() for instance in instances]
