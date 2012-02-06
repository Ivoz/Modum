import collections
import json


class Config(collections.MutableMapping):

    def __init__(self, config_path):
        self._settings = {
            'servers' : {
                'Default' : {
                    'host'    : 'irc.oftc.net',
                    'port'    : 6667,
                    'ssl'     : False,
                    'timeout' : 10,
                    'nick'    : 'Modum',
                    'channels' : ['#bots']
                    }
                }
            }
        self.load(config_path)
        self.config_path = config_path

    def load(self, config_path):
        self._settings = json.load(open(config_path, 'r'),
                encoding="ASCII")

    def reload(self):
        self.load(self.config_path)

    def save(self, config_path=None):
        if not config_path:
            config_path = self.config_path
        json.dump(self._settings, open(config_path, 'w'),
                sort_keys=True, indent=4)

    def __getitem__(self, key):
        return self._settings.__getitem__(key)

    def __setitem__(self, key, value):
        self._settings.__setitem__(key, value)

    def __delitem__(self, key):
        self._settings.__delitem__(key)

    def __iter__(self):
        return self._settings.__iter__()

    def __len__(self):
        return self._settings.__len__()

    def __getattr__(self, name):
        return self._settings[name]
