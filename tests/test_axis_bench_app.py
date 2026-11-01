"""Runs axis_bench.main end to end with a fake camera, recognizer, clock and keyboard. No hand or camera is real."""
import contextlib
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace as N
from unittest import mock

import cv2
import mediapipe as mp
import numpy as np

from camera_gestures import axis_bench
from camera_gestures.axis_report import read_log, summarize

NEUTRAL = 255
SHORT_TRIALS = (axis_bench.Trial('C', 1, 'tip'), axis_bench.Trial('A_mid', 1, 'hold'))


class FakeCapture:
    opened = True
    size = (1280, 720)

    def __init__(self, *_):
        pass

    def isOpened(self):
        return self.opened

    def set(self, *_):
        return True

    def get(self, prop):
        return {cv2.CAP_PROP_FRAME_WIDTH: self.size[0], cv2.CAP_PROP_FRAME_HEIGHT: self.size[1],
                cv2.CAP_PROP_FPS: 30}.get(prop, 0)

    def read(self):
        frame = np.zeros((720, 1280, 3), np.uint8)
        frame[:, :100] = 255   # lit on the left only, so a flip shows
        return True, frame

    def release(self):
        pass


def hand(x):
    points = [N(x=x, y=.5, z=0.) for _ in range(21)]
    points[0], points[9] = N(x=x, y=.7, z=0.), N(x=x, y=.475, z=0.)
    points[5], points[17] = N(x=x-.036, y=.5, z=0.), N(x=x+.036, y=.5, z=0.)
    return points


class FakeRecognizer:
    def __init__(self, side='Right', two_hands=False):
        self.side, self.two_hands = side, two_hands

    def __enter__(self):
        return self

    def __exit__(self, *_):
        pass

    def recognize_for_video(self, image, _now):
        self.left_pixel = int(image.numpy_view()[0, 0, 0])
        world = [N(x=.01, y=.02, z=.03) for _ in range(21)]
        if self.two_hands:
            return N(hand_landmarks=[hand(.3), hand(.6)], hand_world_landmarks=[world, world],
                     gestures=[[N(category_name='Open_Palm', score=.9)]]*2,
                     handedness=[[N(category_name='Right', score=.99)]]*2)
        return N(hand_landmarks=[hand(.5)], hand_world_landmarks=[world],
                 gestures=[[N(category_name='Closed_Fist', score=.9)]],
                 handedness=[[N(category_name=self.side, score=.99)]])


