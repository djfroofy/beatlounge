import sndobj
import math
import uuid


class SndObjInstrument(object):
    '''# basically an oscillator and a filter'''

    def __init__(self, name, driver='jack'):
        self.amp = .01
        self.tab = sndobj.HarmTable(16384, 25, sndobj.SQUARE)
        self.env = sndobj.Interp(0, 0, 0.02)
        self.osc = sndobj.Oscili(self.tab, 440, 0, None, self.env)
        self.fil = sndobj.Lp(100,0.5,self.osc)
        #self.outp = sndobj.SndRTIO(self.fil)
        if driver == 'jack':
            self.outp = sndobj.SndJackIO(name) #TODO jack_client_new is deprecated
            self.outp.SetOutput(1,self.osc)
            self.outp.SetOutput(2,self.osc)
        else:
            raise NotImplementedError('currently you must use jack to use a SndObjInstrument')
        #self.thread = sndobj.SndThread(0, None, self.outp)
        self.thread = sndobj.SndThread() #0, None, self.outp)
        self.thread.AddObj(self.env)
        self.thread.AddObj(self.osc)
        self.thread.AddObj(self.fil)
        self.thread.AddObj(self.outp, sndobj.SNDIO_OUT)
        self.thread.ProcOn()

        self.is_on = False

    def output(self):
        sig = self.fil.Output(0)
        return abs(sig)

    def set_freq(self,freq):
        self.osc.SetFreq(freq)

    def set_amp(self,amp):
        self.amp = amp
        self.osc.SetAmp(self.amp)
        self.fil.SetFreq(self.amp*0.5, None)

    def on(self):
        self.is_on = True
        self.env.SetCurve(0,self.amp)
        self.env.Restart()

    def off(self):
        self.is_on = False
        self.env.SetCurve(self.amp, 0)
        self.osc.SetAmp(0, self.env)
        self.env.Restart()


