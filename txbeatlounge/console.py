import sys

import os, tty, sys, termios

from twisted.internet import stdio, protocol, defer
from twisted.conch.stdio import ServerProtocol, ConsoleManhole
from twisted.python import failure, reflect, log

from txbeatlounge.internet import reactor

def runWithProtocol(klass):
    fd = sys.__stdin__.fileno()
    oldSettings = termios.tcgetattr(fd)
    tty.setraw(fd)
    try:
        p = ServerProtocol(klass)
        stdio.StandardIO(p)
        reactor.run()
    finally:
        termios.tcsetattr(fd, termios.TCSANOW, oldSettings)
        os.write(fd, "\r\x1bc\r")


def main(argv=None, reactor=None):
    log.startLogging(file('child.log', 'w'))

    if argv is None:
        argv = sys.argv[1:]
    if argv:
        klass = reflect.namedClass(argv[0])
    else:
        klass = ConsoleManhole
    runWithProtocol(klass)

if __name__ == '__main__':
    main()
 
