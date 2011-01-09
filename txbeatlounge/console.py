import sys
import random
import os
import tty
import sys
import termios

from twisted.internet import stdio, protocol, defer
from twisted.conch.stdio import ServerProtocol, ConsoleManhole
from twisted.conch.recvline import HistoricRecvLine
from twisted.python import failure, reflect, log
from twisted.python.filepath import FilePath

from txbeatlounge.scheduler import clock as reactor
from txbeatlounge.utils import buildNamespace

__all__ = ['consoleNamespace', 'FriendlyConsoleManhole']

consoleNamespace = buildNamespace(
        'itertools', 'functools', 'collections', 'txbeatlounge.instrument.fsynth',
        'txbeatlounge.player', 'txbeatlounge.notes', 'txbeatlounge.filters',
        'txbeatlounge.scheduler', 'txbeatlounge.debug', 'comps.complib')
consoleNamespace.update({'random': random})

class FriendlyConsoleManhole(ConsoleManhole):

    persistent = True
    historyFile = os.path.join(os.environ.get('HOME', ''), '.beatlounge.history')
    maxLines = 2**12
    namespace = consoleNamespace
    session = None

    def connectionMade(self):
        ConsoleManhole.connectionMade(self)
        if self.persistent:
            self._readHistoryFile()
        self.interpreter.locals['console'] = self
        
    def _readHistoryFile(self):
        self._historySession = os.getpid()
        self._historyFd = open(self.historyFile + ('.%d' % self._historySession), 'w')
        if os.path.exists(self.historyFile):
            with open(self.historyFile) as fd:
                lineCount = 0
                for line in fd:
                    if not line.strip(): continue
                    if lineCount > self.maxLines:
                        self.historyLines.pop(0)
                    self.historyLines.append(line[:-1])
                    lineCount += 1
        for line in self.historyLines:
            self._historyFd.write(line + '\n')
        self.historyPosition = len(self.historyLines)

    def connectionLost(self, reason):
        if self.persistent:
            self._historyFd.close()
            path = FilePath(self.historyFile + ('.%d' % self._historySession))
            path.moveTo(FilePath(self.historyFile))
        ConsoleManhole.connectionLost(self, reason)

    def handle_RETURN(self):
        line = ''.join(self.lineBuffer)
        rv = ConsoleManhole.handle_RETURN(self)
        if line and self.persistent:
            self._historyFd.write(line + '\n')
        if self.session:
            log.msg('session set - forwarding line: %r' % line)
            self.session.write(line + '\r\n')
        return rv

    def handle_UP(self):
        lineToDeliver = None
        if self.lineBuffer and self.historyPosition == len(self.historyLines):
            current = ''.join(self.lineBuffer)
            for line in reversed(self.historyLines):
                if line[:len(current)] == current:
                    lineToDeliver = line
                    break
        elif self.historyPosition > 0:
            self.historyPosition -= 1
            lineToDeliver = self.historyLines[self.historyPosition]
        if lineToDeliver:
            self._resetAndDeliverBuffer(lineToDeliver)

    def _resetAndDeliverBuffer(self, buffer):
        self.handle_HOME()
        self.terminal.eraseToLineEnd()
        self.lineBuffer = []
        self._deliverBuffer(buffer)

    def handle_TAB(self):
        if not self.lineBuffer:
            return
        current = ''.join(self.lineBuffer)
        if '.' in current:
            matches = self._matchAttributes(current)
        else:
            matches = self._matchLocals(current)
        if not matches:
            return
        if len(matches) == 1:
            if '.' in current:
                buf = '.'.join(current.split('.')[:-1]) + '.' + matches[0] 
                self._resetAndDeliverBuffer(buf)
            else:
                self._resetAndDeliverBuffer(matches[0])
        else:
            matches.sort()
            self._writeHelp('  '.join(matches))

    def _matchAttributes(self, current):
        names = current.split('.')
        obj = self.interpreter.locals.get(names[0], None)
        if obj is None:
            return
        for name in names[1:-1]:
            obj = getattr(obj, name, None)
            if obj is None:
                return
        matches = []
        for name in dir(obj):
            # Omit private names unless we're really trying to complete them
            if not names[-1] and name[0] == '_':
                continue
            if name[:len(names[-1])] == names[-1]:
                matches.append(name)
        return matches

    def _matchLocals(self, current):
        matches = []
        for name in self.interpreter.locals.iterkeys():
            if name[:len(current)] == current:
                matches.append(name)
        return matches

    def _writeHelp(self, text):
        current = ''.join(self.lineBuffer)
        self.terminal.nextLine()
        self.terminal.write(text)
        self.terminal.nextLine()
        self.terminal.write(self.ps[self.pn])
        self.terminal.write(current)
        
