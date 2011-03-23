beatlounge.music.notes
========================


.. code-block:: pycon

    >>> from txbeatlounge.music import notes

A notes.MidiNote is a little bit like an 0 <= int < 128.
Instantiate with an int in this range.

.. code-block:: pycon

    >>> my_middle_c = notes.MidiNote(60)

Or, you can use the pre-made notes in the first octave,
``notes.A``, ``notes.Cs``, ``notes.Ef``, etc ..

.. code-block:: pycon

    >>> notes.A
    MidiNote(9)
    >>> notes.Af == notes.Gs
    True
    >>> notes.MidiNote(9) == notes.A
    True
    >>> int(notes.A)
    9
    >>> notes.MidiNote(9) == 9
    True
    >>> notes.A + 2
    MidiNote(11)
    >>> notes.A
    MidiNote(9)
    >>> notes.A - 3
    MidiNote(6)
    >>> 12 - notes.A
    MidiNote(3)

Comparisons work as expected:

.. code-block:: pycon

    >>> notes.A < 12
    True


A MidiNote also acts like a sequence.  You may iterate over the higher octaves, index them, slice them.


.. code-block:: pycon

    >>> [n for n in notes.A]
    [MidiNote(9), MidiNote(21), MidiNote(33), MidiNote(45), MidiNote(57), MidiNote(69), MidiNote(81), MidiNote(93), MidiNote(105), MidiNote(117)]
    >>> notes.A[4]
    MidiNote(57)
    >>> 45 in notes.A
    True
    >>> 60 in notes.A
    False
    >>> notes.A[2:7]
    [MidiNote(33), MidiNote(45), MidiNote(57), MidiNote(69), MidiNote(81)]
    >>> notes.A[1] == 21
    True
    >>> import random
    >>> random.choice(notes.A)
    MidiNote(33)


``reversed()`` acts a little differently that expected.  It steps the octaves backwards.
Negative indexing is consistent with reverse but not the sequences above.
Perhaps we should change this.
But, I thought it would be cool to have reversed() to step through the octaves going lower
instead of higher.  Negative indexing goes backwards in octaves as well.


.. code-block:: pycon


    >>> midC = notes.MidiNote(60)
    >>> midC.freq()
    523.25113060119725
    >>> midC[0]
    MidiNote(60)
    >>> midC[-1]
    MidiNote(48)
    >>> midC[-2]
    MidiNote(36)
    >>> [n for n in reversed(midC)]
    [MidiNote(60), MidiNote(48), MidiNote(36), MidiNote(24), MidiNote(12)]


Note that the reversed() is not subscriptable.


.. code-block:: pycon

    >>> random.choice(reversed(midC))
    Traceback (most recent call last):
      File "<console>", line 1, in <module>
      File "/System/Library/Frameworks/Python.framework/Versions/2.6/lib/python2.6/random.py", line 261, in choice
        return seq[int(self.random() * len(seq))]  # raises IndexError if seq is empty
    TypeError: object of type 'generator' has no len()
    >>> random.choice(list(reversed(midC)))
    MidiNote(12)
    >>> reversed(midC)[0]
    Traceback (most recent call last):
      File "<console>", line 1, in <module>
    TypeError: 'generator' object is unsubscriptable

