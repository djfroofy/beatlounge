from zope.interface import Interface, Attribute


class Instrument(Interface):
    """
    Abstract interface for Instruments: Wrappers around various
    backends for making sound: fluidsynth, pyo, pyaudio, midi, etc.
    """

    clock = Attribute("""
        The BeatClock this Instrument should use for any time-related functions
        """)


class IMIDIInstrument(Interface):
    """
    A MIDI-like instrument supported a minimal subset of MIDI commands.
    """

    channel = Attribute("""
        The MIDI channel or None if this is a virtual MIDI instrument with no
        real channel assigned.
        """)

    def noteon(note, velocity):
        """
        Send a "Note On" event with a MIDI note and velocity ("loudness").

        @param note: The note [0,127]
        @param velocity: The velocity [0,127]
        """

    def noteoff(note):
        """
        Send a "Note Off" event with a MIDI note.

        @param note: The note [0,127]
        """

    def chordon(chord, velocity):
        """
        Call noteon(note, velocity) for each note in chord.

        @param chord: The notes (list)
        @param velocity: The velocity for the chord.
        """

    def chordoff(chord):
        """
        Call noteoff(note) for each note in chord.

        @param chord: The notes (list)
        """

    def controlChange(vibrato=None, pan=None, expression=None, sustain=None,
                      reverb=None, chorus=None, **other):
        """
        Send a "Control Change" (CC) event. The implementation may support 0 to
        all of the predefined controls.

        @param vibrato: vibrato (Control #76) [0,127]
        @param pan: pan (Control #10) [0,127]
        @param expression: expression (Control #11) [0,127]
        @param sustain: sustain/pedal (Control #64) [0,127]
        @param reverb: reverb effect (Control #91) [0,127]
        @param chorus: chorus effect (Control #93) [0,127]
        @param other: Other control keyword arguments (naming may vary by
        implementation)
        """

    def pitchBend(value):
        """
        Send a "Pitch Bend" event.

        @param value: The pitch bend amount [0,127]
        """
