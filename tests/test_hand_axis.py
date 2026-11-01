import contextlib
import io
import json
import math
import random
import tempfile
import unittest
from pathlib import Path
from statistics import pstdev

from camera_gestures.axis_estimators import (BenchContext, REACH_METHODS, base_gain, hand_angles,
                                             position_m, reach_z)
from camera_gestures.axis_bench import TRIALS, Trial, TrialRunner, world_for
from camera_gestures.axis_report import EXPECTED_TRIALS, fit_z_gain, format_table, main as report_main, read_log, summarize
from camera_gestures.metric import palm_length_px

WIDTH, HEIGHT, F = 1280, 720, 900.
PALM_M = .09
PALM_FRAME = {0: (0, 0, 0), 5: (-.022, .088, 0), 9: (0, .09, 0), 17: (.028, .078, 0)}
CTX = BenchContext(WIDTH, HEIGHT, F, PALM_M, math.hypot(.05, .01), (640., 360.))


def synthetic_hand(x, y, z, pitch=0, roll=0, z_scale=1.):
    """Project the palm at camera-frame metres to MediaPipe-style points; other joints sit on the wrist."""
    cr, sr = math.cos(math.radians(roll)), math.sin(math.radians(roll))
    cp, sp = math.cos(math.radians(pitch)), math.sin(math.radians(pitch))
    def camera(point):
        a, b, c = point[0]*cr+point[2]*sr, point[1], -point[0]*sr+point[2]*cr
        return x+a, y-(b*cp-c*sp), z-(b*sp+c*cp)  # positive pitch tips the fingers toward the camera
    def normalized(point):
        cx, cy, cz = camera(point)
        return [(WIDTH/2+F*cx/cz)/WIDTH, (HEIGHT/2+F*cy/cz)/HEIGHT, (cz-z)*F/z/WIDTH*z_scale]
    wrist = normalized(PALM_FRAME[0])
    return [normalized(PALM_FRAME[i]) if i in PALM_FRAME else list(wrist) for i in range(21)]


def err_mm(method, pitch=30, roll=0, z_gain=1., z_scale=1.):
    flat = synthetic_hand(0, 0, .5, z_scale=z_scale)
    bent = synthetic_hand(0, 0, .5, pitch=pitch, roll=roll, z_scale=z_scale)
    return base_gain()*abs(REACH_METHODS[method](flat, CTX, z_gain)-REACH_METHODS[method](bent, CTX, z_gain))*1000


