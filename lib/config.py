import json


class Config(object):

    def __init__(self, config_path):
        self.config_path = config_path
        self._settings = {}
        self.load(self.config_path)
        self.clients = None
        self.servers = None

    def load(self, path=None):
        path = self.config_path if path is None else path
        self._settings = json.load(open(path, 'r'),
                encoding="utf8")
        self.clients = self._settings['clients']
        self.servers = self._settings['servers']

    def reload(self):
        self.load(self.config_path)

    def save(self, config_path=None):
        if config_path is None:
            config_path = self.config_path
        json.dump(self._settings, open(config_path, 'w'),
                sort_keys=True, indent=4)
