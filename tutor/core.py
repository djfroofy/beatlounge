# All the names we want in our beatlounge python console

import random # for rilz
from itertools import cycle
from functools import partial
from collections import deque

from twisted.python import log

from complib import *
from bl.instrument.fsynth import *
from bl.player import *
from bl.arp import *
from bl.notes import *
from bl.filters import *
from bl.scheduler import *
from bl.debug import setDebug, DEBUG

from bl.music import notes, chords, scales, constants


