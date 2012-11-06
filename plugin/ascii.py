from plugin import *
import os


class Ascii(Plugin):

    def setup(self):
        self.sailors = os.listdir(self.data_dir)

    @command
    def sailor(self, msg):
        """
        Print ascii of a Sailor Scout.
        Usage: sailor <name>
        """
        print 'sailor called'
        scout = 'sailor_' + msg.params[-1].lower() + '.ascii'
        if scout in self.sailors:
            ascii = open(self.data_dir + scout)
            for line in ascii.readlines():
                self.privmsg(msg.nick, line.replace('\n', ''))
