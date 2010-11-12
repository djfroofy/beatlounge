from itertools import cycle
import sys

import optparse

from txbeatlounge.internet import reactor

from txbeatlounge.scheduler2 import clock, measuresToTicks
from txbeatlounge.experiment.player import Player, generateSounds
from txbeatlounge.filters import Sustainer
from txbeatlounge.instrument.fsynth import Instrument

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
    parser.add_option('-b', '--bank', dest='bank', default=0, type='int')

    opts, args = parser.parse_args()
    sf2path = args[0]
    if opts.note != -1:
        opts.range_start = opts.note
        opts.range_end = opts.note + 1

    gen = cycle(range(opts.range_start, opts.range_end))
    def noteGenerator():
        next = gen.next()
        print 'note', next
        return next

    instrument = Instrument(sf2path, preset=opts.preset, bank=opts.bank)
    player = Player(instrument,
        noteGenerator,
        Sustainer(opts.volume),
        stop = lambda : measuresToTicks(opts.interval))

    clock.schedule(player.play).startLater(1, opts.interval)
    clock.run()

if __name__ == '__main__':
    main()