class Estimators(unittest.TestCase):
    def test_values_match_the_design_table(self):
        self.assertAlmostEqual(base_gain(), .516, places=2)
        self.assertAlmostEqual(err_mm('2d', pitch=-30), 66.7, delta=1)
        self.assertAlmostEqual(err_mm('2d', pitch=30), 13.1, delta=1)
        self.assertAlmostEqual(err_mm('z', pitch=30), 18.0, delta=1)
        self.assertAlmostEqual(err_mm('z_perspective'), 0, delta=.5)
        self.assertAlmostEqual(err_mm('z_perspective', pitch=-30, z_scale=.9), 8.1, delta=1)
        self.assertLess(err_mm('z_perspective', pitch=-30), .5)
        self.assertAlmostEqual(err_mm('bones', pitch=-30), 23.2, delta=1)

    def test_z_gain_undoes_a_scaled_z(self):
        self.assertLess(err_mm('z_perspective', pitch=-30, z_scale=.7, z_gain=1/.7), .5)

    def test_z_method_matches_the_current_app_formula(self):
        points = synthetic_hand(.03, -.01, .45, pitch=20, roll=10)
        self.assertAlmostEqual(reach_z(points, WIDTH, HEIGHT, F, PALM_M),
                               F*PALM_M/palm_length_px(points, WIDTH, HEIGHT), places=9)

    def test_reach_is_true_when_flat(self):
        for name in REACH_METHODS:
            self.assertAlmostEqual(REACH_METHODS[name](synthetic_hand(.05, -.02, .4), CTX), .4, delta=.002, msg=name)

    def test_position_reads_from_the_chosen_point(self):
        points = synthetic_hand(.05, -.02, .4)
        wrist = position_m(points, CTX, .4, 'wrist')
        self.assertAlmostEqual(wrist[0], .05, places=6)
        self.assertAlmostEqual(wrist[1], -.02, places=6)
        center = position_m(points, CTX, .4, 'center')
        self.assertLess(center[1], wrist[1])    # the palm centre sits above the wrist in the image

    def test_position_of_the_wrist_ignores_pitch(self):
        flat, bent = synthetic_hand(.05, -.02, .4), synthetic_hand(.05, -.02, .4, pitch=30)
        self.assertAlmostEqual(position_m(flat, CTX, .4, 'wrist')[1], position_m(bent, CTX, .4, 'wrist')[1], places=6)

    def test_position_rejects_an_unknown_point(self):
        with self.assertRaises(ValueError):
            position_m(synthetic_hand(0, 0, .5), CTX, .5, 'thumb')

    def test_angles_recover_pose(self):
        pitch, roll = hand_angles(synthetic_hand(0, 0, .5, pitch=30), CTX)
        self.assertAlmostEqual(pitch, 30, delta=3)   # perspective reads about 27.7
        self.assertAlmostEqual(roll, 0, delta=1)
        self.assertAlmostEqual(abs(hand_angles(synthetic_hand(0, 0, .5, roll=45), CTX)[1]), 45, delta=3)

    def test_pitch_sign_is_positive_toward_the_camera(self):
        self.assertGreater(hand_angles(synthetic_hand(0, 0, .5, pitch=30), CTX)[0], 0)
        self.assertLess(hand_angles(synthetic_hand(0, 0, .5, pitch=-30), CTX)[0], 0)

    def test_pointing_at_camera_returns_none(self):
        for name in REACH_METHODS:
            self.assertIsNone(REACH_METHODS[name](synthetic_hand(0, 0, .5, pitch=89.9), CTX), name)

    def test_missing_or_short_landmarks_return_none(self):
        self.assertIsNone(REACH_METHODS['z']([], CTX))
        self.assertIsNone(hand_angles([], CTX))
        self.assertIsNone(hand_angles(synthetic_hand(0, 0, .5)[:5], CTX))


HEADER = dict(kind='header', width=WIDTH, height=HEIGHT, focal_px=F, principal_px=[640., 360.],
              palm_length_m=PALM_M, palm_width_m=math.hypot(.05, .01), calibration='logs/run4.json',
              provisional=False, platform='test', camera=0, note='')


def still(t):
    return {}


def pitch_wave(amplitude):
    return lambda t: dict(pitch=amplitude*math.sin((t-1)/4*2*math.pi)) if t > 1 else {}


def frames_for(trial, pose, seconds=9., fps=30, z_scale=1., lost_every=None):
    frames = []
    for i in range(int(seconds*fps)):
        t = i/fps
        kw = dict(x=0, y=0, z=.5)
        kw.update(pose(t))
        gesture = kw.pop('gesture', 'Open_Palm')
        missing = lost_every is not None and i % 100 < lost_every
        frames.append(dict(kind='frame', trial=trial, t_ms=t*1000, hand_present=not missing, gesture=gesture,
                           landmarks=[] if missing else synthetic_hand(z_scale=z_scale, **kw), world_landmarks=[]))
    return frames


def fist_cycles(t):
    return dict(gesture='Closed_Fist') if t > 1 and int(t*2) % 2 else {}


def row(summary, trial, method='z_perspective', point='wrist', scale='1.0'):
    return summary['trials'][trial]['methods'][method][point]['scale'][scale]