try:
    import getpass
    import tty
    import struct
    import fcntl
    import signal

    from twisted.conch.ssh import channel, session, connection
    from twisted.conch.client import default, connect, options


    def connectConsole(console, user=None, host='127.0.0.1', port=9000):
        opts = options.ConchOptions()
        opts.parseOptions([])
        opts['host'] = host
        opts['port'] = port
        if user is None:
            user = getpass.getuser()
        conn = SSHConnection(console)
        userauth = default.SSHUserAuthClient(user, opts, conn)

        log.msg('connecting')
        connect.connect(host, port, opts,
                        default.verifyHostKey, userauth).addErrback(log.err)
        return conn

    class SSHConnection(connection.SSHConnection):

        def __init__(self, console):
            self.console = console
            connection.SSHConnection.__init__(self)

        def serviceStarted(self):
            connection.SSHConnection.serviceStarted(self)
            self.openChannel(SSHSession())
            self.console._writeHelp('connected to remote')

    class SSHSession(channel.SSHChannel):
        name = 'session'

        def channelOpen(self, ignore):
            log.msg('session %s open' % self.id)
            conn = self.conn

            def connectionLost(reason):
                log.msg('connection lost: %s' % reason)
                conn.console.session = None
                conn.console._writeHelp('Lost remote connection! %s' % reason)
                self.sendEOF()

            client = session.SSHSessionClient()
            #client.dataReceived = dataReceived
            client.connectionLost = connectionLost
            
            conn.console.session = self

            # tty voodoo magic (my head is officially fucking hurting)
            term = os.environ['TERM']
            winsz = fcntl.ioctl(0, tty.TIOCGWINSZ, '12345678')
            winSize = struct.unpack('4H', winsz)
            ptyReqData = session.packRequest_pty_req(term, winSize, '')
            conn.sendRequest(self, 'pty-req', ptyReqData)
            signal.signal(signal.SIGWINCH, self._windowResized)
            conn.sendRequest(self, 'shell', '')

        def dataReceived(self, data):
            log.msg('data received from remote side. bytes=%r' % data)

        def closeReceived(self):
            log.msg('remote side closed %s' % self) 

        def closed(self):
            log.msg('closed: %r' % self)
            self.conn.console.session = None
 
        def sendEOF(self):
            self.conn.sendEOF(self)
    
        def _windowResized(self, *args):
            winsz = fcntl.ioctl(0, tty.TIOCGWINSZ, '12345678')
            winSize = struct.unpack('4H', winsz)
            newSize = winSize[1], winSize[0], winSize[2], winSize[3]
            self.conn.sendRequest(self, 'window-change', struct.pack('!4L', *newSize))

except ImportError:
    pass

def runWithProtocol(klass, audioDev):
    fd = sys.__stdin__.fileno()
    oldSettings = termios.tcgetattr(fd)
    tty.setraw(fd)
    try:
        p = ServerProtocol(klass)
        stdio.StandardIO(p)
        reactor.synthAudioDevice = audioDev
        reactor.run()
    finally:
        termios.tcsetattr(fd, termios.TCSANOW, oldSettings)
        os.write(fd, "\r\x1bc\r")


def main(argv=None, reactor=None):
    log.startLogging(file('child.log', 'w'))

    audioDev = 'coreaudio'

    if argv is None:
        argv = sys.argv[1:]
        if argv:
            audioDev = argv[0]
            argv = argv[2:]
    if argv:
        klass = reflect.namedClass(argv[0])
    else:
        klass = FriendlyConsoleManhole
    log.msg('audio dev: %s' % audioDev)
    runWithProtocol(klass, audioDev)

if __name__ == '__main__':
    main()
 
