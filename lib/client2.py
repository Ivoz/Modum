from lib.irc import Irc, Msg


class Client(object):

    def __init__(self, nick, servers, publisher):
        self.publisher = publisher
        if len(servers) < 1:
            raise Exception('No servers specified')
        self.ircs = []
        for name, server in servers.items():
            self.ircs[name] = Irc(server['details'], publisher)
            self.ircs[name]
            self.ircs[name].connect()


class Channel(object):

    def __init__(self, name):
        self.name = name


class User(object):

    def __init__(self, nick, user='', host=''):
        self.nick = nick
        self.user = user
        self.host = host

    @classmethod
    def from_msg(cls, message):
        return cls(message.nick, message.user, message.host)

