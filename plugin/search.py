from plugin import *


class Search(Plugin):

    def setup(self, settings, botSettings):
        self.url = settings[url]
        print url
        print url

    @command
    def search(self, msg):
        pass


def get_results(url, query):
    pass
