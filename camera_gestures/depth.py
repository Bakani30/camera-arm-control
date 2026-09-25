"""Relative depth proxy from palm image scale; not metric depth."""
import math


def palm_scale(points, width, height):
    if len(points) != 21 or width <= 0 or height <= 0:
        return None
    # Palm bases, not fingertips: reduces direct dependence on finger opening.
    palm = [points[i] for i in (0, 5, 9, 17)]
    if any(len(p) < 2 or not all(math.isfinite(v) and 0 <= v <= 1 for v in p[:2]) for p in palm):
        return None
    def distance(a, b):
        return math.hypot((points[a][0]-points[b][0])*width,
                          (points[a][1]-points[b][1])*height)
    across, length = distance(5,17), distance(0,9)
    if min(across,length) < 5:  # Pixel degeneracy guard, not calibrated reliability.
        return None
    return math.sqrt(across*length)


class RelativeDepth:
    def __init__(self):
        self.value = self.raw = self.anchor = 0.0
        self.reference = None
        self.active = False
        self.last = None
        self.hand = None

    def pause(self):
        self.active = False

    def calibrate(self, scale, now, hand):
        if scale is None or not math.isfinite(scale) or scale <= 0:
            self.pause()
            return False
        self.reference = scale
        self.anchor = self.value
        self.raw = self.value
        self.last = now
        self.hand = hand
        self.active = True
        return True

    def update(self, scale, now, hand, enabled):
        if (not enabled or scale is None or not math.isfinite(scale) or scale <= 0
                or (self.active and hand != self.hand)
                or (self.last is not None and not 0 <= now-self.last <= 500)):
            self.pause()
        dt = max(0, now-self.last) if self.last is not None else 0
        self.last = now
        if self.active:
            self.raw = max(-1.,min(1., self.anchor+1-self.reference/scale))
            alpha = 1-math.exp(-dt/120.)
            self.value += alpha*(self.raw-self.value)
        return self.value