class Report(unittest.TestCase):
    def test_clean_c_trial_passes_with_perspective(self):
        s = summarize(HEADER, frames_for('C', pitch_wave(30)), {'C'})
        self.assertEqual(s['trials']['C']['status'], 'ok')
        self.assertLess(row(s, 'C')['reach_mm'], 1)
        self.assertTrue(row(s, 'C')['passed'])

    def test_2d_fails_the_same_trial(self):
        s = summarize(HEADER, frames_for('C', pitch_wave(30)), {'C'})
        self.assertFalse(row(s, 'C', '2d')['passed'])
        self.assertAlmostEqual(row(s, 'C', '2d')['reach_mm'], 66.7, delta=8)

    def test_center_point_adds_vertical_error(self):
        s = summarize(HEADER, frames_for('C', pitch_wave(30)), {'C'})
        self.assertLess(row(s, 'C')['vertical_mm'], .5)
        self.assertGreater(row(s, 'C', point='center')['vertical_mm'], 3)

    def test_scale_multiplies_the_error(self):
        s = summarize(HEADER, frames_for('C', pitch_wave(30)), {'C'})
        self.assertAlmostEqual(row(s, 'C', '2d', scale='1.25')['reach_mm'], row(s, 'C', '2d')['reach_mm']*1.25, places=6)
        self.assertAlmostEqual(row(s, 'C', '2d', scale='0.5')['reach_mm'], row(s, 'C', '2d')['reach_mm']*.5, places=6)

    def test_c_judges_only_within_35_degrees(self):
        s = summarize(HEADER, frames_for('C', pitch_wave(65)), {'C'})
        self.assertLess(row(s, 'C', '2d')['reach_mm'], 120)   # at -65 degrees the 2D reading is off by far more
        self.assertGreater(s['trials']['C']['angles']['pitch_range_deg'], 80)

    def test_fit_finds_the_z_scale(self):
        frames = frames_for('C', pitch_wave(30), z_scale=.7)
        ctx = BenchContext(WIDTH, HEIGHT, F, PALM_M, HEADER['palm_width_m'], (640., 360.))
        self.assertAlmostEqual(fit_z_gain(frames, ctx), 1/.7, delta=.1)
        summary = summarize(HEADER, frames, {'C'})
        self.assertAlmostEqual(summary['z_accuracy_pct'], 70, delta=5)

    def test_fit_without_a_c_trial_is_none(self):
        s = summarize(HEADER, frames_for('D', still), {'D'})
        self.assertIsNone(s['z_gain_fit'])
        self.assertIsNone(s['z_accuracy_pct'])

    def test_hand_loss_over_ten_percent_is_invalid(self):
        s = summarize(HEADER, frames_for('C', still, lost_every=15), {'C'})
        self.assertEqual(s['trials']['C']['status'], 'invalid')
        self.assertAlmostEqual(s['trials']['C']['lost_pct'], 15, delta=2)

    def test_baseline_not_held_is_invalid(self):
        drift = lambda t: dict(z=.5+min(t, 1)*.05)
        s = summarize(HEADER, frames_for('C', drift), {'C'})
        self.assertEqual(s['trials']['C']['status'], 'invalid')

    def test_low_fps_is_invalid(self):
        s = summarize(HEADER, frames_for('C', still, fps=10), {'C'})
        self.assertEqual(s['trials']['C']['status'], 'invalid')
        self.assertAlmostEqual(s['trials']['C']['median_fps'], 10, delta=.1)

    def test_the_macs_usual_frame_rate_is_accepted(self):
        """Saved Mac logs run at 14.9 to 30 fps; 15 as a floor would reject most of a slow session."""
        s = summarize(HEADER, frames_for('A_mid', still, fps=14), {'A_mid'})
        self.assertEqual(s['trials']['A_mid']['status'], 'ok')

    def test_unfinished_trial_is_incomplete(self):
        s = summarize(HEADER, frames_for('C', still), set())
        self.assertEqual(s['trials']['C']['status'], 'incomplete')

    def test_a_hand_never_seen_does_not_crash(self):
        s = summarize(HEADER, frames_for('C', still, lost_every=100), {'C'})
        self.assertEqual(s['trials']['C']['status'], 'invalid')
        self.assertEqual(s['trials']['C']['methods'], {})

    def test_retried_runs_are_kept_out_of_the_results(self):
        s = summarize(HEADER, frames_for('C#retry1', still)+frames_for('C', still), {'C'})
        self.assertEqual(list(s['trials']), ['C'])

    def test_sd_trial_reports_noise(self):
        quiet = summarize(HEADER, frames_for('A_mid', still), {'A_mid'})
        self.assertEqual(row(quiet, 'A_mid')['reach_mm'], 0)
        self.assertTrue(row(quiet, 'A_mid')['passed'])
        self.assertIn('pitch_sd_deg', quiet['trials']['A_mid']['angles'])
        loud = summarize(HEADER, frames_for('A_mid', lambda t: dict(z=.5+.05*math.sin((t-1)*3)) if t > 1 else {}), {'A_mid'})
        self.assertEqual(loud['trials']['A_mid']['status'], 'ok')
        self.assertIs(row(loud, 'A_mid')['passed'], False)

    def test_a_free_push_reports_its_range_with_no_pass_mark(self):
        push = lambda t: dict(z=.5+.15*math.sin((t-1)/8*2*math.pi)) if t > 1 else {}
        s = summarize(HEADER, frames_for('B', push), {'B'})
        self.assertEqual(s['trials']['B']['status'], 'ok')
        self.assertAlmostEqual(row(s, 'B')['reach_mm'], base_gain()*300, delta=15)
        self.assertIsNone(row(s, 'B')['passed'])

    def test_a_push_set_with_no_push_does_not_count(self):
        s = summarize(HEADER, frames_for('B', still), {'B'})
        self.assertEqual(s['trials']['B']['status'], 'invalid')
        self.assertIn('too little motion', s['trials']['B']['reason'])

    def test_fist_trial_uses_the_same_limit(self):
        s = summarize(HEADER, frames_for('E', fist_cycles, seconds=14.), {'E'})
        self.assertEqual(s['trials']['E']['status'], 'ok')
        self.assertTrue(row(s, 'E')['passed'])

    def test_crosstalk_compares_the_axis_not_commanded(self):
        pure = summarize(HEADER, frames_for('F_pitch', pitch_wave(30)), {'F_pitch'})
        self.assertLess(pure['trials']['F_pitch']['crosstalk_pct'], 5)
        self.assertTrue(pure['trials']['F_pitch']['passed'])
        mixed = lambda t: dict(pitch=30*math.sin(t*1.5), roll=30*math.sin(t*1.5)) if t > 1 else {}
        self.assertIs(summarize(HEADER, frames_for('F_pitch', mixed), {'F_pitch'})['trials']['F_pitch']['passed'], False)

    def test_read_log_skips_truncated_last_line(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'x.axis_bench.jsonl'
            frame = frames_for('C', still, seconds=.1)[0]
            path.write_text('\n'.join([json.dumps(HEADER), json.dumps(frame), json.dumps(dict(kind='trial_end', trial='C')),
                                       '{"kind":"fr']), encoding='utf-8')
            header, frames, completed = read_log(path)
        self.assertEqual(header['focal_px'], F)
        self.assertEqual(len(frames), 1)
        self.assertEqual(completed, {'C'})

    def test_read_log_refuses_a_broken_middle_line(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'x.axis_bench.jsonl'
            path.write_text(json.dumps(HEADER)+'\n{"kind":"fr\n'+json.dumps(HEADER)+'\n', encoding='utf-8')
            with self.assertRaises(ValueError):
                read_log(path)

    def test_table_names_the_setup_and_marks_provisional(self):
        table = format_table(summarize(dict(HEADER, provisional=True), frames_for('C', still), {'C'}))
        self.assertIn('provisional', table)
        self.assertIn('z_perspective', table)
        self.assertIn('logs/run4.json', table)
        self.assertNotIn('provisional', format_table(summarize(HEADER, frames_for('C', still), {'C'})))

    def test_cli_writes_the_summary_next_to_the_log(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'x.axis_bench.jsonl'
            lines = [HEADER]+frames_for('A_mid', still, seconds=2.)+[dict(kind='trial_end', trial='A_mid')]
            path.write_text('\n'.join(map(json.dumps, lines))+'\n', encoding='utf-8')
            with contextlib.redirect_stdout(io.StringIO()) as out:
                self.assertEqual(report_main([str(path)]), 0)
            self.assertIn('A_mid', out.getvalue())
            summary = json.loads((Path(folder)/'x.axis_summary.json').read_text(encoding='utf-8'))
        self.assertEqual(summary['trials']['A_mid']['status'], 'ok')

    def test_cli_keeps_a_renamed_log_intact(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'mac_run.jsonl'
            lines = [HEADER]+frames_for('A_mid', still, seconds=2.)+[dict(kind='trial_end', trial='A_mid')]
            original = '\n'.join(map(json.dumps, lines))+'\n'
            path.write_text(original, encoding='utf-8')
            with contextlib.redirect_stdout(io.StringIO()):
                report_main([str(path)])
            self.assertEqual(path.read_text(encoding='utf-8'), original)
            self.assertTrue((Path(folder)/'mac_run.axis_summary.json').is_file())

    def test_a_bad_trial_is_not_judged(self):
        for frames, completed in ((frames_for('C', pitch_wave(30), lost_every=30), {'C'}), (frames_for('C', pitch_wave(30)), set())):
            s = summarize(HEADER, frames, completed)
            self.assertIsNone(row(s, 'C')['passed'])
            table = format_table(s)
            self.assertIn('not judged', table)
            self.assertNotIn(' pass', table)

    def test_no_motion_is_not_a_pass(self):
        cases = (('C', still), ('C', pitch_wave(5)), ('D', still), ('D', lambda t: dict(roll=5*math.sin(t*2)) if t > 1 else {}),
                 ('E', still), ('F_pitch', still), ('F_roll', still))
        for trial, pose in cases:
            result = summarize(HEADER, frames_for(trial, pose), {trial})['trials'][trial]
            self.assertEqual(result['status'], 'invalid', trial)
            self.assertIn('motion', result['reason'], trial)

    def test_real_motion_clears_the_gate_and_is_printed(self):
        twist = lambda t: dict(roll=45*math.sin((t-1)/4*2*math.pi)) if t > 1 else {}
        s = summarize(HEADER, frames_for('D', twist), {'D'})
        self.assertEqual(s['trials']['D']['status'], 'ok')
        self.assertIn('roll range', format_table(s))
        self.assertEqual(summarize(HEADER, frames_for('F_roll', twist), {'F_roll'})['trials']['F_roll']['status'], 'ok')

    def test_a_wrist_out_of_frame_counts_as_lost(self):
        result = summarize(HEADER, frames_for('A_near', lambda t: dict(y=.3)), {'A_near'})['trials']['A_near']
        self.assertEqual(result['status'], 'invalid')
        self.assertGreater(result['lost_pct'], 90)

    def test_tipping_during_neutral_is_invalid(self):
        tip = lambda t: dict(pitch=30*math.sin(t*6)) if t <= 1 else pitch_wave(30)(t)
        result = summarize(HEADER, frames_for('C', tip), {'C'})['trials']['C']
        self.assertEqual(result['status'], 'invalid')
        self.assertIn('neutral', result['reason'])

    def test_neutral_held_bent_is_invalid(self):
        result = summarize(HEADER, frames_for('A_mid', lambda t: dict(pitch=-45)), {'A_mid'})['trials']['A_mid']
        self.assertEqual(result['status'], 'invalid')
        self.assertIn('neutral', result['reason'])

    def test_hand_absent_for_the_neutral_second_is_invalid(self):
        frames = frames_for('C', pitch_wave(30), seconds=16.)
        for f in frames[:30]:
            f['hand_present'], f['landmarks'] = False, []
        result = summarize(HEADER, frames, {'C'})['trials']['C']
        self.assertEqual(result['status'], 'invalid')
        self.assertIn('neutral', result['reason'])

    def test_fit_reaches_a_poor_z_and_flags_the_edge(self):
        low = summarize(HEADER, frames_for('C', pitch_wave(30), z_scale=.4), {'C'})
        self.assertAlmostEqual(low['z_accuracy_pct'], 40, delta=5)
        self.assertFalse(low['z_fit_at_edge'])
        flat = summarize(HEADER, frames_for('C', pitch_wave(30), z_scale=.01), {'C'})
        self.assertTrue(flat['z_fit_at_edge'])
        self.assertIn('edge', format_table(flat))

    def test_no_fit_from_an_invalid_c(self):
        s = summarize(HEADER, frames_for('C', still), {'C'})
        self.assertIsNone(s['z_gain_fit'])

    def test_fitted_rows_show_what_the_gain_would_do(self):
        s = summarize(HEADER, frames_for('C', pitch_wave(30), z_scale=.7), {'C'})
        self.assertIs(row(s, 'C')['passed'], False)
        self.assertIs(row(s, 'C', 'z_perspective_fit')['passed'], True)

    def test_crosstalk_survives_z_noise(self):
        noise = random.Random(1)
        frames = frames_for('F_pitch', pitch_wave(30))
        for f in frames:
            for point in f['landmarks']:
                point[2] += noise.gauss(0, 5/WIDTH)
        self.assertLess(summarize(HEADER, frames, {'F_pitch'})['trials']['F_pitch']['crosstalk_pct'], 25)

    def test_sd_is_taken_after_the_filter(self):
        noise = random.Random(2)
        frames = frames_for('A_mid', lambda t: dict(z=.5+noise.gauss(0, .001)))
        raw = pstdev(REACH_METHODS['z_perspective'](f['landmarks'], CTX) for f in frames)*base_gain()*1000
        self.assertLess(row(summarize(HEADER, frames, {'A_mid'}), 'A_mid')['reach_mm'], raw*.7)

    def test_drift_judges_every_axis(self):
        slide = lambda t: dict(x=max(0, t-1)*.01)
        s = summarize(HEADER, frames_for('E', lambda t: dict(slide(t), **fist_cycles(t)), seconds=14.), {'E'})
        self.assertGreater(row(s, 'E')['lateral_mm'], 10)
        self.assertLess(row(s, 'E')['reach_mm'], 5)
        self.assertIs(row(s, 'E')['passed'], False)

    def test_baseline_ignores_a_one_frame_spike(self):
        frames = frames_for('E', fist_cycles, seconds=14.)
        frames[0]['landmarks'] = synthetic_hand(0, 0, .53)
        self.assertLess(row(summarize(HEADER, frames, {'E'}), 'E')['reach_mm'], 1)

    def test_trials_never_run_are_listed(self):
        s = summarize(HEADER, frames_for('A_mid', still), {'A_mid'})
        self.assertIn('B', s['not_run'])
        self.assertNotIn('A_mid', s['not_run'])
        self.assertIn('not run', format_table(s))

    def test_report_expects_the_trials_the_bench_runs(self):
        self.assertEqual(EXPECTED_TRIALS, tuple(t.name for t in TRIALS))

    def test_palm_width_comes_from_the_open_palm_when_not_measured(self):
        header = dict(HEADER, palm_width_m=None, palm_measured=False)
        s = summarize(header, frames_for('A_mid', still), {'A_mid'})
        self.assertEqual(s['trials']['A_mid']['status'], 'ok')
        self.assertAlmostEqual(row(s, 'A_mid', 'bones')['reach_mm'], 0, delta=.1)
        self.assertIn('estimated', format_table(s))
        self.assertNotIn('estimated', format_table(summarize(dict(HEADER, palm_measured=True), frames_for('A_mid', still), {'A_mid'})))

    def test_a_bent_start_stands_out_from_the_other_starts(self):
        header = dict(HEADER, palm_width_m=None, palm_measured=False)
        frames = (frames_for('A_near', still)+frames_for('A_mid', still)+frames_for('A_far', still)
                  +frames_for('B', lambda t: dict(pitch=-45)))
        s = summarize(header, frames, {'A_near', 'A_mid', 'A_far', 'B'})
        self.assertEqual(s['trials']['A_mid']['status'], 'ok')
        self.assertEqual(s['trials']['B']['status'], 'invalid')
        self.assertIn('neutral', s['trials']['B']['reason'])

    def test_a_different_hand_size_reads_the_same_motion(self):
        """Palm length scales every axis alike, so a wrong one acts as a scale and turns no direction."""
        small = BenchContext(WIDTH, HEIGHT, F, .09, .05, (640., 360.))
        large = BenchContext(WIDTH, HEIGHT, F, .12, .05, (640., 360.))
        a, b = synthetic_hand(.02, 0, .5), synthetic_hand(.1, 0, .4)
        def move(ctx):
            za, zb = REACH_METHODS['2d'](a, ctx), REACH_METHODS['2d'](b, ctx)
            return (zb-za, position_m(b, ctx, zb, 'wrist')[0]-position_m(a, ctx, za, 'wrist')[0])
        ratio = [m/n for m, n in zip(move(large), move(small))]
        self.assertAlmostEqual(ratio[0], .12/.09, places=6)
        self.assertAlmostEqual(ratio[1], .12/.09, places=6)

    def test_the_report_names_the_hand_each_trial_used(self):
        frames = [dict(f, side='Left') for f in frames_for('A_mid', still)]
        frames[0]['side'] = 'Right'     # a one-frame label flicker
        s = summarize(HEADER, frames, {'A_mid'})
        self.assertEqual(s['trials']['A_mid']['side'], 'Left')
        self.assertIn('hand Left', format_table(s))

    def test_a_log_without_sides_still_reads(self):
        s = summarize(HEADER, frames_for('A_mid', still), {'A_mid'})
        self.assertIsNone(s['trials']['A_mid']['side'])

    def test_calibration_warnings_are_printed(self):
        s = summarize(dict(HEADER, calibration_warnings=['focal std is high']), frames_for('A_mid', still), {'A_mid'})
        self.assertIn('focal std is high', format_table(s))


class Runner(unittest.TestCase):
    def test_walks_each_trial(self):
        r = TrialRunner((Trial('C', 15, 'x'),))
        self.assertEqual(r.state, 'waiting')
        self.assertFalse(r.recording)
        r.press(' ', 0)
        self.assertEqual(r.state, 'neutral')
        self.assertTrue(r.recording)
        self.assertIsNone(r.tick(999))
        r.tick(1000)
        self.assertEqual(r.state, 'running')
        self.assertEqual(r.tick(16000), 'C')
        self.assertEqual(r.state, 'done')
        self.assertIsNone(r.tick(17000))

    def test_moves_to_the_next_trial_and_waits(self):
        r = TrialRunner((Trial('A', 1, 'x'), Trial('B', 1, 'y')))
        r.press(' ', 0)
        r.tick(1000)
        self.assertEqual(r.tick(2000), 'A')
        self.assertEqual((r.state, r.current.name), ('waiting', 'B'))

    def test_retry_during_a_trial_renames_the_old_frames(self):
        r = TrialRunner((Trial('C', 15, 'x'),))
        r.press(' ', 0)
        r.tick(1000)
        self.assertEqual(r.press('r', 2000), ('C', 'C#retry1'))
        self.assertEqual(r.state, 'waiting')
        r.press(' ', 3000)
        self.assertEqual(r.press('r', 3100), ('C', 'C#retry2'))

    def test_retry_after_a_trial_goes_back_to_it(self):
        r = TrialRunner((Trial('A', 1, 'x'), Trial('B', 1, 'y')))
        r.press(' ', 0)
        r.tick(1000)
        r.tick(2000)
        self.assertEqual(r.press('r', 2500), ('A', 'A#retry1'))
        self.assertEqual(r.current.name, 'A')

    def test_retry_before_anything_ran_does_nothing(self):
        r = TrialRunner((Trial('A', 1, 'x'),))
        self.assertIsNone(r.press('r', 0))
        self.assertEqual(r.state, 'waiting')

    def test_space_does_nothing_while_running_or_done(self):
        r = TrialRunner((Trial('A', 1, 'x'),))
        r.press(' ', 0)
        r.press(' ', 10)
        self.assertEqual(r.state, 'neutral')
        r.tick(1000)
        r.tick(2000)
        r.press(' ', 2100)
        self.assertEqual(r.state, 'done')

    def test_the_screen_numbers_each_step_and_names_its_keys(self):
        r = TrialRunner((Trial('A', 1, 'x'), Trial('B', 1, 'y')))
        lines = r.status(0)
        self.assertEqual(lines[0], 'Step 1/2 A: x')
        self.assertIn('SPACE', lines[1])
        r.press(' ', 0)
        r.tick(1000)
        r.tick(2000)
        self.assertEqual(r.status(2000)[0], 'Step 2/2 B: y')

    def test_the_screen_names_the_neutral_pose_and_the_time_left(self):
        r = TrialRunner((Trial('A', 10, 'x'),))
        r.press(' ', 0)
        self.assertIn('open palm', r.status(0)[0])
        r.tick(1000)
        self.assertEqual(r.status(1000), ['Step 1/1 A (10 s left): x'])

    def test_a_second_retry_key_does_not_undo_the_step_before(self):
        r = TrialRunner((Trial('A', 1, 'x'), Trial('B', 1, 'y')))
        r.press(' ', 0)
        r.tick(1000)
        r.tick(2000)
        r.press(' ', 3000)
        r.tick(4000)
        r.tick(5000)
        self.assertEqual(r.press('r', 5100), ('B', 'B#retry1'))
        self.assertIsNone(r.press('r', 5200))
        self.assertEqual(r.current.name, 'B')
        r.press(' ', 6000)
        self.assertEqual(r.press('r', 6100), ('B', 'B#retry2'))

    def test_no_step_asks_for_a_ruler(self):
        self.assertFalse([t.name for t in TRIALS if 'ruler' in t.prompt])

    def test_the_plan_lists_every_set_with_its_length(self):
        self.assertEqual([(t.name, t.seconds) for t in TRIALS],
                         [('A_near', 10), ('A_mid', 10), ('A_far', 10), ('B', 20), ('C', 15), ('D', 15), ('E', 30),
                          ('F_pitch', 12), ('F_roll', 12)])

    def test_world_landmarks_come_from_the_same_hand(self):
        from types import SimpleNamespace as N
        a, b = [N(x=.1, y=.2, z=0.)], [N(x=.7, y=.2, z=0.)]
        result = N(hand_landmarks=[a, b], hand_world_landmarks=[[N(x=1., y=0., z=0.)], [N(x=2., y=0., z=0.)]])
        self.assertEqual(world_for(result, [[.7, .2, 0.]]), [[2., 0., 0.]])
        self.assertEqual(world_for(result, []), [])

    def test_module_needs_no_camera_libraries_to_import(self):
        import camera_gestures.axis_bench
        self.assertNotIn('cv2', vars(camera_gestures.axis_bench))

    def test_read_log_applies_a_retry(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'x.axis_bench.jsonl'
            frame = frames_for('C', still, seconds=.1)[0]
            lines = [HEADER, frame, dict(kind='trial_end', trial='C'), dict(kind='retry', trial='C', as_trial='C#retry1'),
                     frame]
            path.write_text('\n'.join(map(json.dumps, lines))+'\n', encoding='utf-8')
            _, frames, completed = read_log(path)
        self.assertEqual([f['trial'] for f in frames], ['C#retry1', 'C'])
        self.assertEqual(completed, set())


if __name__ == '__main__':
    unittest.main()
