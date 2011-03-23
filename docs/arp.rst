beatlounge.arp
==============


Arp classes provide ways to cycle through notes, integer values.
``IndexedArp``, ``AscArp``, ``DescArp``, ``OrderedArp``, ``RevOrderedArp``, ``RandomArp``, ``ArpSwitcher``
and ``OctaveArp`` are currently included (maybe more, check the ``__all__``).

.. code-block:: pycon

    >>> from txbeatlounge.arp import *
    >>> v = DescArp([127, 110, 100, 80, 100, 110])
    >>> v()
    110
    >>> v()
    100
    >>> v()
    80
    >>> v()
    100
    >>> v()
    110
    >>> v()
    127
    >>> v()
    110
    >>> v.reset([1,2,3])
    >>> v()
    2
    >>> v()
    1
    >>> v()
    3
    >>> v()
    2
    >>> v()
    1
 
   
The ``ArpSwitcher`` is probably the most useful b/c, in addition to being able to reset the sequence, 
you can switch the kind of arp.

.. code-block:: pycon


    >>> from txbeatlounge.music.notes import *
    >>> asw = ArpSwitcher(AscArp(), [C[3], F[3], F[4]])
    >>> asw()
    MidiNote(36)
    >>> asw()
    MidiNote(41)
    >>> asw()
    MidiNote(53)
    >>> asw()
    MidiNote(36)
    >>> asw()
    MidiNote(41)
    >>> asw()
    MidiNote(53)
    >>> asw.reset([C[4], A[4], C[5], F[5]])
    >>> asw()
    MidiNote(48)
    >>> asw()
    MidiNote(57)
    >>> asw()
    MidiNote(60)
    >>> asw()
    MidiNote(65)
    >>> asw.switch(DescArp())
    >>> asw()
    MidiNote(65)
    >>> asw()
    MidiNote(60)
    >>> asw()
    MidiNote(57)
    >>> asw()
    MidiNote(48)


You will need to figure a way to load some instruments.  See {{ making your own complib }} TODO!

.. code-block:: pycon

    >>> from comps.complib import *
    >>> gtr = studio_guitar_f()
   

For more on the ``beatlounge.player``, see {{ link to beatlounge.player docs }} TODO!
Here is how we can use the arp classes with the players.

.. code-block:: pycon

    >>> pl = Player(gtr, asw, v, interval=1/8.)
    >>> pl.startPlaying()



