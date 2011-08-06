import sys
import random
import os
import tty
import sys
import termios
import getpass
import struct
import fcntl
import signal

from twisted.internet import stdio, protocol, defer
from twisted.conch.stdio import ServerProtocol, ConsoleManhole
from twisted.conch.recvline import HistoricRecvLine
from twisted.python import failure, reflect, log, usage
from twisted.python.filepath import FilePath


from bl.scheduler import Tempo, BeatClock, Meter, standardMeter

__all__ = ['consoleNamespace', 'FriendlyConsoleManhole']

# Todo - make this an opt flag instead
EXPERIMENTAL = False


def toMeter(s, tempo):
    count, division = s.split('/')
    return Meter(int(count), int(division), tempo=tempo)

class Options(usage.Options):
    optParameters = [['channels', 'c', 'stereo', 'Number of channels or a label: stereo, mono, quad'],
                     ['logfile', 'l', 'child.log', 'Path to logfile'],
                     ['bpm', 'b', 130, 'The tempo in beats per minute', int],
                     ['tpb', 't', 24, 'Ticks per beat', int],
                     ['meter', 'm', '4/4', 'The meter (default 4/4)']
                     ]

    def parseArgs(self, audiodev='coreaudio'):
        self['audiodev'] = audiodev

class FriendlyConsoleManhole(ConsoleManhole):

    persistent = True
    historyFile = os.path.join(os.environ.get('HOME', ''), '.beatlounge.history')
    maxLines = 2**12
    session = None
    _onPrompt = None


    def __init__(self, *p, **kw):
        from bl.utils import buildNamespace
        namespace = buildNamespace('twisted.internet',
                'itertools', 'functools', 'collections',
                'bl.instrument.fsynth', 'bl.player', 'bl.notes',
                'bl.filters', 'bl.scheduler', 'bl.debug', 'bl.arp',
                'comps.complib', 'txosc.async', 'bl.osc')
        namespace.update({'random': random})
        self.namespace = namespace
        ConsoleManhole.__init__(self, *p, **kw)

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
        if self._onPrompt:
            return self._answerPrompt(line)
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
            self.writeHelp('  '.join(matches))

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

    def writeHelp(self, text):
        current = ''.join(self.lineBuffer)
        self.terminal.nextLine()
        self.terminal.write(text)
        self.terminal.nextLine()
        self.terminal.write(self.ps[self.pn])
        self.terminal.write(current)


    # methods for host key verification ui

    def prompt(self, message):
        """
        Set state to stop evaluating python and give a yes/no prompt to answer
        to the given message.
        """
        self._onPrompt = defer.Deferred()
        self.writeHelp(message)
        return self._onPrompt

    warn = writeHelp

    def _answerPrompt(self, line):
        answer = line.strip().lower()
        if answer == 'yes':
            self._onPrompt.callback(True)
        else:
            self._onPrompt.callback(False)
        self._onPrompt = None
        self.lineBuffer = []
        self.handle_HOME()
        self.writeHelp('')


try:

    from twisted.conch.ssh import channel, session, keys, connection
    from twisted.conch.client import default, connect, options
    from twisted.conch.client.knownhosts import KnownHostsFile

    def connectConsole(console, user=None, host='127.0.0.1', port=9000):
        opts = options.ConchOptions()
        opts.parseOptions([])
        opts['host'] = host
        opts['port'] = port
        if user is None:
            user = getpass.getuser()
        conn = SSHConnection(console)
        userauth = default.SSHUserAuthClient(user, opts, conn)

        def eb(reason):
            log.err(reason)
            console.writeHelp('failed connecting to remote: %s' % reason)

        log.msg('connecting')

        def verifyHostKey(transport, host, pubKey, fingerprint):
            log.msg('verifying host key')
            actualHost = transport.factory.options['host']
            actualKey = keys.Key.fromString(pubKey)
            kh = KnownHostsFile.fromPath(FilePath(
                transport.factory.options['known-hosts'] or
                os.path.expanduser('~/.ssh/known_hosts')
                ))
            return kh.verifyHostKey(console, actualHost, host, actualKey).addErrback(log.err)

        connect.connect(host, port, opts,
                        verifyHostKey, userauth).addErrback(eb)
        return conn


    class SSHConnection(connection.SSHConnection):

        def __init__(self, console):
            self.console = console
            connection.SSHConnection.__init__(self)

        def serviceStarted(self):
            connection.SSHConnection.serviceStarted(self)
            self.openChannel(SSHSession())
            self.console.writeHelp('connected to remote')

    class SSHSession(channel.SSHChannel):
        name = 'session'

        def channelOpen(self, ignore):
            log.msg('session %s open' % self.id)
            conn = self.conn

            def connectionLost(reason):
                log.msg('connection lost: %s' % reason)
                conn.console.session = None
                conn.console.writeHelp('Lost remote connection! %s' % reason)
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

except ImportError, ie:
    from warnings import warn
    warn('%s - connectConsole() will not be avaiable' % ie)

def runWithProtocol(klass, audioDev, channels, bpm, tpb, meter):
    fd = sys.__stdin__.fileno()
    oldSettings = termios.tcgetattr(fd)
    tty.setraw(fd)
    tempo = Tempo(bpm, tpb)
    meter = toMeter(meter, tempo)
    try:
        # TODO - there should be a cleaner strategy for collecting parameters and
        # initializing fluidsynth - initializing fluidsynth shouldn't really even be
        # necessary
        if EXPERIMENTAL:
            from bl.sync import SystemClock
            clock = BeatClock(tempo=tempo, meter=meter, default=True, syncClockClass=SystemClock)
        else:
            clock = BeatClock(tempo=tempo, meter=meter, default=True)
        clock.synthAudioDevice = audioDev
        clock.synthChannels = channels
        p = ServerProtocol(klass)
        stdio.StandardIO(p)
        clock.run()
    finally:
        termios.tcsetattr(fd, termios.TCSANOW, oldSettings)
        os.write(fd, "\r\x1bc\r")


def main(argv=None, reactor=None):

    opts = Options()
    opts.parseOptions()
    klass = FriendlyConsoleManhole
    log.startLogging(file(opts['logfile'], 'w'))
    log.msg('audio dev: %s' % opts['audiodev'])
    log.msg('channels: %s' % opts['channels'])
    log.msg('tempo/BPM: %s' % opts['bpm'])
    log.msg('tempo/TPB: %s' % opts['tpb'])
    log.msg('meter: %s' % opts['meter'])
    runWithProtocol(klass, opts['audiodev'], opts['channels'], opts['bpm'], opts['tpb'], opts['meter'])

if __name__ == '__main__':
    main()

