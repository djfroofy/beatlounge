import random

from txbeatlounge import constants

def rising_gen(gen):
    incr = 128/gen.num
    while True:
        for i in range(gen.num):
            if not any([divmod(i, o)[1] for o in gen.ones]):
                gen.e.playchord(gen.all_midi_notes, 127)

            gen.e.playnote(gen.choose_one(), incr*i)
            yield


def kick_gen(gen):
    while True:
        for i in range(gen.num):
            if not all([divmod(i, o)[1] for o in gen.ones]):
                gen.e.playnote(gen.choose_one(), gen.get_volume(10))

            else:
                if random.random() < .5:
                    gen.e.playnote(gen.choose_one(), gen.get_volume(-10))

            yield

def pattern1_gen(self):
    while True:
        for i in range(self.num):
            note = random.choice(self.notes)
            notes = getattr(constants, note)
            if not any([divmod(i, o)[1] for o in self.ones]):
                self.e.playchord(self.all_midi_notes, 10)

            else:
                self.e.stopchord(self.all_midi_notes[12:])
                self.e.playchord(notes[4:6], random.choice(range(5,35)))

                for n in range(3):
                    self.e.playnote(self.get_random_note(), random.choice(range(10,20)))

            yield


