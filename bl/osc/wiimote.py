from bl.osc import FloatDispatcher, BoolDispatcher, DispatcherHub


class Wiimote(object):
    pitch = 0
    roll = 0
    yaw = 0
    accel = 0
    one = 0
    two = 0
    A = 0
    B = 0
    up = 0
    down = 0
    left = 0
    right = 0
    home = 0
    minus = 0
    plus = 0

    def on_pitch(self, pitch):
        self.pitch = pitch

    def on_roll(self, roll):
        self.roll = roll

    def on_yaw(self, yaw):
        self.yaw = yaw

    def on_accel(self, accel):
        self.accel = accel

    def on_one(self, one):
        self.one = one

    def on_two(self, two):
        self.two = two

    def on_A(self, A):
        self.A = A

    def on_B(self, B):
        self.B = B

    def on_up(self, up):
        self.up = up

    def on_down(self, down):
        self.down = down

    def on_left(self, left):
        self.left = left

    def on_right(self, right):
        self.right = right

    def on_home(self, home):
        self.home = home

    def on_minus(self, minus):
        self.minus = minus

    def on_plus(self, plus):
        self.plus = plus


ROOT = 'wii/1/accel/pry/'
PITCH_ADDR = ROOT + '0'
ROLL_ADDR = ROOT + '1'
YAW_ADDR = ROOT + '2'
ACCEL_ADDR = ROOT + '3'
BUTTON_ROOT = 'wii/1/button/'
BUTTON1 = BUTTON_ROOT + '1'
BUTTON2 = BUTTON_ROOT + '2'
BUTTONA = BUTTON_ROOT + 'A'
BUTTONB = BUTTON_ROOT + 'B'
BUTTON_DOWN = BUTTON_ROOT + 'Down'
BUTTON_HOME = BUTTON_ROOT + 'Home'
BUTTON_LEFT = BUTTON_ROOT + 'Left'
BUTTON_MINUS = BUTTON_ROOT + 'Minus'
BUTTON_PLUS = BUTTON_ROOT + 'Plus'
BUTTON_RIGHT = BUTTON_ROOT + 'Right'
BUTTON_UP = BUTTON_ROOT + 'Up'


class PitchDispatcher(FloatDispatcher):
    address = PITCH_ADDR


class RollDispatcher(FloatDispatcher):
    address = ROLL_ADDR


class YawDispatcher(FloatDispatcher):
    address = YAW_ADDR


class AccelDispatcher(FloatDispatcher):
    address = ACCEL_ADDR


def wiimoteHub():
    """
    Returns a DispatcherHub with a the wiimote that is updated with
    pitch, roll, yaw and accel.

    An example of attaching the hub's receiver to listen on udp:

        from txosc.async import DatagramServerProtocol
        hub = wiimoteHub()
        wiimote = hub.wiimote
        reactor.listenUDP(17779, DatagramServerProtocol(hub.receiver),
                          interface='0.0.0.0')
    """
    wiimote = Wiimote()

    hub_args = []
    for Dispatcher, wii_meth in [
        (PitchDispatcher, wiimote.on_pitch),
        (RollDispatcher, wiimote.on_roll),
        (YawDispatcher, wiimote.on_yaw),
        (AccelDispatcher, wiimote.on_accel),
        (BoolDispatcher(BUTTON1), wiimote.on_one),
        (BoolDispatcher(BUTTON2), wiimote.on_two),
        (BoolDispatcher(BUTTONA), wiimote.on_A),
        (BoolDispatcher(BUTTONB), wiimote.on_B),
        (BoolDispatcher(BUTTON_DOWN), wiimote.on_down),
        (BoolDispatcher(BUTTON_UP), wiimote.on_up),
        (BoolDispatcher(BUTTON_LEFT), wiimote.on_left),
        (BoolDispatcher(BUTTON_RIGHT), wiimote.on_right),
        (BoolDispatcher(BUTTON_MINUS), wiimote.on_minus),
        (BoolDispatcher(BUTTON_HOME), wiimote.on_home),
        (BoolDispatcher(BUTTON_PLUS), wiimote.on_plus),
    ]:
        d = Dispatcher()
        d.listen(wii_meth)
        hub_args.append(d)

    hub = DispatcherHub(*hub_args)
    hub.wiimote = wiimote
    return hub
