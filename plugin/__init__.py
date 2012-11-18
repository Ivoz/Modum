import os
import sys
from functools import partial, wraps
from lib.irc import Msg
if sys.version > '3':
    basestring = str

__all__ = ['command', 'Plugin']


def command(func=None, name=None):
    """Make a plugin method a command actionable by a user"""
    if func is None:
        return partial(command, name=name)

    if name is None:
        name = func.__name__

    @wraps(func)
    def wrapper(self, msg):
        return func(self, msg)
    wrapper._command = name
    return wrapper


class Plugin(object):
    """
    Underlying class from which plugins can extend.
    Implements a number of helpful irc-related wrapper
    methods, implements command functionality.
    """

    def __init__(self, client):
        self.client = client
        self._send = self.client.sending.put
        data = self.client.config.data_dir
        name = self.__class__.__name__.lower()
        self.data_dir = os.path.join(data, name) + os.path.sep
        self._load_commands()

    def _load_commands(self):
        members = [getattr(self, m) for m in dir(self)]
        commands = {}
        for member in members:
            if hasattr(member, '_command'):
                commands[member._command] = member
        self.commands = commands

    def action(self, target, text):
        self._send(Msg('PRIVMSG', target, ctcp=['ACTION', text]))

    def ctcp_reply(self, cmd, target, text):
        self._send(Msg('NOTICE', target, ctcp=[cmd, text]))

    def join(self, channel):
        if isinstance(channel, basestring):
            channel = [channel]
        self._send(Msg('JOIN', ','.join(channel)))

    def mode(self, flags):
        self._send(Msg('MODE', [self.client.nick, flags]))

    def notice(self, target, text):
        for line in text.split('\n'):
            self._send(Msg('NOTICE', [target, line]))

    def nick(self, nick):
        self._send(Msg('NICK', nick))

    def part(self, channel, text=None):
        if isinstance(channel, basestring):
            channel = [channel]
        self._send(Msg('PART', [','.join(channel), text]))

    def privmsg(self, target, text):
        for line in text.split('\n'):
            self._send(Msg('PRIVMSG', [target, line]))

    def quit(self, text):
        self._send(Msg('QUIT', text))

    def reply(self, msg, text):
        """Reply in correct channel or private query"""
        if msg.params[0] == self.client.nick:
            target = msg.nick
        else:
            target = msg.params[0]
        self.privmsg(target, text)

    def whois(self, nick):
        self._send(Msg('WHOIS', nick))

    def on_privmsg(self, msg):
        for name, command in self.commands.iteritems():
            if msg.params[-1][0] in self.client.options['prefixes']:
                if msg.params[-1][1:].startswith(name):
                    m = Msg.from_msg(str(msg))
                    m.params[-1] = m.params[-1][len(name) + 1:].lstrip(' ')
                    command(m)
