import gevent
from gevent.queue import Queue
from lib.irc import Msg

class Client(object):

    def __init__(self, irc, config, stdio):
        self.irc = irc
        self.stdio = stdio
        self.config = config
        self.nick = config['nick']
        self.servername = None
        # None when not received, [] when processing, '' when received
        self.options = {}
        self.op = '@'
        self.voice = '+'
        self.motd = None
        self.channels = {}
        self.messagers = {}
        # Using these for now; if only this communicates with irc,
        # then there's no need for another publishing loop here
        self.sending = Queue()
        self.receiving = Queue()
        self.publisher = irc.publisher
        self.publisher.subscribe(self.irc.sender, self.sending)
        self.publisher.subscribe(self.receiving, self.irc.receiver)
        self.instance = gevent.spawn(self._event_loop)
        # Backdoor receiver to execute command line input
        self._backinput = Queue()
        self.publisher.subscribe(self._backinput, self.stdio.input)
        self._backdoor = gevent.spawn(self._back_door)

    def _event_loop(self):
        while True:
            if self.irc.wait_for_connection(self.config['timeout']):
                self.sending.put(Msg('NICK', self.nick))
                self.sending.put(Msg('USER',
                    [self.nick, '8', '*', self.nick]))
                for msg in self.receiving:
                    func = getattr(self, msg.cmd, self.unknown)
                    gevent.spawn(func, msg)
                self._finish()
# TODO: Add cleanup stuff

# TODO: Figure out why this doesn't work, possibly move to Irc?
    def _finish(self):
        self.irc.disconnect()
        if type(self.config['autoretry']) == int:
            self.stdio.output.put('{0} reconnecting in {1} \
                    seconds...'.format(self.irc.name, self.config['autoretry']))
            gevent.sleep(self.config['autoretry'])
            gevent.spawn(self.irc.connect)
        else:
            self.stdio.output.put(self.irc.name + ' shutting down...')
            self._backinput.put(StopIteration)
            gevent.spawn(self.instance.kill)

    def _back_door(self):
        for line in self._backinput:
            if line.startswith(self.irc.name):
                line = line[len(self.irc.name):].lstrip()
                gevent.spawn(self._do_exec, line)

    def _do_exec(self, code):
        exec code

    def quit(self):
        self.sending.put(Msg('QUIT','Goodbye'))

    def unknown(self, msg):
        """Fallback handler"""
        if msg.cmd.isdigit():
            self.stdio.output.put("Unknown call: " + msg.cmd)

    def RPL_WELCOME(self, msg):
        self.nick = msg.params[0]
        self.servername = msg.prefix
        self.sending.put(Msg('JOIN',
            ','.join(self.config['channels'])))

    def RPL_ISUPPORT(self, msg):
        opts = msg.params[1:-1]
        for option in opts:
            if '=' in option:
                key, value = option.split('=', 1)
            else:
                key = option
                value = True
            self.options[key] = value
            if key == 'PREFIX':
                try:
                    prefixes, chars = value[1:].split(')', 1)
                    for (pref, val) in zip(prefixes, chars):
                        if pref == 'o':
                            self.op = val
                        if pref == 'v':
                            self.voice = val
                except:
                    pass

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
        users = [User(self, channel, msg, name) for name in msg.params[3].split(' ')]
        self.channels[channel].chantype = chantype
        for user in users:
            self.channels[channel].users[user.nick] = user

    def ERR_NICKNAMEINUSE(self, msg):
        self.nick += '_'
        self.sending.put(Msg('NICK', self.nick))

    def ERROR(self, msg):
        print "Quit!!!!!!"
        self.receiving.put(StopIteration)

    def JOIN(self, msg):
        channel = msg.params[0]
        if self.nick == msg.nick:
            self.channels[channel] = Channel(self, channel)
        self.channels[channel].JOIN(msg)

# TODO: Complete this... a lot
    def MODE(self, msg):
        target = msg.params[0]
        if target in self.channels:
            self.channels[target].MODE(msg)

    def NICK(self, msg):
        old = msg.nick
        new = msg.params[0]
        if self.nick == old:
            self.nick = new
        for channel in filter(lambda x: old in x.users, self.channels.values()):
            channel.NICK(msg)

    def NOTICE(self, msg):
        target = msg.params[0]
        if self.nick == target:
# TODO: Debug why this is happening
            try:
                self.messagers[msg.nick] = msg
            except ValueError:
                print msg.nick, msg
        elif target in self.channels:
            self.channels[target].NOTICE(msg)

    def PART(self, msg):
        if self.nick == msg.nick:
            del self.channels[msg.params[0]]
        else:
            for channel in msg.params[0].split(','):
                self.channels[channel].PART(msg)

    def PING(self, msg):
        msg.cmd = 'PONG'
        self.sending.put(msg)

    def PRIVMSG(self, msg):
        target = msg.params[0]
        if self.nick == target:
            self.messagers[msg.nick] = msg
# TODO: Cheap hack to exec code. Replace with plugin ASAP.
            if msg.params[1].startswith(self.nick + ': '):
                gevent.spawn(self._do_exec,
                        msg.params[1][len(self.nick + ': '):])
        elif target in self.channels:
            self.channels[target].PRIVMSG(msg)

    def QUIT(self, msg):
        for channel in self.channels.values():
            self.channels.QUIT(msg)


class User(object):

    special = '[]\`_^{|}'

    def __init__(self, client, channel, msg, name=None):
        self.client = client
        self.channel = channel
        self.nick = name if name is not None else msg.nick
        self.oldnicks = []
        self.user = msg.user if name is None else ''
        self.host = msg.host if name is None else ''
        self.prefix = ''
        if self.nick[0] not in self.special and not self.nick[0].isalpha():
            self.prefix, self.nick = self.nick[0], self.nick[1:]
        self.voiced = True if self.prefix == self.client.voice else False
        self.chanop = True if self.prefix == self.client.op else False

    def NICK(self, msg):
        if self.nick == msg.nick:
            self.oldnicks.append(self.nick)
            self.nick = msg.params[0]
            self.user = msg.user
            self.host = msg.host

class Channel(object):

    def __init__(self, client, name, topic='', modes='', chantype=''):
        self.client = client
        self.name = name
        self.topic = topic
        self.modes = modes
        self.chantype = chantype
        self.users = {}
        self.privmsgs = []
        self.notices = []

    def JOIN(self, msg):
        user = User(self.client, self.name, msg)
        self.users[user.nick] = user

# TODO: Complete
    def MODE(self, msg):
        pass

    def NICK(self, msg):
        if msg.nick in self.users:
            self.users[msg.params[0]] = self.users[msg.nick]
            self.users[msg.params[0]].NICK(msg)
            del self.users[msg.nick]

    def NOTICE(self, msg):
        self.notices.append(msg)

    def PART(self, msg):
        if msg.nick in self.users:
            del self.users[msg.nick]

    def PRIVMSG(self, msg):
        self.privmsgs.append(msg)
# TODO: Needs to be... pluginized! :D
        if self.client.nick in msg.params[1]:
            self.client.sending.put(Msg('PRIVMSG',
                [self.name, "G'day, {0}".format(msg.nick)]))

    def QUIT(self, msg):
        if msg.nick in self.users:
            del self.users[msg.nick]
