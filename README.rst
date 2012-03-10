Beatlounge
----------

The framework of your beats.

Overview
~~~~~~~~

The beatlounge is an experiment in computer music. It makes sound. It's fun.

It's written in Python and uses Twisted for its scheduling but you don't have
to know anything about Twisted to use it. Promise.


Some Features
~~~~~~~~~~~~~


* Isochronous scheduler based on configured tempo and meter.
* Pluggable clock synchronization (System Time and Midi Beat Clock)
* Pluggable backends for virtual instruments (current implementations are
  pyfluidsynth and generic)
* A high-level interface for virtual instrument players
* Arpeggiators, drum sequencers, and general pattern generators
* Constants mapping musical notes/chords/scales to MIDI note values and some
  fun-loving functions over those things: chord inversions, and some crazy (as in
  crazy awesome) thing we've dubbed grasshoppers
* A python console-based live-coding environment (beatlounge)
* Beginnings of near plug-and-play integration with MIDI and OSC devices
* Some OSC utilities leveraging txosc and mappings to popular embedded OSC
  applications (touchosc, andosc, wiimote - via osculator)
* A (malas palabras)y beat slicing algorithm that can almost sound boss given
  the right conditions
* A grab bag of almost good things that are about to get tossed and completely
  rewritten with a different API.
* Unit tests! Did I say they run fast?
* Some things we'd rather not talk about.


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


