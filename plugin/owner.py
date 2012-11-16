from functools import wraps
from plugin import *


def owner(func):
    """
    Validates that a someone is an owner of this bot
    before calling the wrapped method.
    """
    @wraps(func)
    def wrapper(self, msg):
        if 'Owner' not in self.client.plugins:
            return
        if self.client.plugins['Owner'].validate(msg):
            return func(self, msg)
    return wrapper


class Owner(Plugin):

    def setup(self, settings, botSettings):
        self.owners = botSettings
        self.authed = {}

    def validate(self, msg):
        return msg.nick in self.authed

    def _auth_pass(self, msg, user, creds):
        nick = msg.nick
        password = msg.params[-1]
        if nick == user and password == creds:
            return True
        else:
            return False

    def _auth_host(self, msg, user, creds):
        if creds[0] != '*' and creds[0] != msg.user:
            return False
        if creds[1] != '*' and creds[1] != msg.host:
            return False
        return True

    def on_join(self, msg):
        for (owner, method, creds) in self.owners:
            if method != 'host':
                continue
            if self._auth_host(msg, owner, creds):
                self.authed[msg.nick] = owner
                self.privmsg(msg.nick, "I've logged you in as %s!" % owner)
                break

    def on_nick(self, msg):
        if msg.nick in self.authed:
            owner = self.authed[msg.nick]
            del self.authed[msg.nick]
            self.authed[msg.params[-1]] = owner

    @command(name='auth')
    def authenticate(self, msg):
        """
        Authenticates yourself.
        Usage: auth [<credentials>]
        """
        authed = False
        for (owner, method, creds) in self.owners:
            if not hasattr(self, '_auth_' + method):
                continue
            auth = getattr(self, '_auth_' + method)
            if auth(msg, owner, creds):
                self.authed[msg.nick] = owner
                authed = owner
                break
        if authed:
            self.privmsg(msg.nick, 'Authenticated as %s' % authed)
        else:
            self.privmsg(msg.nick, 'Failed to authenticate')

    @command(name='deauth')
    def deauthenticate(self, msg):
        """
        Deaunthicates a logged in user.
        With no arguments, deauths yourself.
        Usage: deauth [<nick>]
        """
        if msg.nick in self.authed:
            if msg.params[-1].strip() == '':
                del self.authed[msg.nick]
                self.privmsg(msg.nick, 'You are now deauthenticated')
            if msg.params[-1] in self.authed:
                del self.authed[msg.params[-1]]
                self.privmsg(msg.nick, msg.nick + ' deauthenticated')

    @owner
    @command
    def owners(self, msg):
        a = ', '.join([': '.join(i) for i in self.authed.items()])
        self.privmsg(msg.nick, 'My current owners: %s.' % a)
