import gevent
from gevent.queue import Queue
from lib.publisher import Publisher
from lib.irc import Msg

class Client(object):

    def __init__(self, irc, config, stdio):
        self.irc = irc
        self.stdio = stdio
        self.config = config
        self.nick = config['nick']
        self.servername = None
        self.motd = None
        self.channels = {}
        self.messagers = {}
        self.sending = Queue()
        self.receiving = Queue()
        self.publisher = Publisher()
        self.publisher.publish(self.sending)
        self.publisher.subscribe(self.irc.sender, self.sending)
        self.publisher.publish(self.irc.receiver)
        self.publisher.subscribe(self.receiving, self.irc.receiver)
        self.instance = gevent.spawn(self._event_loop)
        self._backdoor = Queue()
        self.publisher.publish(self.stdio.input)
        self.publisher.subscribe(self._backdoor, self.stdio.input)
        self.backdoor = gevent.spawn(self._back_door)

    @property
    def connected(self):
        return self.irc.connected

    def _event_loop(self):
        while True:
            if self.irc.wait_for_connection(self.config['timeout']):
                self.sending.put(Msg(cmd='NICK', params=[self.nick]))
                self.sending.put(Msg(cmd='USER', params=[self.nick, '8', '*', self.nick]))
                for msg in self.receiving:
                    if not self.irc.connected:
                        break
                    func = getattr(self, msg.cmd, self.unknown)
                    func(msg)

# TODO: Figure out why this doesn't work
# TODO: Add cleanup stuff

    def finish(self, dieing):
        if self.config['autoretry']:
            self.stdio.output.put(self.irc.name + ' rejoining...')
            gevent.spawn(self.irc.connect)
        else:
            self.stdio.output.put(self.irc.name + ' shutting down...')
            gevent.spawn(self.backdoor.kill)
            gevent.spawn(self.instance.kill)

    def _back_door(self):
        for line in self._backdoor:
            if line.startswith(self.irc.name):
                line = line[len(self.irc.name):].lstrip()
                exec(line)

    def RPL_WELCOME(self, msg):
        self.nick = msg.params[0]
        self.servername = msg.prefix
        self.sending.put(Msg(cmd='JOIN', params=[','.join(self.config['channels'])]))

    def RPL_MOTDSTART(self, msg):
        self.motd = []

    def RPL_MOTD(self, msg):
        self.motd.append(msg.params[-1])

    def RPL_ENDOFMOTD(self, msg):
        self.motd = "\n".join(self.motd)

    def RPL_TOPIC(self, msg):
        self.channels[msg.params[1]].topic = msg.params[2]

    def RPL_NAMREPLY(self, msg):
        channel = msg.params[2]
        chantype = msg.params[1]
        users = [User(self, msg, channel, name) for name in msg.params[3].split(' ')]
        self.channels[channel].chantype = chantype
        for user in users:
            self.channels[channel].users[user.nick] = user

    def ERR_NICKNAMEINUSE(self, msg):
        self.nick += '_'
        self.sending.put(Msg(cmd='NICK', params=[self.nick]))
        self.stdio.output.put('Changing nick to ' + self.nick)

    def ERROR(self, msg):
        if self.nick == msg.nick:
            self.irc.disconnect()
            self.finish(gevent.current)

    def join(self, channel):
        self.sending.put(Msg(cmd='JOIN', params=[channel]))

    def JOIN(self, msg):
        channel = msg.params[0]
        if self.nick == msg.nick:
            self.channels[channel] = Channel(self, channel)
        else:
            self.channels[channel].JOIN(msg)

    def notice(self, target, text):
        self.sending.put(Msg(cmd='NOTICE', params=[target, text]))

    def NOTICE(self, msg):
        target = msg.params[0]
        if self.nick == target:
            self.messagers[msg.nick] = (User(self, msg, target), msg.params[1])
        elif target in self.channels:
            self.channels[target].NOTICE(msg)

    def part(self, channel):
        self.sending.put(Msg(cmd='PART', params=[channel]))

    def PART(self, msg):
        if self.nick == msg.nick:
            del self.channels[msg.params[0]]
        else:
            for channel in msg.params[0].split(','):
                self.channels[channel].PART(msg)

    def ping(self):
        self.sending.put(Msg(cmd='PING', params=[self.servername]))

    def PING(self, msg):
        msg.cmd = 'PONG'
        self.sending.put(msg)

    def privmsg(self, target, text):
        self.sending.put(Msg(cmd='PRIVMSG', params=[target, text]))

    def PRIVMSG(self, msg):
        target = msg.params[0]
        if self.nick == target:
            self.messagers[msg.nick] = (User(self, msg, target), msg.params[1])
        elif target in self.channels:
            self.channels[target].PRIVMSG(msg)

    def quit(self):
        self.sending.put(Msg(cmd='QUIT', params=['Goodbye']))
        dieing = gevent.spawn_later(1, self.irc.disconnect)
        dieing.link(self.finish)

    def QUIT(self, msg):
        if self.nick == msg.nick:
            pass
        for channel in self.channels:
            self.channels[channel].QUIT(msg)

    def unknown(self, msg):
        if msg.cmd.isdigit():
            self.stdio.output.put("Unknown call: " + msg.cmd)


class User(object):

    def __init__(self, client, msg, channel, nick=None):
        self.client = client
        self.nick = nick if nick is not None else msg.nick
        self.user = msg.user
        self.host = msg.host
        self.voiced = False
        self.chanop = False
        if self.nick.startswith('+'):
            self.voiced = channel
            self.nick = self.nick[1:]
        if self.nick.startswith('@'):
            self.chanop = channel
            self.nick = self.nick[1:]

    def send(self, text):
        self.client.sending.put(Msg(cmd='PRIVMSG', params=[self.nick, text]))

    def notice(self, text):
        self.client.sending.put(Msg(cmd='NOTICE', params=[self.nick, text]))

class Channel(object):

    def __init__(self, client, name, topic='', chantype=''):
        self.client = client
        self.name = name
        self.topic = topic
        self.chantype = chantype
        self.users = {}
        self.privmsgs = []
        self.notices = []

    def JOIN(self, msg):
        user = User(self, msg, self.name)
        self.users[user.nick] = user

    def PART(self, msg):
        if msg.nick in self.users:
            del self.users[msg.nick]

    def privmsg(self, text):
        self.client.sending.put(Msg(cmd='PRIVMSG', params=[self.name, text]))

    def PRIVMSG(self, msg):
        pm = (self.users[msg.nick], msg.params[1])
        self.privmsgs.append(pm)
# TODO: Needs to be... pluginized! :D
        if self.client.nick in msg.params[1]:
            self.privmsg("G'day, {0}".format(msg.nick))

    def notice(self, text):
        self.client.sending.put(Msg(cmd='NOTICE', params=[self.name, text]))

    def NOTICE(self, msg):
        nt = (self.users[msg.nick], msg.params[1])
        self.privmsgs.append(nt)

    def QUIT(self, msg):
        if msg.nick in self.users:
            del self.users[msg.nick]
