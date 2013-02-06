from plugin import *


def Moderation(Plugin):

    def setup(self, settings, botSettings):
        self.op = {}
        self.voice = {}

    def ban(self, channel, nick='*', user='*', host='*', unban=False):
        if not self.op.get(channel, False):
            return
        usermask = '%s!%s@%s' % (nick, user, host)
        mode = '-b' if unban else '+b'
        self.chan_mode(channel, mode, usermask)

    def chan_mode(self, channel, flags, args=None):
        if not self.op.get(channel, False):
            return
        arg = [channel, flags]
        if args is not None:
            arg.append(args)
        self._send(Msg('MODE', arg))

    def kick(self, channel, target, text=''):
        if not self.op.get(channel, False):
            return
        self._send(Msg('KICK', [channel, target, text]))

    def op(self, channel, nick, deop=False):
        if not self.op.get(channel, False):
            return
        mode = '-o' if deop else '+o'
        self.chan_mode(channel, mode, nick)

    def topic(self, channel, topic):
        if not self.op.get(channel, False):
            return
        self._send(Msg('TOPIC', [channel, topic]))

    def on_namreply(self, msg):
        nicks = msg.params[-1].split()
        me = [n for n in nicks if n.find(self.client.nick) >= 0]
        if len(me) != 1:
            return
        if me[0][0] == '@':
            self.op[msg.params[-2]] = True
        if me[0][0] == '+':
            self.voice[msg.params[-2]] = True
