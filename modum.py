import os
from lib.irc import Irc
from lib.config import Config
from lib.stdio import StdIO
from lib.publisher import Publisher

plugin_paths = ['lib/plugins', 'plugins']


class Modum(object):
    """ Modum, the Super Duper IRC bot """

    def __init__(self, config_path='config.json', plugins=plugin_paths):
        self.root_path = os.path.abspath('')
        self.config_path = config_path
        self.conf = Config(os.path.join(self.root_path, config_path))
        self.ircs = {}
        self.stdio = StdIO()
        self.stdio.output.put("Bootin' this bitch up...")
        self.publisher = Publisher()
        for name in self.conf.servers.keys():
            irc = Irc(self.conf.servers[name], name)
            self.ircs[name] = irc

    def run(self):
        """Main method to start the bot up"""
        self.publisher.publish(self.stdio.input)
        for irc in self.ircs.values():
            irc.connect()
            self.publisher.publish(irc.output)
            # Subscribe stdout to Irc's output
            self.publisher.subscribe(self.stdio.output, irc.output)
            # Subscribe the Irc input to stdin
            self.publisher.subscribe(irc.input, self.stdio.input)
# TODO: Temporary hack to see the bot's commands as well
            irc.publisher.subscribe(self.stdio.output, irc.input)
        import gevent; gevent.sleep(30000)

    # Load a plugin
    def load(self, paths):
        def load_plugin():
            pass

        for path in paths:
            pass


    def stop(self):
        for irc in self.ircs.values():
            irc.disconnect()
        self.stdio.stop()


if __name__ == "__main__":
    ze_bot = Modum('config.json')
    ze_bot.run()
