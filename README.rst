txBeatLounge is an experiment in computer music. At its core txBeatLounge is:

1. An musical-measure-relative event scheduler based on Twisted
2. Wrapper around fluidsynth for loading and playing soundfonts
3. A configural metronome for calculating the current beat relative to mostly any meter of your choice
4. A set of utilities for affecting sound velocity over time (txbeatlounge.filters)
   and generating patterns of notes and chords.
5. A simple python console based on twisted.conch.stdio.
6. A fun set of toys like txbeatlounge.osc.wiimote for connecting devices
   to virtual instruments.

The project is still under active development and there are lots of half-baked
parts as well total garbage that will likely go away in the near future.

Installation
------------

The module can be installed with all of it's python dependencies with:

    python setup.py install

Installing just python dependencies (with pip):

    pip install -r requirements.txt

You can run unit tests with trial:

    trial txbeatlounge


Additional dependencies for certain parts of txBeatLounge, from other languages,
may include fluidsynth, sndobj, supercollider, osculator, touchosc, puredata, 
cwiid and other software and hardware, proprietary and open source,
in the past, present and future.  They are, of course, not provided and must be installed
on the users machine and configured.  The authors primarily use OS X 10.6 with JACK
and homebrew installed packages where possible.


Future
------

There is some experimental stuff in ble package (ble = beatlounge experiment).
We hope to graduate good experiments to the stable package txbeatlounge
and of course cleanup and adequately test this dog before too long.

For rilz.


