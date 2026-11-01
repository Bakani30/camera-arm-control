import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from arm_contracts.messages import EndEffectorTarget
from arm_contracts.replay import write_replay
from camera_gestures.mapping_report import main, target_times, track_segments

A, B = (.20, 0., .10), (.30, 0., .10)


def message(seq, t_ms, position=A, mode='track'):
    return EndEffectorTarget(t_ms=t_ms, seq=seq, robot_id='small_arm', position_m=position, grip=0., mode=mode, enabled=True)


def stream(*steps):
    return [message(i+1, t, p, m) for i, (t, p, m) in enumerate(steps)]


class SegmentTests(unittest.TestCase):
    def test_segments_split_on_hold(self):
        got = track_segments(stream((0, A, 'track'), (100, (.21, 0., .10), 'track'), (200, (.23, 0., .10), 'track'),
                                    (300, (.23, 0., .10), 'hold'),
                                    (400, A, 'track'), (500, (.20, .05, .10), 'track')))
        self.assertEqual(len(got), 2)
        self.assertAlmostEqual(got[0]['net_m'][0], .03)
        self.assertAlmostEqual(got[0]['seconds'], .2)
        self.assertAlmostEqual(got[1]['net_m'][1], .05)

    def test_std_of_a_still_segment_is_zero(self):
        got = track_segments(stream(*[(i*33, A, 'track') for i in range(10)]))
        self.assertEqual(got[0]['std_mm'], (0., 0., 0.))

    def test_std_is_in_millimetres(self):
        got = track_segments(stream((0, (.2, 0., .1), 'track'), (33, (.202, 0., .1), 'track')))
        self.assertAlmostEqual(got[0]['std_mm'][0], 1.)

    def test_no_tracking_means_no_segments(self):
        self.assertEqual(track_segments(stream((0, A, 'hold'))), [])


class TargetTests(unittest.TestCase):
    def test_target_needs_the_full_dwell(self):
        short = stream(*[(t, A, 'track') for t in range(0, 901, 100)])
        self.assertEqual(target_times(short, [A]), [None])
        full = stream(*[(t, A, 'track') for t in range(0, 1001, 100)])
        self.assertEqual(target_times(full, [A]), [1.])

    def test_target_not_reached_is_none(self):
        self.assertEqual(target_times(stream((0, B, 'track'), (2000, B, 'track')), [A, B]), [None, None])

    def test_leaving_the_radius_restarts_the_dwell(self):
        got = target_times(stream((0, A, 'track'), (600, B, 'track'), (700, A, 'track'), (1700, A, 'track')), [A])
        self.assertEqual(got, [1.7])

    def test_hold_does_not_count_as_dwell(self):
        got = target_times(stream((0, A, 'track'), (500, A, 'hold'), (1000, A, 'hold'), (1100, A, 'track')), [A])
        self.assertEqual(got, [None])

    def test_each_target_times_from_the_previous_one(self):
        got = target_times(stream((0, A, 'track'), (1000, A, 'track'), (3000, B, 'track'), (4000, B, 'track')), [A, B])
        self.assertEqual(got, [1., 3.])


class CliTests(unittest.TestCase):
    def test_cli_reads_a_replay_file(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'run.ee_target.jsonl'
            write_replay(path, 'ee_target', stream((0, A, 'track'), (33, A, 'track')))
            printed = io.StringIO()
            with contextlib.redirect_stdout(printed):
                self.assertEqual(main([str(path), '--targets']), 0)
            self.assertIn('segment 1', printed.getvalue())
            self.assertIn('target 5: not reached', printed.getvalue())


if __name__ == '__main__':
    unittest.main()
