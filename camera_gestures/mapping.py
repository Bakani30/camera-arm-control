"""Relative hand-to-target mapping (M0): metric hand motion moves an end-effector target in robot_base.

Plain logic only, so live runs, replays and tests share it. No robot messages here.
"""
import math
from collections import namedtuple
from dataclasses import dataclass

GRIP_BY_CODE = {'01': 0.0, '10': 1.0}  # palm opens, fist closes; any other code keeps the last grip
DRAG_TARGETS_M = ((.25, -.06, .08), (.30, .08, .12), (.30, -.08, .12), (.22, .06, .07), (.28, -.06, .17))
MapperOutput = namedtuple('MapperOutput', 'position_m grip mode enabled')


@dataclass(frozen=True)
class MappingConfig:
    start_m: tuple = (.25, 0., .12)
    box_min_m: tuple = (.18, -.12, .04)  # x stays past tcp_min_radius of small_arm_v1
    box_max_m: tuple = (.33, .12, .20)
    gain_lateral: float = .5
    gain_depth: float = .2
    depth_deadband_m: float = .015
    tau_lateral_ms: float = 80
    tau_depth_ms: float = 120
    jump_m: float = .15
    max_speed_mps: float = .25
    max_gap_ms: float = 500


class Ema:
    """First-order low-pass until P006 brings One Euro; tau <= 0 passes values through."""

    def __init__(self, tau_ms):
        self.tau_ms = tau_ms
        self.value = None

    def reset(self, value):
        self.value = value

    def update(self, value, dt_ms):
        self.value = value if self.tau_ms <= 0 else self.value+(1-math.exp(-dt_ms/self.tau_ms))*(value-self.value)
        return self.value


def _finite(position_m, z_m):
    return (position_m is not None and z_m is not None
            and all(math.isfinite(v) for v in (*position_m, z_m)))


class RelativeMapper:
    def __init__(self, config=MappingConfig(), filter_factory=Ema):
        self.config = config
        self.filters = (filter_factory(config.tau_lateral_ms), filter_factory(config.tau_lateral_ms),
                        filter_factory(config.tau_depth_ms))
        self.desired = self.emitted = tuple(config.start_m)
        self.grip = 0.0
        self.code = None
        self.reference = None    # last raw hand; None means the next good frame re-anchors
        self.filtered = None
        self.held_z = None
        self.tracking = False
        self.last = None

    def reset(self):
        """Send the target home. The point slides back only while tracking, under the speed cap."""
        self.desired = tuple(self.config.start_m)
        self.reference = None
        self.tracking = False

    def reanchor(self):
        """The C key: take the hand's next frame as the new reference, and leave the point where it is."""
        self._drop()

    def _drop(self):
        if self.tracking:
            self.desired = self.emitted  # A still hand on return must mean a still point.
        self.tracking = False
        self.reference = None

    def _jumped(self, hand):
        previous = self.reference
        return (math.hypot(hand[0]-previous[0], hand[1]-previous[1]) > self.config.jump_m
                or abs(hand[2]-previous[2]) > self.config.jump_m)

    def _anchor(self, hand, code):
        for f, v in zip(self.filters, hand):
            f.reset(v)
        self.filtered = hand
        self.held_z = hand[2]
        self.code = code

    def _move(self, hand, code, dt):
        c = self.config
        now = tuple(f.update(v, dt) for f, v in zip(self.filters, hand))
        # Backlash on position, not per frame: per-frame steps would all fall inside the deadband.
        held = self.held_z
        if abs(now[2]-held) > c.depth_deadband_m:
            held = now[2]-math.copysign(c.depth_deadband_m, now[2]-held)
        step = (-c.gain_depth*(held-self.held_z),
                -c.gain_lateral*(now[0]-self.filtered[0]),
                -c.gain_lateral*(now[1]-self.filtered[1]))
        self.filtered, self.held_z = now, held
        # Clipping the running target leaves no windup past the box edge.
        self.desired = tuple(min(high, max(low, d+s)) for d, s, low, high
                             in zip(self.desired, step, c.box_min_m, c.box_max_m))
        if code != self.code:
            self.code = code
            self.grip = GRIP_BY_CODE.get(code, self.grip)

    def _emit(self, dt):
        gap = [d-e for d, e in zip(self.desired, self.emitted)]
        distance = math.sqrt(sum(v*v for v in gap))
        limit = self.config.max_speed_mps*dt/1000
        scale = 1 if distance <= limit else limit/distance
        self.emitted = self.desired if scale == 1 else tuple(e+scale*v for e, v in zip(self.emitted, gap))

    def update(self, armed, position_m, z_m, active, code, now_ms):
        c = self.config
        dt = 0 if self.last is None else now_ms-self.last
        self.last = now_ms
        if not 0 <= dt <= c.max_gap_ms:
            dt = 0
            self._drop()
        valid = armed and active and _finite(position_m, z_m)
        hand = (*position_m, z_m) if valid else None
        if valid and self.reference is not None and self._jumped(hand):
            valid = False
        if not valid:
            self._drop()
            return MapperOutput(self.emitted, self.grip, 'hold', bool(armed))
        if self.reference is None:
            self._anchor(hand, code)
        else:
            self._move(hand, code, dt)
        self.reference = hand
        self._emit(dt)
        self.tracking = True
        return MapperOutput(self.emitted, self.grip, 'track', True)