class BenchApp(unittest.TestCase):
    def run_bench(self, keys, frames=200, recognizer=None, capture=FakeCapture, calibration='cal.json', extra=(),
                  calibration_extra=None, args=None):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        folder = Path(tmp.name)
        (folder/'model.task').write_bytes(b'fake')
        (folder/calibration).write_text(json.dumps(dict(
            focal_px=900., fx_px=900., fy_px=900., cx_px=600., cy_px=360., width=1280, height=720,
            rms_px=.3, views=15, **(calibration_extra or {}))), encoding='utf-8')
        ticks = iter(range(1, frames+1))
        script = dict(keys)
        clock = iter(i*.033 for i in range(100000))

        def wait(_):
            tick = next(ticks)
            return ord('q') if tick == frames else ord(script[tick]) if tick in script else NEUTRAL

        self.texts = []
        cwd = os.getcwd()
        os.chdir(folder)
        self.addCleanup(os.chdir, cwd)
        argv = ['--model', 'model.task', *(args if args is not None else
                ('--calibration', calibration, '--palm-length-m', '.09', '--palm-width-m', '.051')), *extra]
        with mock.patch.object(axis_bench, 'TRIALS', SHORT_TRIALS), mock.patch.object(cv2, 'VideoCapture', capture), \
                mock.patch.object(cv2, 'imshow', lambda *_: None), mock.patch.object(cv2, 'waitKey', wait), \
                mock.patch.object(cv2, 'putText', lambda _frame, text, *_: self.texts.append(text)), \
                mock.patch.object(cv2, 'getWindowProperty', lambda *_: 1), \
                mock.patch.object(cv2, 'destroyAllWindows', lambda: None), \
                mock.patch.object(mp.tasks.vision.GestureRecognizer, 'create_from_options',
                                  lambda _: recognizer or FakeRecognizer()):
            with contextlib.redirect_stdout(io.StringIO()):
                axis_bench.main(argv, clock=lambda: next(clock))
        return next((folder/'logs').glob('*.axis_bench.jsonl')), folder

    def test_a_guided_run_gives_a_report_ready_file(self):
        path, folder = self.run_bench({2: ' ', 70: ' '}, frames=140)
        header, frames, completed = read_log(path)
        self.assertEqual(header['focal_px'], 900.)
        self.assertEqual(header['principal_px'], [680., 360.])    # mirrored, as the frames are
        self.assertEqual(header['palm_length_m'], .09)
        self.assertFalse(header['provisional'])
        self.assertEqual(completed, {'C', 'A_mid'})
        self.assertEqual({f['trial'] for f in frames}, {'C', 'A_mid'})
        self.assertEqual(len(frames[0]['world_landmarks']), 21)
        self.assertEqual(frames[0]['gesture'], 'Closed_Fist')
        self.assertEqual(summarize(header, frames, completed)['trials']['A_mid']['status'], 'ok')
        self.assertEqual(list((folder/'logs').glob('*.ee_target.jsonl')), [])

    def test_each_finished_step_says_at_once_whether_it_counts(self):
        self.run_bench({2: ' ', 70: ' '}, frames=140)
        self.assertTrue(any(t.startswith('Last: C NOT VALID') and 'too little motion' in t and 'R to redo' in t
                            for t in self.texts))
        self.assertIn('Last: A_mid ok', self.texts)

    def test_redoing_a_step_clears_its_old_result(self):
        self.run_bench({2: ' ', 70: 'r'}, frames=75)
        at_redo = len(self.texts)-5*3
        self.assertTrue(any(t.startswith('Last: C') for t in self.texts[:at_redo]))
        self.assertFalse(any(t.startswith('Last: C') for t in self.texts[at_redo:]))

    def test_the_hand_distance_shows_while_waiting_only(self):
        self.run_bench({20: ' '}, frames=40)
        shown = [i for i, t in enumerate(self.texts) if t == 'Hand about 50 cm from camera']
        recording = [i for i, t in enumerate(self.texts) if 'hold open palm' in t]
        self.assertTrue(shown)
        self.assertTrue(recording)
        self.assertLess(max(shown), min(recording))

    def test_only_runs_just_the_named_steps(self):
        path, _ = self.run_bench({2: ' '}, frames=70, extra=('--only', 'A_mid'))
        _, frames, completed = read_log(path)
        self.assertEqual({f['trial'] for f in frames}, {'A_mid'})
        self.assertEqual(completed, {'A_mid'})
        self.assertIn('Step 1/1 A_mid: hold', self.texts)

    def test_only_refuses_a_step_that_does_not_exist(self):
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            self.run_bench({}, frames=3, extra=('--only', 'Z'))

    def test_frames_are_mirrored_as_the_principal_point_assumes(self):
        recognizer = FakeRecognizer()
        self.run_bench({}, frames=3, recognizer=recognizer)
        self.assertEqual(recognizer.left_pixel, 0)

    def test_calibration_warnings_reach_the_header(self):
        path, _ = self.run_bench({}, frames=3, calibration_extra=dict(focal_std_px=50., tilt_max_deg=5.))
        self.assertTrue(read_log(path)[0]['calibration_warnings'])

    def test_no_ruler_and_no_calibration_are_needed(self):
        path, _ = self.run_bench({2: ' ', 70: ' '}, frames=140, args=())
        header, frames, completed = read_log(path)
        self.assertEqual(header['palm_length_m'], .10)
        self.assertIsNone(header['palm_width_m'])
        self.assertFalse(header['palm_measured'])
        self.assertTrue(header['provisional'])
        self.assertEqual(header['focal_px'], 900.)
        self.assertEqual(header['principal_px'], [640., 360.])
        self.assertEqual(summarize(header, frames, completed)['trials']['A_mid']['status'], 'ok')

    def test_ruler_values_are_marked_as_measured(self):
        path, _ = self.run_bench({}, frames=3)
        self.assertTrue(read_log(path)[0]['palm_measured'])

    def test_frames_before_space_are_not_recorded(self):
        path, _ = self.run_bench({20: ' '}, frames=40)
        _, frames, _ = read_log(path)
        self.assertLess(len(frames), 21)

    def test_quit_mid_trial_leaves_a_readable_incomplete_trial(self):
        path, _ = self.run_bench({2: ' '}, frames=10)
        header, frames, completed = read_log(path)
        self.assertEqual(completed, set())
        self.assertEqual(summarize(header, frames, completed)['trials']['C']['status'], 'incomplete')

    def test_retry_keeps_old_frames_out_of_the_result(self):
        path, _ = self.run_bench({2: ' ', 10: 'r', 12: ' '}, frames=80)
        _, frames, completed = read_log(path)
        self.assertIn('C#retry1', {f['trial'] for f in frames})
        self.assertIn('C', completed)

    def test_space_waits_for_the_hand_and_the_screen_says_what_it_sees(self):
        path, _ = self.run_bench({2: ' '}, frames=20, recognizer=FakeRecognizer(side='Left'), extra=('--hand', 'Right'))
        self.assertEqual(read_log(path)[1], [])
        self.assertTrue(any('Right hand not found: sees Left 0.99' in t for t in self.texts))

    def test_either_hand_works_by_default(self):
        for side in ('Left', 'Right'):
            with self.subTest(side):
                path, _ = self.run_bench({2: ' '}, frames=20, recognizer=FakeRecognizer(side=side))
                header, frames, _ = read_log(path)
                self.assertEqual(header['hand'], 'Any')
                self.assertTrue(frames)
                self.assertTrue(all(f['hand_present'] and f['side'] == side for f in frames))

    def test_two_hands_in_view_are_refused(self):
        path, _ = self.run_bench({2: ' '}, frames=20, recognizer=FakeRecognizer(two_hands=True))
        self.assertEqual(read_log(path)[1], [])
        self.assertTrue(any('2 hands in view, keep one: sees Right 0.99, Right 0.99' in t for t in self.texts))

    def test_an_empty_view_is_named_with_its_brightness(self):
        class Empty(FakeRecognizer):
            def recognize_for_video(self, image, _now):
                return N(hand_landmarks=[], hand_world_landmarks=[], gestures=[], handedness=[])
        path, _ = self.run_bench({2: ' '}, frames=20, recognizer=Empty())
        self.assertEqual(read_log(path)[1], [])
        self.assertTrue(any('no hand in view' in t and 'brightness 20/255' in t for t in self.texts))

    def test_a_hand_lost_after_the_start_still_counts_against_the_step(self):
        class Vanishing(FakeRecognizer):
            calls = 0
            def recognize_for_video(self, image, now):
                self.calls += 1
                if self.calls <= 5:
                    return super().recognize_for_video(image, now)
                return N(hand_landmarks=[], hand_world_landmarks=[], gestures=[], handedness=[])
        path, _ = self.run_bench({2: ' '}, frames=70, recognizer=Vanishing())
        header, frames, completed = read_log(path)
        self.assertTrue(frames)
        self.assertEqual(summarize(header, frames, completed)['trials']['C']['status'], 'invalid')

    def test_a_provisional_calibration_is_marked(self):
        path, _ = self.run_bench({}, frames=3, calibration='camera_provisional_f900.json')
        self.assertTrue(read_log(path)[0]['provisional'])

    def test_note_reaches_the_header(self):
        path, _ = self.run_bench({}, frames=3, extra=('--note', 'mac first pass'))
        self.assertEqual(read_log(path)[0]['note'], 'mac first pass')

    def test_a_closed_camera_says_so(self):
        class Closed(FakeCapture):
            opened = False
        with self.assertRaisesRegex(RuntimeError, 'Camera unavailable'):
            self.run_bench({}, frames=3, capture=Closed)

    def test_a_resolution_other_than_the_calibration_is_refused(self):
        class Small(FakeCapture):
            size = (640, 480)
        with self.assertRaisesRegex(ValueError, 'calibration is for 1280x720'):
            self.run_bench({}, frames=3, capture=Small)


if __name__ == '__main__':
    unittest.main()
