from lib.irc import Irc, Msg

class Client(object):

    def __init__(self, irc, nick):
        self.irc = irc
        self.nick = nick
        self.channels = {}


    def _event_loop(self):
        while True:
            self.irc.wait_for_connection()
            while self.irc.connected:
                msg = self.irc.input.get()
                func = getattr(self, msg.cmd.tolower(), self.unknown)
                func(msg)

    @property
    def connected(self):
        return self.irc.connected

    def join(self, channel):
        self.channels[channel] = Channel(channel)

    def part(self, channel):
        del self.channels[channel]

    def unknown(self, msg):
        print "unknown", str(msg)


class User(Client):

    def __init__(self, irc, nick, channel):
        Client.__init__(self, irc, nick)
        self.join(channel)

    def send(self, message):
        pass


class Channel(object):

    def __init__(self, name):
        self.name = name
        self.users = {}
