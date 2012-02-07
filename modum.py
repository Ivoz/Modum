import os
from lib.irc import Irc
from lib.config import Config
from lib.stdio import StdIO
from lib.publisher import Publisher

plugin_paths = ['lib/plugins', 'plugins']


class Modum(object):
    """ Modum, the Super Duper IRC bot """

    def __init__(self, config_path='config.json', plugins=None):
        self.root_path = os.path.abspath('')
        self.config_path = config_path
        self.conf = Config(os.path.join(self.root_path, config_path))
        self.plugin_paths = plugins if plugins is not None else plugin_paths
        self.ircs = {}
        self.stdio = StdIO()
        self.stdio.output.put("Bootin' this bitch up...")
        self.publisher = Publisher()
        for name in self.conf.servers.keys():
            irc = Irc(self.conf.servers[name], name)
            self.ircs[name] = irc

    def run(self):
        """Main method to start the bot up"""
        from lib.irc import Msg
        self.publisher.publish(self.stdio.input, Msg)
        for irc in self.ircs.values():
            err = irc.connect()
            if err != True:
                self.stdio.put("Error connecting to {0}: {1}".format(irc.name, err))
                continue
            self.publisher.publish(irc.output, str)
            # Subscribe stdout to Irc's output
            #self.publisher.subscribe(self.stdio.output, irc.output)
            # Subscribe the Irc input to stdin
            #self.publisher.subscribe(irc.input, self.stdio.input)
# TODO: Temporary hack to see the bot's commands as well
            #irc.publisher.subscribe(self.stdio.output, irc.input)
        self.publisher.join_loop()

    def stop(self):
        for irc in self.ircs.values():
            irc.disconnect()
        self.stdio.stop()


if __name__ == "__main__":
    ze_bot = Modum('config.json')
    ze_bot.run()
