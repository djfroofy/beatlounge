Beatlounge
----------

The framework of your beats.

Overview
~~~~~~~~

The beatlounge is an experiment in computer music. It makes sound. It's fun.
You can program melodies and wicked arpegiators, whatever your imagination
and technical prowess allows. And it's simple. Really, really simple.

It's written in Python and uses Twisted for its scheduling but you don't have
to know anything about Twisted to use it. Promise.


Some Features
~~~~~~~~~~~~~

* Isochronous scheduler based on musical meters and tick rate (pulses per quarter)
* MIDI integration and a decent abstraction layer over pyportmidi via bl.midi
* OSC ingegration and some predefined device adaptors (uses txosc)
* uses fluidsynth for loading and playing soundfonts
* "pluggable" backends for virtual instruments
* An extensible arpegiator library which can be used to control melodies and rhythms
* Live-coding environment using twisted.conch.stdio
* A fun set of toys like bl.osc.wiimote, bl.osc.touchosc, etc

The project is still under active development and there are lots of half-baked
parts as well total garbage that will likely go away in the near future.


Installation
~~~~~~~~~~~~

The module can be installed with all of it's python dependencies with:

    python setup.py install

Installing just python dependencies (with pip):

    pip install -r requirements.txt

You can run unit tests with trial:

    trial bl


For rilz.


