from txbeatlounge.osc import FloatDispatcher, DispatcherHub

class Wiimote(object):
    pitch = 0
    roll = 0
    yaw = 0
    accel = 0

    def on_pitch(self, pitch):
        self.pitch = pitch

    def on_roll(self, roll):
        self.roll = roll

    def on_yaw(self, yaw):
        self.yaw = yaw

    def on_accel(self, accel):
        self.accel = accel


ROOT = 'wii/1/accel/pry/'
PITCH_ADDR = ROOT + '0'
ROLL_ADDR = ROOT + '1'
YAW_ADDR = ROOT + '2'
ACCEL_ADDR = ROOT + '3'

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
    Returns a DispatcherHub with a the wiimote thay is updated with
    pitch, roll, yaw and accel.
    
    An example of attaching the hub's receiver to listen on udp:

        from txosc.async import DatagramServerProtocol
        hub = wiimoteHub()
        wiimote = hub.wiimote
        reactor.listenUDP(17779, DatagramServerProtocol(hub.receiver), interface='0.0.0.0')
    """
    wiimote = Wiimote()
    pd = PitchDispatcher()
    pd.listen(wiimote.on_pitch)
    rd = RollDispatcher()
    rd.listen(wiimote.on_roll)
    yd = YawDispatcher()
    yd.listen(wiimote.on_yaw)
    ad = AccelDispatcher()
    ad.listen(wiimote.on_accel)
    hub = DispatcherHub(pd, rd, yd, ad)
    hub.wiimote = wiimote
    return hub

