"""One-person, selected-side control with atomic XYZ re-anchoring."""
import math
from .target import ScreenTarget
from .depth import RelativeDepth


class HandControl:
    def __init__(self, side='Right', metric=None):
        self.side = side
        self.metric = metric
        self.target = ScreenTarget()
        self.depth = RelativeDepth()
        self.armed = False
        self.status = 'PRESS C TO START'
        self.last = None

    def pause(self):
        self.armed = False
        self.target.pause()
        self.depth.pause()
        self._pause_metric()
        self.status = 'MANUAL PAUSE - C TO RESUME'

    def select(self, side):
        self.pause()
        self.side = side
        self.status = 'HAND CHANGED - PRESS C'

    def reset(self):
        self.target = ScreenTarget()
        self.depth = RelativeDepth()
        if self.metric is not None:
            self.metric.reset()
        self.armed = True
        self.status = 'WAITING FOR ASSIGNED HAND'

    def _pause_metric(self):
        if self.metric is not None:
            self.metric.pause()

    def update(self, wrist, scale, now, palm=None):
        valid = (wrist is not None and len(wrist)==2
                 and all(math.isfinite(v) and 0 <= v <= 1 for v in wrist)
                 and scale is not None and math.isfinite(scale) and scale > 0)
        gap = self.last is not None and not 0 <= now-self.last <= 500
        self.last = now
        if not valid or gap:
            self.target.pause()
            self.depth.pause()
            self._pause_metric()
        if not self.armed:
            return
        if not valid:
            self.status = 'WAITING FOR ASSIGNED HAND'
            return
        if self.metric is not None:
            self.metric.update(palm)
        if not self.target.active or not self.depth.active:
            # Rebase input at the FIRST valid returning frame. Preserve output.
            self.target.calibrate(wrist, now, self.side)
            self.depth.calibrate(scale, now, self.side)
            self.status = 'REANCHORED - ACTIVE'
            return
        self.target.update(wrist,now,self.side)
        self.depth.update(scale,now,self.side,True)
        self.status = 'ACTIVE'

    def calibrate(self, wrist, scale, now):
        self.target.pause()
        self.depth.pause()
        self._pause_metric()
        self.armed = True
        self.update(wrist,scale,now)
