import sys

import os, tty, sys, termios

from twisted.internet import stdio, protocol, defer
from twisted.conch.stdio import ServerProtocol, ConsoleManhole
from twisted.conch.recvline import HistoricRecvLine
from twisted.python import failure, reflect, log
from twisted.python.filepath import FilePath

from txbeatlounge.scheduler import clock as reactor

class FriendlyConsoleManhole(ConsoleManhole):

    historyFile = os.path.join(os.environ.get('HOME', ''), '.beatlounge.history')
    maxLines = 2**12

    def connectionMade(self):
        self._historySession = os.getpid()
        self._historyFd = open(self.historyFile + ('.%d' % self._historySession), 'w')
        ConsoleManhole.connectionMade(self)
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
        self._historyFd.close()
        path = FilePath(self.historyFile + ('.%d' % self._historySession))
        path.moveTo(FilePath(self.historyFile))
        ConsoleManhole.connectionLost(self, reason)

    def handle_RETURN(self):
        line = ''.join(self.lineBuffer)
        rv = ConsoleManhole.handle_RETURN(self)
        if line:
            self._historyFd.write(line + '\n')
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
    import time
    main()
 
