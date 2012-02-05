from connection import Connection
import replycodes

# Constants for IRC special chars
SPACE = ' '
NULL  = '\0'
DELIM = ':'

class Irc(object):
    """ Handles the IRC protocol """

    def __init__(self, server, name):
        self.name = name
        self.nick = server['nick']
        self.channels = server['channels']
        self.conn = Connection(server['host'], server['port'], 
                    server['ssl'], server['timeout'])

    def connect(self):
        self.conn.connect()
        return self.conn.connected

    def disconnect(self):
        self.conn.disconnect()
        return self.conn.connected

#TODO: Not totally sure about this interface yet.
    def send(self, cmd):
        self.conn.oqueue.put(cmd)
    
    def receive(self):
        return self.conn.iqueue.get()

#TODO: allow for saving new params to the config, e.g nick changes
    #def save(config)

        
class Msg(object):
    """ Represents an IRC message to be sent or decoded """

    def __init__(self, msg = None):
        self.prefix = ''
        self.cmd = ''
        self.params = []
        if msg != None:
            self.decode(msg)

    def decode(self, msg):
        if msg.startswith(DELIM):
            self.prefix, msg = msg[1:].split(SPACE, 1)
            msg = msg.lstrip(SPACE)
        self.cmd, msg = msg.split(SPACE, 1)
        while (len(msg) > 0):
            msg = msg.lstrip(SPACE)
            if msg.startswith(DELIM):
                self.params.append(msg[1:])
                break
            p, msg = msg.split(SPACE, 1)
            self.params.append(p)

    def encode(self):
        msg = ''
        if (len(self.prefix) > 0):
            msg += DELIM + self.prefix + SPACE
        msg += self.cmd
        for p in self.params:
            msg += SPACE
            if SPACE in p:
                msg += DELIM + p
                break
            else:
                msg += p
        return msg

    def __repr__(self):
        return self.encode()

    def __str__(self):
        return self.encode()

class User(object):

    def __init__(self, userstring):
        self.prefix
        self.name
        self.host
        self.server
        self.real
