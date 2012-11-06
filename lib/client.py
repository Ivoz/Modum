from lib.irc import Irc
from lib.publisher import Publisher
from lib.stdio import StdIO
import gevent
from gevent.queue import Queue


class Client(object):

    def __init__(self, name, config):
        self.name = name
        conf = config.clients[name]
        self.config = conf
        self.publisher = Publisher()
        # Initialize Irc connection object
        self.server = config.servers[conf['server']]
        self.irc = Irc(self.server, self.publisher)
        # Configuration
        self.nick = config.clients[name]['nick']
        self.stdio = StdIO()
        self.sending = Queue()
        self.receiving = Queue()
        self.plugins = {}
        for plugin in ['Base'] + conf['plugins']:
            if self._load_module(plugin):
                if plugin in config.plugins:
                    self.plugins[plugin].setup(config.plugins[plugin])
                else:
                    self.plugins[plugin].setup()
                self.plugins[plugin]._load_commands()
        self.instance = None

    def start(self):
        if self.instance is not None:
            raise
        self.publisher.subscribe(self.irc.sender, self.sending)
        self.publisher.subscribe(self.receiving, self.irc.receiver)
# TODO: Remove, debugging
        self.publisher.subscribe(self.stdio.output,
                self.irc.receiver, str)
        self.publisher.subscribe(self.stdio.output,
                self.irc.sender, str)
        from lib.irc import Msg
        self.publisher.subscribe(self.sending,
                self.stdio.input, Msg.from_msg)
        self.irc.connect()
        self.instance = gevent.spawn(self._event_loop)
        return self.instance

    def _event_loop(self):
# TODO: Add cleanup stuff
        gevent.spawn(self.plugins['Base'].on_connect)
        for msg in self.receiving:
            if msg is FinishLoop:
                break
            for plugin in self.plugins.values():
                cmd = 'on_' + msg.cmd.lower()
                if hasattr(plugin, cmd):
                    func = getattr(plugin, cmd)
                    gevent.spawn(func, msg)
                if msg.ctcp is not None:
                    cmd = 'on_ctcp_' + msg.ctcp[0].lower()
                    if hasattr(plugin, cmd):
                        func = getattr(plugin, cmd)
                        gevent.spawn(func, msg)

    def _load_module(self, plugin):
        try:
            p_name = 'plugin.' + plugin.lower()
            p = __import__(p_name, fromlist=[plugin], level=-1)
            self.plugins[plugin] = getattr(p, plugin)(self)
            return True
        except ImportError as e:
            print str(e)
            return False

    def kill(self):
        self.irc.kill()
# TODO: Remove, debugging
        self.publisher.unsubscribe(self.irc.sender, self.sending)
        self.publisher.unsubscribe(self.receiving, self.irc.receiver)
        self.publisher.unsubscribe(self.stdio.output,
            self.irc.receiver)
        self.publisher.unsubscribe(self.stdio.output,
            self.irc.sender)
        self.stdio.stop()
        self.receiving.put(FinishLoop)


class FinishLoop(StopIteration):
    pass


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
