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
        self.channels = {}
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

    def _event_loop(self):
        while True:
            if self.irc.wait_for_connection(self.config['timeout']):
                self.sending.put(Msg(cmd='NICK', params=[self.nick]))
                self.sending.put(Msg(cmd='USER', params=[self.nick, '8', '*', self.nick]))
                self.sending.put(Msg(cmd='JOIN', params=[','.join(self.config['channels'])]))
                while self.irc.connected:
                    for msg in self.receiving:
                        func = getattr(self, 'recv_' + msg.cmd.lower(),
                                self.unknown)
                        func(msg)
# TODO: Figure out why this doesn't work
            if self.config['autoretry']:
                print 'rejoining'
                gevent.spawn_later(3, self.irc.connect)
            else:
                gevent.spawn_later(2, self.instance.kill)
                gevent.spawn_later(2, self.backdoor.kill)
                return
# TODO: Add cleanup stuff

    def _back_door(self):
        for line in self._backdoor:
            if line.startswith(self.irc.name):
                line = line[len(self.irc.name):].lstrip()
                exec(line)

    def recv_err_nicknameinuse(self, msg):
        self.nick += '_'
        self.sending.put(Msg(cmd='NICK', params=[self.nick]))
        self.stdio.output.put('Changing nick to ' + self.nick)

    @property
    def connected(self):
        return self.irc.connected

    def join(self, channel):
        pass

    #def recv_join(self, msg):
        #if
        #self.channels[channel] = Channel(channel)

    def part(self, channel):
        del self.channels[channel]

    def quit(self):
        self.sending.put(Msg(cmd='QUIT', params=['Goodbye']))
        gevent.spawn_later(1, self.irc.disconnect)

    def recv_ping(self, msg):
        self.sending.put(Msg(cmd='PONG', params=msg.params))

    def unknown(self, msg):
        if msg.cmd.isdigit():
            self.stdio.output.put("Unknown call: " + msg.cmd)


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
