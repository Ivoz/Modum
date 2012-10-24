import json


class Config(object):

    def __init__(self, config_path=None):
        self.config_path = config_path
        self.clients = None
        self.plugins = None
        self.servers = None
        if self.config_path is not None:
            self.load(self.config_path)

    def load(self, path=None):
        path = self.config_path if path is None else path
        settings = json.load(open(path, 'r'),
                encoding="utf8")
        self.clients = settings['clients']
        self.plugins = settings['plugins']
        self.servers = settings['servers']

    def reload(self):
        self.load(self.config_path)

    def save(self, config_path=None):
        if config_path is None:
            config_path = self.config_path
        settings = {
                'clients': self.clients,
                'plugins': self.plugins,
                'servers': self.servers
                }
        json.dump(settings, open(config_path, 'w'),
                sort_keys=True, indent=2)
