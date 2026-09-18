"""Pure gesture-to-code mapping with conservative stabilization."""
import math


class GestureOutput:
    def __init__(self, threshold=0.7, dwell_ms=250, max_gap_ms=500):
        if not 0 <= threshold <= 1 or dwell_ms < 0 or max_gap_ms <= 0:
            raise ValueError('Invalid threshold or timing')
        self.threshold = threshold
        self.dwell_ms = dwell_ms
        self.max_gap_ms = max_gap_ms
        self.candidate = '00'
        self.since = 0
        self.last = None

    def update(self, gesture, score, now_ms):
        if self.last is not None and (now_ms < self.last or now_ms-self.last > self.max_gap_ms):
            self.candidate = '00'
        self.last = now_ms
        code = {'Open_Palm': '01', 'Closed_Fist': '10'}.get(gesture, '00')
        if not math.isfinite(score) or score < self.threshold:
            code = '00'
        if code != self.candidate:
            self.candidate, self.since = code, now_ms
        if code == '00' or now_ms-self.since < self.dwell_ms:
            return '00'
        return code
