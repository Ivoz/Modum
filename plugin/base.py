from plugin import *
from lib.irc import Msg
from plugin.owner import owner


class Base(Plugin):
    """Implements basic functionality an IRC bot needs."""

    def on_connect(self):
        nick = self.client.nick
        self.nick(self.client.nick)
        self._send(Msg('USER', [nick, '8', '*', nick]))
        self.connecting = True

    def on_ping(self, msg):
        msg.cmd = 'PONG'
        self._send(msg)

    def on_nick(self, msg):
        if self.client.nick == msg.nick:
            self.client.nick = msg.params[0]

    def on_err_nicknameinuse(self, msg):
        if self.connecting:
            self.client.nick += '_'
            self.nick(self.client.nick)

    def on_rpl_welcome(self, msg):
        channels = self.client.options['channels']
        self.join(channels)
        self.connecting = False

    def on_ctcp_ping(self, msg):
        self.ctcp_reply('PING', msg.nick, msg.ctcp[1])

    def on_ctcp_version(self, msg):
        from lib.bot import __version__ as version
        self.ctcp_reply('VERSION', msg.nick, version)

    @command
    def help(self, msg):
        """
        Provide help for commands.
        Usage: help [<command>]
        """
        cmd_list = [p.commands for p in self.client.plugins.values()]
        names = {}
        [names.update(cmds) for cmds in cmd_list]
        if 'Owner' in self.client.plugins:
            if not self.client.plugins['Owner'].validate(msg):
                [names.pop(k) for k, v in names.items()
                        if hasattr(v, '_owner')]
        if msg.params[-1] in names:
            doc = names[msg.params[-1]].__doc__
            if doc is None:
                doc = 'No help available'
            self.privmsg(msg.nick, msg.params[-1] + ': ' + doc.rstrip())
        else:
            cmds = sorted(names.keys())
            self.privmsg(msg.nick, 'available commands: ' + ', '.join(cmds))

    @owner
    @command
    def die(self, msg):
        """
        I will then expire.
        """
        self.privmsg(msg.nick, "Goodbye, cruel world...")
        self.quit("Cya, folks!")
        self.client.kill()
