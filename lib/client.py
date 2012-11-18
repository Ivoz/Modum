from lib.irc import Irc
from lib.publisher import Publisher
from lib.stdio import StdIO
import gevent
from gevent.queue import Queue


class Client(object):
    """An IRC Client, designed to be pluggable"""

    def __init__(self, name, config):
        self.name = name
        self.config = config  # Overall config
        self.options = config.clients[name]  # Client options
        self.publisher = Publisher()
        # Initialize Irc connection object
        self.server = config.servers[self.options['server']]
        self.irc = Irc(self.server, self.publisher)
        # Configuration
        self.nick = self.options['nick']
        self.stdio = StdIO()
        self.sending = Queue()
        self.receiving = Queue()
        # Plugins
        self.plugins = {}
        plugins = ['Base'] + self.options['plugins'].keys()
        [self.load_plugin(p) for p in plugins]
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

    def kill(self):
        """Completely close connection to server"""
        while not self.sending.empty():
            gevent.sleep(0.5)
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

    def load_plugin(self, plugin):
        if self._load_module(plugin):
            if hasattr(self.plugins[plugin], 'setup'):
                settings = None
                if plugin in self.config.plugins:
                    settings = self.config.plugins[plugin]
                botSettings = None
                if plugin in self.options['plugins']:
                    botSettings = self.options['plugins'][plugin]
                self.plugins[plugin].setup(settings, botSettings)

    def _event_loop(self):
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


class FinishLoop(StopIteration):
    pass
