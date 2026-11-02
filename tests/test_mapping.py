import math
import unittest

from camera_gestures.mapping import DRAG_TARGETS_M, Ema, MappingConfig, RelativeMapper

FAST = MappingConfig(tau_lateral_ms=0, tau_depth_ms=0, max_speed_mps=100.)
RAW = MappingConfig(tau_lateral_ms=0, tau_depth_ms=0)  # no filter, default speed cap
HAND = (0., 0., .5)


def run(mapper, frames, start=0, dt=33):
    """frames: (x, y, z) in metres, or None for a frame with no usable hand."""
    out = None
    for i, f in enumerate(frames):
        pos, z = (f[:2], f[2]) if f else ((0., 0.), None)
        out = mapper.update(True, pos, z, f is not None, '00', start + i * dt)
    return out


def distance(a, b):
    return math.dist(a, b)


class AxisTests(unittest.TestCase):
    def assertPosition(self, got, want):
        for g, w in zip(got, want):
            self.assertAlmostEqual(g, w, places=9)

    def test_axes_and_gain(self):
        self.assertPosition(run(RelativeMapper(FAST), [HAND, (.04, 0., .5)]).position_m, (.25, -.02, .12))
        self.assertPosition(run(RelativeMapper(FAST), [HAND, (0., .04, .5)]).position_m, (.25, 0., .10))
        self.assertPosition(run(RelativeMapper(FAST), [HAND, (0., 0., .555)]).position_m, (.242, 0., .12))

    def test_toward_camera_moves_forward(self):
        out = run(RelativeMapper(FAST), [HAND, (0., 0., .4)])
        self.assertAlmostEqual(out.position_m[0], .25 + .2 * (.1 - .015))


class ReanchorTests(unittest.TestCase):
    def test_first_frame_after_loss_does_not_move(self):
        m = RelativeMapper(FAST)
        moved = run(m, [HAND, (.04, .02, .5)])
        run(m, [None], start=66)
        back = run(m, [(.3, .3, .7)], start=99)
        self.assertEqual(back.position_m, moved.position_m)
        self.assertEqual(back.mode, 'track')

    def test_gap_reanchors_even_when_active(self):
        m = RelativeMapper(FAST)
        moved = run(m, [HAND, (.04, 0., .5)])
        back = m.update(True, (.04, 0.), .6, True, '00', 33 + 900)
        self.assertEqual(back.position_m, moved.position_m)
        self.assertEqual(back.mode, 'track')
        still = m.update(True, (.04, 0.), .6, True, '00', 33 + 933)
        self.assertEqual(still.position_m, moved.position_m)

    def test_reanchor_drops_lag_while_tracking(self):
        m = RelativeMapper(RAW)
        lagging = run(m, [HAND, (.14, 0., .5)])
        m.reanchor()
        still = [run(m, [(.14, 0., .5)], start=66 + i * 33) for i in range(5)]
        self.assertTrue(all(o.position_m == lagging.position_m and o.mode == 'track' for o in still))

    def test_reanchor_keeps_following_after_it(self):
        m = RelativeMapper(FAST)
        moved = run(m, [HAND, (.04, 0., .5)])
        m.reanchor()
        run(m, [(.3, .3, .5)], start=66)
        after = run(m, [(.34, .3, .5)], start=99)
        self.assertAlmostEqual(after.position_m[1], moved.position_m[1] - .02)

    def test_lag_is_dropped_on_loss(self):
        m = RelativeMapper(RAW)
        lagging = run(m, [HAND, (.14, 0., .5)])
        run(m, [None], start=66)
        still = [run(m, [(.5, .5, .6)], start=99 + i * 33).position_m for i in range(10)]
        self.assertTrue(all(p == lagging.position_m for p in still))

    def test_first_frame_after_a_long_pause_cannot_step(self):
        m = RelativeMapper(RAW)
        run(m, [HAND, (.14, 0., .5)])
        m.reset()
        before = m.update(True, (0., 0.), .5, False, '00', 66).position_m
        after = m.update(True, (0., 0.), .5, True, '00', 66 + 900).position_m
        self.assertEqual(before, after)


