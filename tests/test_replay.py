import math
import unittest
from pathlib import Path
from camera_gestures.control import HandControl
from camera_gestures.pipeline import handle_key, step
from camera_gestures.replay import compare, excerpt, infer_keys, load, replay, replay_file
from camera_gestures.state import GestureOutput

FIXTURES = Path(__file__).resolve().parent / 'fixtures'
NAMES = ('replay_start_loss', 'replay_resume_reanchor', 'replay_reset_key')
EXPECTED_KEYS = {'replay_start_loss': {142: ' ', 223: 'c'}, 'replay_resume_reanchor': {}, 'replay_reset_key': {1113: 'r'}}
# Same code, same float inputs: replay is exact; the bound only absorbs
# platform differences in math.exp and math.hypot, far below one pixel (1/1280).
TOL = 1e-9


def fixture(name):
    return replay_file(FIXTURES / f'{name}.frames.jsonl')


class ReplayTests(unittest.TestCase):
    def test_replay_reproduces_logged_output_and_target(self):
        # Logged 2026-09-18; logic unchanged since, so the log is the golden value.
        for name in NAMES:
            with self.subTest(name):
                records, results = fixture(name)
                self.assertEqual(len(records), len(results))
                self.assertEqual(compare(records, results, TOL, TOL), [])

    def test_hand_loss_gives_00_after_drop_window(self):
        episodes = 0
        for name in NAMES:
            records, results = fixture(name)
            drop_ms = load(FIXTURES / f'{name}.frames.jsonl')[1]['drop_ms']
            held, lost_at = '00', None
            for record, result in zip(records, results):
                if record['hand_present']:
                    held, lost_at = result['output'], None
                    continue
                if lost_at is None:
                    lost_at, episodes = record['receipt_ms'], episodes + (held != '00')
                if held != '00':
                    expected = '00' if record['receipt_ms']-lost_at >= drop_ms else held
                    self.assertEqual(result['output'], expected, (name, record['frame']))
        self.assertGreaterEqual(episodes, 2)

    def test_reanchor_after_return_does_not_jump(self):
        returns, moved = 0, 0
        for name in NAMES:
            records, results = fixture(name)
            last_wrist = None
            for i, result in enumerate(results):
                if records[i]['hand_present']:
                    wrist = records[i]['landmarks'][0]
                if result['control_status'] != 'REANCHORED - ACTIVE':
                    if result['target_active']:
                        last_wrist = wrist
                    continue
                returns += 1
                before, after = results[i-1], results[i+1]
                self.assertEqual(result['screen_target'], before['screen_target'])
                self.assertEqual(result['depth_relative'], before['depth_relative'])
                # First tracked step moves at most as far as the wrist did in one frame.
                step = math.dist(after['screen_target'], result['screen_target'])
                wrist_step = math.dist(records[i+1]['landmarks'][0], records[i]['landmarks'][0])
                self.assertLessEqual(step, wrist_step + TOL)
                if last_wrist is not None and math.dist(wrist, last_wrist) > .05:
                    moved += 1
        self.assertGreaterEqual(returns, 3)
        self.assertGreaterEqual(moved, 1)  # the hand came back somewhere else

    def test_keys_recovered_from_status(self):
        for name in NAMES:
            records, _ = load(FIXTURES / f'{name}.frames.jsonl')
            self.assertEqual(infer_keys(records), EXPECTED_KEYS[name])

    def test_resume_needs_a_no_hand_frame(self):
        records, meta = load(FIXTURES / 'replay_start_loss.frames.jsonl')
        with self.assertRaises(ValueError):
            replay(records, meta['width'], meta['height'], resume=True)

    def test_compare_catches_a_wrong_palm_scale_and_hand_side(self):
        records, results = fixture(NAMES[0])
        changed = [dict(r, palm_scale_px=None if r['palm_scale_px'] is None else r['palm_scale_px'] * 2) for r in results]
        self.assertTrue(any(m[1] == 'palm_scale_px' for m in compare(records, changed, TOL, TOL)))
        changed = [dict(r, assigned_hand='Left') for r in results]
        self.assertTrue(any(m[1] == 'assigned_hand' for m in compare(records, changed, TOL, TOL)))

    def test_excerpt_refuses_an_empty_range(self):
        with self.assertRaises(ValueError):
            excerpt(FIXTURES / f'{NAMES[0]}.frames.jsonl', 900000, 900001, FIXTURES / 'never_written')
        self.assertFalse((FIXTURES / 'never_written.frames.jsonl').exists())


class StepAndKeyTests(unittest.TestCase):
    OBS = dict(hand_present=True, gesture='Open_Palm', score=.9, landmarks=[[.4, .6]] * 21)

    def test_stale_frame_counts_as_no_hand(self):
        state, control = GestureOutput(.7, 0, drop_ms=0), HandControl('Right')
        code, wrist, scale = step(state, control, self.OBS, True, 100, 1280, 720)
        self.assertIsNone(wrist)
        self.assertIsNone(scale)
        self.assertEqual(code, '00')

    def test_fresh_frame_passes_the_wrist_on(self):
        state, control = GestureOutput(.7, 0, drop_ms=0), HandControl('Right')
        _, wrist, _ = step(state, control, self.OBS, False, 100, 1280, 720)
        self.assertEqual(wrist, (.4, .6))

    def test_l_and_h_pick_the_hand_and_restart_the_filter(self):
        control = HandControl('Right')
        self.assertTrue(handle_key('l', control, None, None, 0))
        self.assertEqual(control.side, 'Left')
        self.assertTrue(handle_key('h', control, None, None, 0))
        self.assertEqual(control.side, 'Right')

    def test_other_keys_leave_the_filter_alone(self):
        for key in ('c', 'r', ' ', 'x'):
            self.assertFalse(handle_key(key, HandControl('Right'), None, None, 0), key)

    def test_r_rearms_with_the_wrist_it_is_given(self):
        control = HandControl('Right')
        handle_key('r', control, (.4, .6), 100., 0)
        self.assertEqual(control.target.position, (.5, .5))
        self.assertTrue(control.armed)
        self.assertTrue(control.target.active)

    def test_space_pauses(self):
        control = HandControl('Right')
        control.calibrate((.4, .6), 100., 0)
        self.assertTrue(control.target.active)
        handle_key(' ', control, (.4, .6), 100., 1)
        self.assertFalse(control.target.active)
        self.assertFalse(control.armed)


if __name__ == '__main__':
    unittest.main()
