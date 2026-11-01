import json
import math
import tempfile
import unittest
from pathlib import Path
import cv2
import numpy as np
from camera_gestures.calibration import CameraCalibration, calibrate_views, load_calibration
from camera_gestures.control import HandControl
from camera_gestures.metric import MetricHand, palm_center_px, palm_length_px, palm_measure
from camera_gestures.pipeline import step
from camera_gestures.replay import compare, excerpt, replay, replay_file
from camera_gestures.state import GestureOutput

F = 800.0
WIDTH, HEIGHT = 1280, 720
PALM_M = .09
BASE_IDS = (0, 5, 9, 17)
CENTER = (WIDTH/2, HEIGHT/2)


def hand(x_m, y_m, z_m, f=F, width=WIDTH, height=HEIGHT, tilt=0.):
    """Project a 9 cm palm at camera-frame metres to MediaPipe-style normalized points."""
    half_width = PALM_M/2
    # Palm plane rotated about the image x axis; wrist below, knuckles above.
    local = {0: (0, PALM_M/2, 0), 9: (0, -PALM_M/2, 0), 5: (-half_width, -PALM_M/2, 0), 17: (half_width, -PALM_M/2, 0)}
    points = [[.5, .5, 0.] for _ in range(21)]
    for i, (dx, dy, dz) in local.items():
        ry = dy*math.cos(tilt)-dz*math.sin(tilt)
        rz = dy*math.sin(tilt)+dz*math.cos(tilt)
        u = width/2+f*(x_m+dx)/z_m
        v = height/2+f*(y_m+ry)/z_m
        # MediaPipe scales z like x: normalized by image width.
        points[i] = [u/width, v/height, f*rz/z_m/width]
    return points


def measure(points, width=WIDTH, height=HEIGHT):
    return palm_measure(points, width, height)


class PalmMeasureTests(unittest.TestCase):
    def test_center_is_the_mean_of_the_palm_base_points_in_pixels(self):
        points = [[.5, .5, 0.] for _ in range(21)]
        for i, xy in zip(BASE_IDS, ((.1, .8), (.2, .4), (.3, .4), (.4, .4))):
            points[i] = [*xy, 0.]
        self.assertEqual(palm_center_px(points, 1000, 500), (250., 250.))

    def test_wrist_jitter_moves_the_center_by_a_quarter(self):
        before, after = hand(0, 0, .5), hand(0, 0, .5)
        after[0][0] += .01
        moved = palm_center_px(after, WIDTH, HEIGHT)[0]-palm_center_px(before, WIDTH, HEIGHT)[0]
        self.assertAlmostEqual(moved, .01*WIDTH/4)

    def test_fingertips_do_not_change_the_measure(self):
        points = hand(0, 0, .5)
        base = measure(points)
        points[8] = [.1, .1, -.2]
        self.assertEqual(measure(points), base)

    def test_tilted_palm_keeps_its_length_with_z_landmarks(self):
        flat = palm_length_px(hand(0, 0, .5), WIDTH, HEIGHT)
        tilted = hand(0, 0, .5, tilt=math.radians(45))
        self.assertAlmostEqual(palm_length_px(tilted, WIDTH, HEIGHT), flat, places=6)
        projected = [p[:2] for p in tilted]
        self.assertLess(palm_length_px(projected, WIDTH, HEIGHT), flat*.8)

    def test_invalid_points_give_no_measure(self):
        self.assertIsNone(measure([]))
        broken = hand(0, 0, .5)
        broken[9] = [math.nan, .5, 0.]
        self.assertIsNone(measure(broken))
        outside = hand(0, 0, .5)
        outside[5] = [1.2, .5, 0.]
        self.assertIsNone(measure(outside))
        self.assertIsNone(measure(hand(0, 0, .5), 0, HEIGHT))

    def test_palm_pointing_at_the_camera_gives_no_measure(self):
        # Under 5 px of projected length the z landmark alone would set the scale.
        self.assertIsNone(measure(hand(0, 0, .5, tilt=math.radians(89.9))))


