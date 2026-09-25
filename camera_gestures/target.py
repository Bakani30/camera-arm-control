"""Normalized screen target, independent of robot coordinates."""
import math


class ScreenTarget:
    def __init__(self):
        self.position = (.5, .5)
        self.raw = self.position
        self.origin = None
        self.anchor = self.position
        self.active = False
        self.last = None
        self.hand = None

    def pause(self):
        self.active = False
        self.origin = None

    def calibrate(self, wrist, now, hand):
        if wrist is None or not all(math.isfinite(v) for v in wrist):
            return False
        self.origin = tuple(wrist)
        self.anchor = self.position
        self.raw = self.position
        self.last = now
        self.hand = hand
        self.active = True
        return True

    def update(self, wrist, now, hand):
        valid = wrist is not None and all(math.isfinite(v) for v in wrist)
        if not valid or (self.active and hand != self.hand):
            self.pause()
        if self.last is not None and (now < self.last or now-self.last > 500):
            self.pause()
        dt = max(0, now-self.last) if self.last is not None else 0
        self.last = now
        if self.active:
            self.raw = tuple(max(0., min(1., a + (v-o))) for a,v,o in zip(self.anchor,wrist,self.origin))
            alpha = 1-math.exp(-dt/80.)
            self.position = tuple(p+alpha*(r-p) for p,r in zip(self.position,self.raw))
        return self.position
