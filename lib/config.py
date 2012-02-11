import json


class Config(object):

    def __init__(self, config_path):
        self.config_path = config_path
        self._settings = {}
        self.load(self.config_path)

    def load(self, config_path):
        self._settings = json.load(open(config_path, 'r'),
                encoding="utf8")

    def reload(self):
        self.load(self.config_path)

    def save(self, config_path=None):
        if config_path is None:
            config_path = self.config_path
        json.dump(self._settings, open(config_path, 'w'),
                sort_keys=True, indent=4)
