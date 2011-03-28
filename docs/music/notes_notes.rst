beatlounge.music.notes (Notes)
==============================


``reversed`` is non-standard
----------------------------

I know it was intended, but the gross incosistency between ``__iter__`` and
``__reversed__`` is not good:

.. code-block:: pycon

    >>> list(C)
    [MidiNote(0),
     MidiNote(12),
     MidiNote(24),
     MidiNote(36),
     MidiNote(48),
     MidiNote(60),
     MidiNote(72),
     MidiNote(84),
     MidiNote(96),
     MidiNote(108),
     MidiNote(120)]
    >>> list(reversed(C))
    []

``reversed`` should iterate from ``120`` to ``0`` in the above case.


Negative indexing is non-standard
---------------------------------

This goes against the usual semantics of negative indexing:

.. code-block:: pycon

    >>> C[10] == C[-1]
    False


On that note, ``C[11]`` etc should just result in ``IndexError``, not:

.. code-block:: pycon

    >>> C[10] == C[11]
    True


Iterate and reverse the same regardless of where note is rooted?
----------------------------------------------------------------

It think this is odd:

.. code-block:: pycon

    >>> list(C[3]) == list(C)
    False

It is simple enough to achieve what we're doing with this instead:

.. code-block:: pycon

    >>> C[3:]
    [MidiNote(36),
     MidiNote(48),
     MidiNote(60),
     MidiNote(72),
     MidiNote(84),
     MidiNote(96),
     MidiNote(108),
     MidiNote(120)]

If you absolutely think iterating from the rooted note up is better, I guess I can
be convinced, but please make the following ``True`` instead of ``False``:

.. code-block:: pycon

    >>> list(reversed(list(C[3])) == list(reversed(C[3]))
    False