class MetricHandTests(unittest.TestCase):
    def tracked(self, *frames, f=F, width=WIDTH, height=HEIGHT):
        metric = MetricHand(f, PALM_M, (width/2, height/2))
        for frame in frames:
            metric.update(palm_measure(frame, width, height))
        return metric

    def test_z_comes_from_focal_length_and_palm_length(self):
        for z in (.3, .5, .8):
            self.assertAlmostEqual(self.tracked(hand(0, 0, z)).z_m, z, places=6)

    def test_five_cm_move_reads_the_same_at_every_distance(self):
        for z in (.3, .5, .8):
            with self.subTest(z=z):
                metric = self.tracked(hand(0, 0, z), hand(.05, 0, z))
                self.assertAlmostEqual(metric.position_m[0], .05, places=6)
                self.assertAlmostEqual(metric.position_m[1], 0., places=6)

    def test_aspect_ratio_does_not_favor_x_or_y(self):
        for width, height in ((1280, 720), (640, 480)):
            with self.subTest(width=width):
                dx = self.tracked(hand(0, 0, .5, width=width, height=height),
                                  hand(.05, 0, .5, width=width, height=height),
                                  width=width, height=height).position_m[0]
                dy = self.tracked(hand(0, 0, .5, width=width, height=height),
                                  hand(0, .05, .5, width=width, height=height),
                                  width=width, height=height).position_m[1]
                self.assertAlmostEqual(dx, dy, places=6)
                self.assertAlmostEqual(dx, .05, places=6)

    def test_moving_toward_the_camera_adds_no_xy_anywhere_in_the_frame(self):
        for x, y in ((0, 0), (.15, -.08), (-.12, .05)):
            with self.subTest(x=x, y=y):
                metric = self.tracked(hand(x, y, .8), hand(x, y, .6), hand(x, y, .4))
                self.assertAlmostEqual(metric.position_m[0], 0., places=6)
                self.assertAlmostEqual(metric.position_m[1], 0., places=6)

    def test_tilting_in_place_does_not_change_z(self):
        metric = self.tracked(hand(0, 0, .5), hand(0, 0, .5, tilt=math.radians(40)))
        self.assertAlmostEqual(metric.z_m, .5, places=6)

    def test_pause_holds_the_position_and_return_does_not_jump(self):
        metric = self.tracked(hand(0, 0, .5), hand(.05, 0, .5))
        metric.update(None)
        self.assertFalse(metric.active)
        self.assertAlmostEqual(metric.position_m[0], .05, places=6)
        metric.update(measure(hand(.2, .1, .5)))
        self.assertTrue(metric.active)
        self.assertAlmostEqual(metric.position_m[0], .05, places=6)
        self.assertAlmostEqual(metric.position_m[1], 0., places=6)
        metric.update(measure(hand(.21, .1, .5)))
        self.assertAlmostEqual(metric.position_m[0], .06, places=6)

    def test_rejects_settings_that_cannot_give_metres(self):
        for f, length in ((0, PALM_M), (F, 0), (math.nan, PALM_M), (F, math.inf), (-F, PALM_M)):
            with self.subTest(f=f, length=length), self.assertRaises(ValueError):
                MetricHand(f, length, CENTER)


class ControlIntegrationTests(unittest.TestCase):
    def run_frames(self, control, frames):
        state = GestureOutput(.7, 250)
        for i, points in enumerate(frames):
            present = points is not None
            observation = dict(hand_present=present, gesture='Open_Palm' if present else 'No_hand',
                               score=1. if present else 0., landmarks=points or [])
            step(state, control, observation, False, i*33, WIDTH, HEIGHT)

    def test_step_feeds_metric_only_while_armed(self):
        control = HandControl('Right', metric=MetricHand(F, PALM_M, CENTER))
        self.run_frames(control, [hand(0, 0, .5), hand(.05, 0, .5)])
        self.assertEqual(control.metric.position_m, (0., 0.))
        self.assertFalse(control.metric.active)

    def test_step_moves_metric_after_arming(self):
        control = HandControl('Right', metric=MetricHand(F, PALM_M, CENTER))
        control.armed = True
        self.run_frames(control, [hand(0, 0, .5), hand(.05, 0, .5)])
        self.assertAlmostEqual(control.metric.position_m[0], .05, places=6)

    def test_lost_hand_pauses_metric_with_the_screen_target(self):
        control = HandControl('Right', metric=MetricHand(F, PALM_M, CENTER))
        control.armed = True
        self.run_frames(control, [hand(0, 0, .5), hand(.05, 0, .5), None])
        self.assertFalse(control.metric.active)
        self.assertFalse(control.target.active)
        self.assertAlmostEqual(control.metric.position_m[0], .05, places=6)

    def test_time_gap_rebases_metric(self):
        control = HandControl('Right', metric=MetricHand(F, PALM_M, CENTER))
        control.armed = True
        state = GestureOutput(.7, 250)
        for now, points in ((0, hand(0, 0, .5)), (33, hand(.05, 0, .5)), (900, hand(.2, 0, .5))):
            observation = dict(hand_present=True, gesture='Open_Palm', score=1., landmarks=points)
            step(state, control, observation, False, now, WIDTH, HEIGHT)
        self.assertAlmostEqual(control.metric.position_m[0], .05, places=6)

    def test_manual_pause_stops_metric(self):
        control = HandControl('Right', metric=MetricHand(F, PALM_M, CENTER))
        control.armed = True
        self.run_frames(control, [hand(0, 0, .5)])
        control.pause()
        self.assertFalse(control.metric.active)

    def test_reset_returns_metric_to_zero(self):
        control = HandControl('Right', metric=MetricHand(F, PALM_M, CENTER))
        control.armed = True
        self.run_frames(control, [hand(0, 0, .5), hand(.05, 0, .5)])
        control.reset()
        self.assertEqual(control.metric.position_m, (0., 0.))
        self.assertTrue(control.armed)

    def test_calibrate_key_holds_metric_position(self):
        control = HandControl('Right', metric=MetricHand(F, PALM_M, CENTER))
        control.armed = True
        self.run_frames(control, [hand(0, 0, .5), hand(.05, 0, .5)])
        control.calibrate(tuple(hand(.05, 0, .5)[0][:2]), 100., 70)
        self.assertAlmostEqual(control.metric.position_m[0], .05, places=6)
        self.assertFalse(control.metric.active)

    def test_without_metric_control_is_unchanged(self):
        control = HandControl('Right')
        control.armed = True
        self.run_frames(control, [hand(0, 0, .5), hand(.05, 0, .5)])
        self.assertIsNone(control.metric)
        self.assertEqual(control.status, 'ACTIVE')