class LimitTests(unittest.TestCase):
    def test_clamp_has_no_windup(self):
        m = RelativeMapper(FAST)
        hand = [(i * .1, 0., .5) for i in range(5)]
        edge = run(m, hand)
        self.assertAlmostEqual(edge.position_m[1], -.12)
        back = run(m, [(.39, 0., .5)], start=5 * 33)
        self.assertAlmostEqual(back.position_m[1], -.115)

    def test_corner_noise_stays_in_box(self):
        c = MappingConfig(tau_lateral_ms=0, tau_depth_ms=0, max_speed_mps=100.)
        m = RelativeMapper(c)
        run(m, [(i * .1, i * .1, .5) for i in range(5)])
        seen = [run(m, [(.4 + .002 * (-1) ** i, .4 + .002 * (-1) ** i, .5)], start=165 + i * 33).position_m
                for i in range(100)]
        for p in seen:
            for v, low, high in zip(p, c.box_min_m, c.box_max_m):
                self.assertTrue(low <= v <= high, p)
        self.assertLessEqual(max(p[1] for p in seen) - min(p[1] for p in seen), .002 + 1e-9)

    def test_speed_cap(self):
        for dt in (33, 100):
            m = RelativeMapper(RAW)
            run(m, [HAND], dt=dt)
            last = (.25, 0., .12)
            for i in range(1, 6):
                now = run(m, [(.14 * i, 0., .5)], start=i * dt).position_m
                self.assertLessEqual(distance(now, last), .25 * dt / 1000 + 1e-9)
                last = now
            self.assertLess(last[1], 0.)

    def test_low_frame_rate_tracks(self):
        m = RelativeMapper(RAW)
        outs = [m.update(True, (.05 * i, 0.), .5, True, '00', i * 100) for i in range(6)]
        self.assertTrue(all(o.mode == 'track' for o in outs))
        self.assertLess(outs[-1].position_m[1], 0.)

    def test_jump_frame_holds(self):
        for jump in ((.2, 0., .5), (0., 0., .7)):
            m = RelativeMapper(FAST)
            before = run(m, [HAND])
            bad = m.update(True, jump[:2], jump[2], True, '00', 33)
            self.assertEqual((bad.mode, bad.position_m), ('hold', before.position_m))
            next_frame = m.update(True, jump[:2], jump[2], True, '00', 66)
            self.assertEqual((next_frame.mode, next_frame.position_m), ('track', before.position_m))

    def test_invalid_values_hold(self):
        for pos, z in (((math.nan, 0.), .5), ((0., math.inf), .5), ((0., 0.), None), ((0., 0.), math.nan), (None, .5)):
            m = RelativeMapper(FAST)
            run(m, [HAND])
            self.assertEqual(m.update(True, pos, z, True, '00', 33).mode, 'hold')


class DepthTests(unittest.TestCase):
    def test_slow_depth_motion_passes_deadband(self):
        out = run(RelativeMapper(FAST), [(0., 0., .5 + i * .001) for i in range(101)])
        self.assertAlmostEqual(out.position_m[0], .25 - .2 * (.1 - .015), places=6)

    def test_small_depth_noise_is_ignored(self):
        out = run(RelativeMapper(FAST), [(0., 0., .5 + .007 * (-1) ** i) for i in range(20)])
        self.assertEqual(out.position_m[0], .25)

    def test_depth_deadband_does_not_jump(self):
        m = RelativeMapper(FAST)
        zs = [.5 + i * .01 for i in range(6)] + [.55 - i * .01 for i in range(6)]
        last, previous = (.25, 0., .12), zs[0]
        for i, z in enumerate(zs):
            now = run(m, [(0., 0., z)], start=i * 33).position_m
            self.assertLessEqual(abs(now[0] - last[0]), .2 * abs(z - previous) + 1e-9)
            last, previous = now, z


