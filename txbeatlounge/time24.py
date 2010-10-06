'''
The limitations of floating-point arithmetic cause us want to define the smallest amount of time.
To support [32nd notes, 16notes, 8th notes ...] as well as triplets on the quarter and 8th,
we find that the largest common divisor is 1/24 of a specified beats per minute.

time = {
    'common': 1/24.,
    '32nd': 1/8.,        # 3
    '8th3': 1/6. ,       # 4
    '16th': 1/4.  ,      # 6
    'qt3': 1/3.    ,     # 8
    '8th': 1/2.     ,    # 12
    'qt': 1,            # 24
}

This leads to the unfortunate consequence though that
the 16th note arrives every 6th repetition of the smallest unit.

def generator(instrument):

    for i in range(num):
        if is_16th(i):

'''



class Measures(object):

    def __init__(self, number=1, length=4, division=4, bpm=120):
        '''defaults to 1 4/4'''

        self.division = division
        self.length = length            # note __len__ below
        self.bpm = bpm
        self.number = number

        self.schedule_length = (60./bpm)/24

    def __len__(self):
        if self.division == 4:
            return 24*self.length*self.number

        if self.division == 8:
            return 12*self.length*self.number

        raise NotImplementedError('division must be 4 or 8')

    def __iter__(self):
        while True:
            self.i = 0
            for i in range(len(self)):
                self.i = i
                yield self

    def is_quarter(self):
        return not bool(divmod(self.i,24)[1])
    def n_quarter(self):
        return self.i/24 if self.is_quarter() else None

    def is_8th(self):
        return not bool(divmod(self.i,12)[1])
    def n_8th(self):
        return self.i/12 if self.is_8th() else None

    def is_16th(self):
        return not bool(divmod(self.i,6)[1])
    def n_16th(self):
        return self.i/6 if self.is_16th() else None

    def is_32nd(self):
        return not bool(divmod(self.i,3)[1])
    def n_32nd(self):
        return self.i/3 if self.is_32nd() else None

    def is_quarter3(self):
        return not bool(divmod(self.i,8)[1])
    def n_quarter3(self):
        return self.i/8 if self.is_quarter3() else None

    def is_8th3(self):
        return not bool(divmod(self.i,4)[1])
    def n_8th3(self):
        return self.i/4 if self.is_8th3() else None



