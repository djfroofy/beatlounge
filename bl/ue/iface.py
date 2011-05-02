"""
User endpoints
"""

from zope.interface import Interface, Attribute, implements

class IUserEndpoint(Interface):
    """
    Base interface for user endpoints.

    What is a "user endpoint"? We will define a "user endpoint" as an interface
    which specifies controlled interactions with the beatlounge from external
    client. Examples of external clients include: REST clients, IPC clients, RPC
    (amp-based, etc.), a GUI (tkinter, gtk, etc). This provides a common
    interface for all those various things to map their message encodings. Thus
    adapters can be built around an more specific IUserEndpoint interface to decode
    such message encodings and interact directly with the beatlounge in a
    consistent manner accross input from disparate clients.
    """

class IUnitNode(IUserInput):
    """
    Unit sources, routers, and desitination nodes with a beatlounge runtime.

    A unit can be raw audio, MIDI values, parameter modulation values, etc;
    i.e. it's up to the implementation to decide.
    """
    inputs =  Attribute("""
        Number of inputs this unit node has
        """)
    outputs = Attribute("""
        Number of outputs this unit node has
        """)

    def connect(destination, output, input):
        """
        Connect to destination IUnitNode's input from our specified output.

        Multiple calls with the same values are idempotent. Calls with different
        destination and input values should not disconnect prior connections on
        the same output, but create fan-out connections.

        destination: the IUnitNode to connect to
        output: which output on this IUnitNode to connect from
        input: which input to connect to on the destination IAudioNode
        """)

    def disconnect(output):
        """
        Disconnect all existing connections on output.
        """


class IUnitSourceNode(INode):
    """
    A unit source node.
    """
    inputs = Attribute("""
        Always 0
        """)
    outputs = Attribute("""
        Always 1
        """)


class IUnitDestinationNode(INode):
    """
    A unit destination node.
    """
    inputs = Attribute("""
        Always 1
        """)
    outputs = Attribute("""
        Always 0
        """)


class IMidiValueSourceNode(IUnitSourceNode):

    def next():
        """
        Get list of two-tuples consisting of an integer midivalue and integer ticks - when
        the note should be played.

        (MIDI, when)
        """