class ReplayMetricTests(unittest.TestCase):
    def logged(self):
        """A log as the app would write it: inputs plus the metric outputs of one run."""
        inputs = [dict(frame=i+1, receipt_ms=i*33, stale=False, hand_present=True, handedness='Right',
                       gesture='Open_Palm', score=1., landmarks=hand(i*.01, 0, .5, tilt=i*.1)) for i in range(5)]
        settings = dict(width=WIDTH, height=HEIGHT, focal_px=F, palm_length_m=PALM_M, principal_px=CENTER, keys={1: 'c'})
        results = replay(inputs, **settings)
        records = [{**r, **{k: list(v) if isinstance(v, tuple) else v for k, v in out.items()}}
                   for r, out in zip(inputs, results)]
        return records, settings

    def test_replay_reproduces_logged_metric(self):
        records, settings = self.logged()
        self.assertAlmostEqual(records[-1]['metric_position_m'][0], .03, places=6)
        self.assertEqual(compare(records, replay(records, **settings)), [])

    def test_compare_reports_a_metric_departure(self):
        records, settings = self.logged()
        results = replay(records, **settings)
        records[3]['metric_z_m'] += .01
        self.assertEqual([m[:2] for m in compare(records, results)], [(4, 'metric_z_m')])

    def test_compare_reports_a_metric_active_departure(self):
        records, settings = self.logged()
        results = replay(records, **settings)
        records[3]['metric_active'] = False
        self.assertEqual([m[:2] for m in compare(records, results)], [(4, 'metric_active')])

    def test_excerpt_keeps_z_and_settings_for_a_metric_log(self):
        records, settings = self.logged()
        meta = dict(width=WIDTH, height=HEIGHT, threshold=.7, dwell_ms=250, drop_ms=250, assigned_hand='Right',
                    classifier='mediapipe', mediapipe='test', mirrored=True, focal_px=F, palm_length_m=PALM_M, principal_px=list(CENTER))
        with tempfile.TemporaryDirectory() as folder:
            log = Path(folder)/'run.frames.jsonl'
            log.write_text(''.join(json.dumps(r)+'\n' for r in records), encoding='utf-8')
            log.with_name('run.json').write_text(json.dumps(meta), encoding='utf-8')
            excerpt(log, 1, 5, Path(folder)/'cut')
            cut, replayed = replay_file(Path(folder)/'cut.frames.jsonl')
        self.assertEqual(len(cut[0]['landmarks'][0]), 3)
        self.assertEqual(cut[0]['metric_active'], replayed[0]['metric_active'])
        self.assertAlmostEqual(replayed[-1]['metric_z_m'], .5, places=6)


TILTED = ((.3, 0, .5), (-.3, .2, .55), (0, .35, .6), (.2, -.3, .5), (-.2, -.2, .65), (.35, .3, .6))


def checkerboard_views(f, width, height, cols=9, rows=6, square=.025, poses=TILTED):
    grid = np.zeros((cols*rows, 3), np.float32)
    grid[:, :2] = np.mgrid[0:cols, 0:rows].T.reshape(-1, 2)*square
    camera = np.array([[f, 0, width/2], [0, f, height/2], [0, 0, 1]], np.float64)
    views = []
    for rx, ry, tz in poses:
        rvec = np.array([rx, ry, 0.], np.float64)
        tvec = np.array([-.1, -.06, tz], np.float64)
        corners, _ = cv2.projectPoints(grid, rvec, tvec, camera, np.zeros(5))
        views.append(corners.astype(np.float32))
    return views


