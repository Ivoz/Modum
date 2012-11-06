from plugin import *
from lib.irc import Msg


class Base(Plugin):

    def on_connect(self):
        nick = self.client.nick
        self.nick(self.client.nick)
        self._send(Msg('USER', [nick, '8', '*', nick]))

    def on_ping(self, msg):
        msg.cmd = 'PONG'
        self._send(msg)

    def on_nick(self, msg):
        if self.client.nick == msg.nick:
            self.client.nick = msg.params[0]

    def on_rpl_welcome(self, msg):
        channels = self.client.config['channels']
        self.join(channels)

    def on_ctcp_version(self, msg):
        self.ctcp_reply('VERSION', msg.nick, 'Modum v0.1')

    @command
    def help(self, msg):
        """
        Provide help for commands.
        Usage: help [<command>]
        """
        cmd_list = [p.commands for p in self.client.plugins.values()]
        names = {}
        [names.update(cmds) for cmds in cmd_list]
        if msg.params[-1] in names:
            doc = names[msg.params[-1]].__doc__
            self.privmsg(msg.nick, msg.params[-1] + ': ' + doc)
        else:
            cmds = sorted(names.keys())
            self.privmsg(msg.nick, 'available commands: ' + ', '.join(cmds))
