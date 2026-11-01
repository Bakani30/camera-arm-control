"""Runs app.main end to end with a fake camera, recognizer and keyboard. No hand or camera is real."""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace as N
from unittest import mock

import cv2
import mediapipe as mp
import numpy as np

from arm_contracts.replay import read_replay
from camera_gestures import app

NEUTRAL = 255


class FakeCapture:
    def __init__(self, *_):
        pass

    def isOpened(self):
        return True

    def set(self, *_):
        return True

    def get(self, prop):
        return {cv2.CAP_PROP_FRAME_WIDTH: 1280, cv2.CAP_PROP_FRAME_HEIGHT: 720, cv2.CAP_PROP_FPS: 30}.get(prop, 0)

    def read(self):
        return True, np.zeros((720, 1280, 3), np.uint8)

    def release(self):
        pass


def hand(x):
    points = [N(x=x, y=.5, z=0.) for _ in range(21)]
    points[0], points[9] = N(x=x, y=.7, z=0.), N(x=x, y=.425, z=0.)  # 198 px palm at 720 high
    points[5], points[17] = N(x=x-.03, y=.45, z=0.), N(x=x+.03, y=.45, z=0.)
    return points


class FakeRecognizer:
    """Hand on every frame, moving right on screen; none on frames listed in missing."""

    def __init__(self, missing=()):
        self.frame = 0
        self.missing = missing

    def __enter__(self):
        return self

    def __exit__(self, *_):
        pass

    def recognize_for_video(self, _image, _now):
        self.frame += 1
        if self.frame in self.missing:
            return N(hand_landmarks=[], gestures=[], handedness=[])
        return N(hand_landmarks=[hand(.4+self.frame*.002)], gestures=[[N(category_name='Open_Palm', score=.9)]],
                 handedness=[[N(category_name='Right', score=.99)]])


class AppMappingTests(unittest.TestCase):
    def run_app(self, *extra, keys=(), frames=30, missing=()):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        folder = Path(tmp.name)
        (folder/'model.task').write_bytes(b'fake')
        (folder/'cal.json').write_text(json.dumps(dict(
            focal_px=900., fx_px=900., fy_px=900., cx_px=640., cy_px=360., width=1280, height=720,
            rms_px=.3, views=15)), encoding='utf-8')
        script = {i: k for i, k in keys}
        ticks = iter(range(1, frames+1))
        windows = set()

        def wait(_):
            tick = next(ticks)
            return ord('q') if tick == frames else ord(script[tick]) if tick in script else NEUTRAL

        argv = ['app', '--calibration', 'cal.json', '--palm-length-m', '.11', '--model', 'model.task', *extra]
        cwd = os.getcwd()
        os.chdir(folder)
        self.addCleanup(os.chdir, cwd)
        with mock.patch.object(sys, 'argv', argv), mock.patch.object(cv2, 'VideoCapture', FakeCapture), \
                mock.patch.object(cv2, 'imshow', lambda name, _: windows.add(name)), \
                mock.patch.object(cv2, 'waitKey', wait), mock.patch.object(cv2, 'getWindowProperty', lambda *_: 1), \
                mock.patch.object(cv2, 'destroyAllWindows', lambda: None), \
                mock.patch.object(mp.tasks.vision.GestureRecognizer, 'create_from_options',
                                  lambda _: FakeRecognizer(missing)):
            app.main()
        return folder/'logs', windows

    def frames(self, logs):
        path = next(logs.glob('*.frames.jsonl'))
        return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]

    def test_tracks_after_c_and_writes_a_readable_replay(self):
        logs, windows = self.run_app('--mapping', 'relative', keys=[(5, 'c')])
        self.assertIn('mock arm', windows)
        header, messages = read_replay(next(logs.glob('*.ee_target.jsonl')))
        self.assertEqual(header['camera'], dict(width=1280, height=720, f_px=900.))
        self.assertIn('palm_length_m=0.11', header['notes'])
        self.assertTrue(all(m.source == 'live' for m in messages))
        self.assertEqual(len(messages), 30)
        self.assertTrue(all(not m.enabled for m in messages[:5]))
        self.assertTrue(all(m.mode == 'track' for m in messages[5:]))
        self.assertLess(messages[-1].position_m[1], 0.)  # right on screen is the robot's right
        self.assertEqual(self.frames(logs)[-1]['mapping_mode'], 'track')

    def test_lost_hand_holds_and_returns_without_a_step(self):
        logs, _ = self.run_app('--mapping', 'relative', keys=[(2, 'c')], missing=(15, 16))
        _, messages = read_replay(next(logs.glob('*.ee_target.jsonl')))
        self.assertEqual([m.mode for m in messages[14:16]], ['hold', 'hold'])
        self.assertEqual(messages[16].mode, 'track')
        self.assertEqual(messages[16].position_m, messages[13].position_m)

    def test_r_key_is_logged_for_recompute(self):
        logs, _ = self.run_app('--mapping', 'relative', keys=[(2, 'c'), (10, 'r')])
        self.assertEqual([i for i, r in enumerate(self.frames(logs)) if r['mapping_reset']], [10])

    def test_quit_before_tracking_leaves_a_readable_file(self):
        logs, _ = self.run_app('--mapping', 'relative', frames=1)
        _, messages = read_replay(next(logs.glob('*.ee_target.jsonl')))
        self.assertFalse(messages[0].enabled)

    def test_without_the_flag_nothing_changes(self):
        logs, windows = self.run_app(keys=[(2, 'c')], frames=5)
        self.assertNotIn('mock arm', windows)
        self.assertEqual(list(logs.glob('*.ee_target.jsonl')), [])
        self.assertNotIn('mapping_mode', self.frames(logs)[-1])


if __name__ == '__main__':
    unittest.main()
