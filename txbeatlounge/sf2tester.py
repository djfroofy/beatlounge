import sys

import optparse

from twisted.internet import reactor

from txbeatlounge.common import Instrument
from txbeatlounge.scheduler import Scheduler, BeatClock, Timely

clock = BeatClock(bpm=60)
machine = Timely(clock=clock)
schedule = Scheduler(clock=clock).schedule


@machine
def play():
    for i in range(opts.range_start, opts.range_end):
        print 'playing note', i
        instrument.playnote(i, opts.volume)
        yield opts.interval
        instrument.stopnote(i) 
        yield opts.interval

opts = None
instrument = None

def main():
    global opts, instrument
    parser = optparse.OptionParser()
    parser.add_option('-v', '--volume', dest='volume', default=100, type='int')
    parser.add_option('-s', '--range-start', dest='range_start', default=0, type='int')
    parser.add_option('-e', '--range-end', dest='range_end', default=128, type='int')
    parser.add_option('-i', '--interval', dest='interval', default=0.125, type='float')
    parser.add_option('-n', '--note', dest='note', default=-1, type='int')
    parser.add_option('-p', '--preset', dest='preset', default=0, type='int')

    opts, args = parser.parse_args()
    sf2path = args[0]
    if opts.note != -1:
        opts.range_start = opts.note
        opts.range_end = opts.note + 1
    instrument = Instrument(sf2path=sf2path, preset=opts.preset)

    schedule(play).start(0)
    reactor.run()

if __name__ == '__main__':
    main()


