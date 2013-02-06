from lib.irc import Msg


class Server(object):

    def __init__(self, client):
        self.client = client
        self.channels = []
        self.connecting = False

    def on_connect(self):
        nick = self.client.nick
        self.nick(nick)
        self._send(Msg('USER', [nick, '8', '*', nick]))
        self.connecting = True

    def on_err_nicknameinuse(self, msg):
        if self.connecting:
            self.client.nick += '_'
            self.nick(self.client.nick)

    def on_rpl_welcome(self, msg):
        channels = self.client.options['channels']
        self.join(channels)
        self.connecting = False

    def on_ping(self, msg):
        msg.cmd = 'PONG'
        self._send(msg)

    def on_nick(self, msg):
        if self.client.nick == msg.nick:
            self.client.nick = msg.params[0]

    def on_ctcp_ping(self, msg):
        self.ctcp_reply('PING', msg.nick, msg.ctcp[1])

    def on_ctcp_version(self, msg):
        from lib.bot import __version__ as version
        self.ctcp_reply('VERSION', msg.nick, version)


class Room(Server):

    def __init__(self, client):
        super(Channel, self).__init__(client)


class Channel(Room):

    def __init__(self, client):
        super(Channel, self).__init__(client)
        self.users = {}
        self.op = False
        self.voice = False


class PrivChat(Room):

    def __init__(self, client, partner):
        super(PrivChat, self).__init__(client)
        self.partner = partner
