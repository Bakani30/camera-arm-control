import math
import unittest
from pathlib import Path
from camera_gestures.replay import compare, infer_keys, load, replay, replay_file

FIXTURES = Path(__file__).resolve().parent / 'fixtures'
NAMES = ('replay_start_loss', 'replay_resume_reanchor')
# Same code, same float inputs: replay is exact; the bound only absorbs
# platform float formatting, far below one pixel (1/1280).
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
            records, meta = load(FIXTURES / f'{name}.frames.jsonl')
            self.assertEqual(infer_keys(records), {f: k for f, k in meta['keys']})

    def test_resume_needs_a_no_hand_frame(self):
        records, meta = load(FIXTURES / 'replay_start_loss.frames.jsonl')
        with self.assertRaises(ValueError):
            replay(records, meta['width'], meta['height'], resume=True)


if __name__ == '__main__':
    unittest.main()
