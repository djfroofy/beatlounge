
class Effect(object):

    def __call__(self):
        pass


class Fade(object):

    direction = 0

    def __init__(self, min=0, max=90):
        self.min = min
        self.max = max
        self.current = min
    
    def __call__(self):
        self.current += self.direction
        self.current = self.cap()
        return self.current

    def cap(self):
        pass


class FadeIn(Fade):

    direction = 1

    def cap(self):
        return min(self.current, self.max)


class FadeOut(Fade):

    direction = -1

    def __init__(self, min=0, max=90):
        super(FadeOut, self).__init__(min, max)
        self.current = max

    def cap(self):
        return max(self.current, self.min)


class FadeInOut(object):

    def __init__(self, min=0, max=90, hold_for_iterations=48, outro=None):
        self.hold_for_iterations = hold_for_iterations
        self.fading_out = False
        self.min = min
        self.max = max
        self.current = None
        self.fadein = FadeIn(min=min, max=max)
        self.fadeout = FadeOut(min=min, max=max)
        self.outro = outro

    def __call__(self):
        if not self.fading_out:
            velocity = self.fadein()
            if velocity == self.max:
                self.fading_out = True
                self._held = 0
        else:
            self._held += 1
            if self._held < self.hold_for_iterations:
                self.current = self.max
                return
            velocity = self.fadeout()
            if velocity == self.min:
                if self.outro:
                    self.outro()
        self.current = velocity
    
