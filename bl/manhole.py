import binascii
import base64

from zope.interface import implements

from twisted.application import service, strports
from twisted.cred import checkers, portal
from twisted.conch import telnet
try:
    from twisted.conch import manhole_ssh, checkers as conchc
except ImportError, ie:
    from warnings import warn
    warn('%s - AuthorizedKeysManhole not avaiable' % ie)
    manhole_ssh = None
    conchc = None
from twisted.conch.insults import insults
from twisted.internet import protocol

from bl.console import consoleNamespace, FriendlyConsoleManhole

# TODO
# Beh ... don't know if we even want even ColoredManhole; the eventual
# "idea" is to fork input to both the local console and a remote
# manhole interpreter


class FriendlyManhole(FriendlyConsoleManhole):

    persistent = False

    def connectionLost(self, reason):
        pass


class makeTelnetProtocol:
    # this curries the 'portal' argument into a later call to
    # TelnetTransport()
    def __init__(self, portal):
        self.portal = portal

    def __call__(self):
        auth = telnet.AuthenticatingTelnetProtocol
        return telnet.TelnetTransport(auth, self.portal)


class _TelnetRealm:
    implements(portal.IRealm)

    def __init__(self, namespace_maker):
        self.namespace_maker = namespace_maker

    def requestAvatar(self, avatarId, *interfaces):
        if telnet.ITelnetProtocol in interfaces:
            namespace = self.namespace_maker()
            p = telnet.TelnetBootstrapProtocol(insults.ServerProtocol,
                                               FriendlyManhole,
                                               namespace)
            return (telnet.ITelnetProtocol, p, lambda: None)
        raise NotImplementedError()

if conchc:
    class AuthorizedKeysChecker(conchc.SSHPublicKeyDatabase):

        def __init__(self, authorized_keys_file):
            self.authorized_keys_file = authorized_keys_file

        def checkKey(self, credentials):
            with open(self.authorized_keys_file) as fd:
                for line in fd:
                    l2 = line.split()
                    if len(l2) < 2:
                        continue
                    try:
                        if base64.decodestring(l2[1]) == credentials.blob:
                            return 1
                    except binascii.Error:
                        continue
            return 0


class _BaseManhole(service.MultiService):

    def __init__(self, port, checker, using_ssh=True):
        service.MultiService.__init__(self)
        if type(port) is int:
            port = 'tcp:%d' % port
        self.port = port
        self.checker = checker

        def makeNamespace():
            namespace = dict(consoleNamespace)
            return namespace

        def makeProtocol():
            namespace = makeNamespace()
            p = insults.ServerProtocol(FriendlyManhole, namespace)
            return p

        if using_ssh:
            r = manhole_ssh.TerminalRealm()
            r.chainedProtocolFactory = makeProtocol
            p = portal.Portal(r, [self.checker])
            f = manhole_ssh.ConchFactory(p)
        else:
            r = _TelnetRealm(makeNamespace)
            p = portal.Portal(r, [self.checker])
            f = protocol.ServerFactory()
            f.protocol = makeTelnetProtocol(p)

        s = strports.service(self.port, f)
        s.setServiceParent(self)

if manhole_ssh:
    class AuthorizedKeysManhole(_BaseManhole):

        def __init__(self, port, keyfile):
            self.keyfile = keyfile
            c = AuthorizedKeysChecker(keyfile)
            _BaseManhole.__init__(self, port, c)


class TelnetManhole(_BaseManhole):

    def __init__(self, port, username, password):
        self.username = username
        self.password = password

        c = checkers.InMemoryUsernamePasswordDatabaseDontUse()
        c.addUser(username, password)

        _BaseManhole.__init__(self, port, c, using_ssh=False)