class CalibrationTests(unittest.TestCase):
    def test_recovers_focal_length_from_synthetic_checkerboard(self):
        result = calibrate_views(checkerboard_views(F, WIDTH, HEIGHT), (9, 6), .025, WIDTH, HEIGHT)
        self.assertAlmostEqual(result.focal_px, F, delta=1.)
        self.assertEqual((result.width, result.height), (WIDTH, HEIGHT))
        self.assertLess(result.rms_px, .1)
        self.assertEqual(result.views, 6)

    def noisy(self, views, sigma=.25):
        rng = np.random.default_rng(7)
        return [(v+rng.normal(0, sigma, v.shape)).astype(np.float32) for v in views]

    def test_reports_focal_uncertainty_and_steepest_tilt(self):
        views = self.noisy(checkerboard_views(F, WIDTH, HEIGHT))
        result = calibrate_views(views, (9, 6), .025, WIDTH, HEIGHT)
        self.assertGreater(result.focal_std_px, 0)
        self.assertAlmostEqual(result.tilt_max_deg, math.degrees(math.hypot(.35, .3)), delta=.5)

    def test_flat_views_are_flagged_even_when_reported_uncertainty_looks_small(self):
        # Nearly flat views leave f unconstrained, yet OpenCV's std stays small.
        flat = [(.02, 0, .5), (-.02, .01, .55), (0, .02, .6), (.01, -.02, .5), (-.02, -.01, .65), (.02, .02, .6)]
        weak = calibrate_views(self.noisy(checkerboard_views(F, WIDTH, HEIGHT, poses=flat)), (9, 6), .025, WIDTH, HEIGHT)
        self.assertLess(weak.tilt_max_deg, 20)
        self.assertTrue(any('tilt' in warning for warning in weak.warnings()))

    def test_warns_only_when_focal_length_is_weak_or_views_are_flat(self):
        base = dict(fx_px=F, fy_px=F, cx_px=640., cy_px=360., width=WIDTH, height=HEIGHT, rms_px=.2, views=15)
        self.assertEqual(CameraCalibration(F, focal_std_px=4., tilt_max_deg=35., **base).warnings(), [])
        self.assertEqual(len(CameraCalibration(F, focal_std_px=40., tilt_max_deg=35., **base).warnings()), 1)
        self.assertEqual(len(CameraCalibration(F, focal_std_px=4., tilt_max_deg=8., **base).warnings()), 1)
        self.assertEqual(len(CameraCalibration(F, **base).warnings()), 1)

    def test_loads_a_file_written_before_the_quality_fields(self):
        result = calibrate_views(checkerboard_views(F, WIDTH, HEIGHT), (9, 6), .025, WIDTH, HEIGHT)
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'camera.json'
            result.save(path)
            data = json.loads(path.read_text(encoding='utf-8'))
            del data['focal_std_px'], data['tilt_max_deg']
            path.write_text(json.dumps(data), encoding='utf-8')
            self.assertIsNone(load_calibration(path).focal_std_px)

    def test_needs_enough_views(self):
        with self.assertRaises(ValueError):
            calibrate_views(checkerboard_views(F, WIDTH, HEIGHT)[:2], (9, 6), .025, WIDTH, HEIGHT)

    def test_file_round_trip_keeps_resolution(self):
        result = calibrate_views(checkerboard_views(F, WIDTH, HEIGHT), (9, 6), .025, WIDTH, HEIGHT)
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'camera.json'
            result.save(path)
            self.assertEqual(load_calibration(path), result)
            self.assertEqual(json.loads(path.read_text(encoding='utf-8'))['width'], WIDTH)

    def test_load_rejects_a_file_without_usable_focal_length(self):
        good = CameraCalibration(F, F, F, 640., 360., WIDTH, HEIGHT, .1, 6)
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'camera.json'
            good.save(path)
            data = json.loads(path.read_text(encoding='utf-8'))
            data['focal_px'] = 0
            path.write_text(json.dumps(data), encoding='utf-8')
            with self.assertRaises(ValueError):
                load_calibration(path)

    def test_mirrored_view_flips_the_principal_point(self):
        calibration = CameraCalibration(F, F, F, 600., 350., WIDTH, HEIGHT, .1, 6)
        self.assertEqual(calibration.mirrored_principal_px(), (680., 350.))

    def test_resolution_mismatch_is_refused(self):
        calibration = CameraCalibration(F, F, F, 640., 360., WIDTH, HEIGHT, .1, 6)
        calibration.require_resolution(WIDTH, HEIGHT)
        with self.assertRaises(ValueError):
            calibration.require_resolution(640, 480)


if __name__ == '__main__':
    unittest.main()