class StateTests(unittest.TestCase):
    def test_not_armed_is_disabled(self):
        out = RelativeMapper(FAST).update(False, (0., 0.), .5, True, '00', 0)
        self.assertEqual((out.enabled, out.mode, out.position_m), (False, 'hold', (.25, 0., .12)))

    def test_lost_hand_while_armed_holds_enabled(self):
        out = run(RelativeMapper(FAST), [None])
        self.assertEqual((out.enabled, out.mode), (True, 'hold'))

    def test_reset_during_pause_moves_only_on_track(self):
        m = RelativeMapper(RAW)
        out = run(m, [HAND] + [(.1 * i, 0., .5) for i in range(1, 4)])
        run(m, [None], start=132)
        m.reset()
        paused = run(m, [None], start=165)
        self.assertEqual(paused.position_m, out.position_m)
        first = run(m, [HAND], start=198)
        self.assertEqual(first.mode, 'track')
        self.assertGreater(first.position_m[1], out.position_m[1])
        self.assertLessEqual(distance(first.position_m, out.position_m), .25 * .033 + 1e-9)

    def test_grip_holds_outside_tracking(self):
        m = RelativeMapper(FAST)
        step = lambda code, active, t: m.update(True, (0., 0.), .5, active, code, t).grip
        self.assertEqual(step('01', True, 0), 0.)
        self.assertEqual(step('10', True, 33), 1.)
        self.assertEqual(step('10', False, 66), 1.)
        self.assertEqual(step('01', False, 99), 1.)
        self.assertEqual(step('01', True, 132), 1.)
        self.assertEqual(step('01', True, 165), 1.)
        self.assertEqual(step('10', True, 198), 1.)
        self.assertEqual(step('01', True, 231), 0.)

    def test_ema_is_swappable(self):
        calls = []

        class Recording(Ema):
            def __init__(self, tau_ms):
                super().__init__(tau_ms)
                calls.append(('new', tau_ms))

            def reset(self, value):
                calls.append(('reset', self.tau_ms))
                super().reset(value)

        run(RelativeMapper(filter_factory=Recording), [HAND])
        self.assertEqual(sorted(c for c in calls if c[0] == 'new'), [('new', 80), ('new', 80), ('new', 120)])
        self.assertEqual(sorted(c for c in calls if c[0] == 'reset'), [('reset', 80), ('reset', 80), ('reset', 120)])

    def test_ema_smooths_with_time_constant(self):
        f = Ema(80)
        f.reset(0.)
        self.assertAlmostEqual(f.update(1., 80), 1 - math.exp(-1))

    def test_zero_tau_passes_through(self):
        f = Ema(0)
        f.reset(0.)
        self.assertEqual(f.update(1., 33), 1.)

    def test_same_frames_same_output(self):
        frames = [(i * .01, -i * .005, .5 + i * .002) for i in range(30)] + [None] + [(.1, .1, .6)] * 5
        self.assertEqual(run(RelativeMapper(), frames), run(RelativeMapper(), frames))

    def test_defaults_match_the_spec(self):
        c = MappingConfig()
        self.assertEqual((c.gain_lateral, c.gain_depth, c.depth_deadband_m, c.tau_lateral_ms, c.tau_depth_ms,
                          c.jump_m, c.max_speed_mps, c.max_gap_ms), (.5, .2, .015, 80, 120, .15, .25, 500))
        self.assertEqual((c.start_m, c.box_min_m, c.box_max_m), ((.25, 0., .12), (.18, -.12, .04), (.33, .12, .20)))

    def test_drag_targets_stay_in_the_box(self):
        c = MappingConfig()
        self.assertEqual(len(DRAG_TARGETS_M), 5)
        for p in DRAG_TARGETS_M:  # A target at the start point would count as reached at once.
            self.assertGreater(distance(p, c.start_m), .03, p)
        for p in DRAG_TARGETS_M:
            for v, low, high in zip(p, c.box_min_m, c.box_max_m):
                self.assertTrue(low <= v <= high, p)


if __name__ == '__main__':
    unittest.main()
