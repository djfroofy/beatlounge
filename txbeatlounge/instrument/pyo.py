from pyo import *

s = Server(sr=44100, nchnls=2, buffersize=512, duplex=0).boot()
s.start()

a = Sine([.1,.2,.3], 0, 100, 500)
b = Sine(a, mul=.4).out()

