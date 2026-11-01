"""Guided camera check of hand reach, tilt and twist. Saves raw landmarks; moves nothing."""
import argparse
import json
import platform
import time
from collections import namedtuple
from datetime import datetime, timezone
from pathlib import Path

from .axis_estimators import reach_2d
from .axis_report import read_log, summarize
from .calibration import load_calibration
from .download_model import MODEL
from .observation import extract, extract_selected

Trial = namedtuple('Trial', 'name seconds prompt')
TRIALS = (
    Trial('A_near', 10, 'Hold open palm still, about 30 cm from camera'),
    Trial('A_mid', 10, 'Hold open palm still, about 50 cm from camera'),
    Trial('A_far', 10, 'Hold open palm still, about 70 cm from camera'),
    Trial('B', 20, 'Push hand toward camera and back, slowly, 3 times'),
    Trial('C', 15, 'Rest elbow, wrist still. Tip +-30 deg, then as far as tracking holds'),
    Trial('D', 15, 'Rest elbow, wrist still. Twist +-45 deg'),
    Trial('E', 30, 'Rest elbow, wrist still. Fist, open: 10 times'),
    Trial('F_pitch', 12, 'FOLD fingers toward camera and back. No twist'),
    Trial('F_roll', 12, 'TURN wrist like a door knob. No folding'),
)
NEUTRAL_MS = 1000
ASSUMED_PALM_M = .10           # a wrong value scales every axis alike, as the scale setting does
ASSUMED_F_PER_WIDTH = 900/1280  # the project's provisional f for a 1280 px laptop camera


class TrialRunner:
    """Which trial is on, from key presses and time. Knows nothing of the camera."""

    def __init__(self, trials):
        self.trials = trials
        self.index = 0
        self.state = 'waiting' if trials else 'done'
        self.started = None
        self.retries = {}
        self.ran = set()
        self.redoing = False

    @property
    def current(self):
        return self.trials[self.index] if self.index < len(self.trials) else None

    @property
    def recording(self):
        return self.state in ('neutral', 'running')

    def press(self, key, now_ms):
        """A retry returns (trial, name for its old frames) so the file can say so; otherwise None."""
        if key == ' ' and self.state == 'waiting':
            self.state, self.started = 'neutral', now_ms
            self.redoing = False
            self.ran.add(self.current.name)
        elif key == 'r':
            if not self.recording and self.index > 0 and not self.redoing:
                self.index -= 1
            elif not self.recording:
                return None
            name = self.current.name
            if name not in self.ran:
                return None
            self.retries[name] = self.retries.get(name, 0)+1
            self.state, self.redoing = 'waiting', True
            return name, f'{name}#retry{self.retries[name]}'
        return None

    def tick(self, now_ms):
        """Advances time; returns a trial's name once, on the tick that finishes it."""
        if self.state == 'neutral' and now_ms-self.started >= NEUTRAL_MS:
            self.state = 'running'
        if self.state == 'running' and now_ms-self.started >= NEUTRAL_MS+self.current.seconds*1000:
            name = self.current.name
            self.index += 1
            self.state = 'waiting' if self.index < len(self.trials) else 'done'
            return name
        return None

    def status(self, now_ms):
        """Lines for the screen."""
        if self.state == 'done':
            return ['All steps done. Q to quit, R to redo the last one']
        trial, step = self.current, f'Step {self.index+1}/{len(self.trials)}'
        if self.state == 'waiting':
            return [f'{step} {trial.name}: {trial.prompt}', 'SPACE to start, R to redo the last one']
        if self.state == 'neutral':
            return [f'{step} {trial.name}: hold open palm, flat to camera, still']
        left = NEUTRAL_MS+trial.seconds*1000-(now_ms-self.started)
        return [f'{step} {trial.name} ({left/1000:.0f} s left): {trial.prompt}']


def trial_note(path, name):
    """Whether the step just finished counts, so a bad one can be redone on the spot."""
    trial = summarize(*read_log(path))['trials'][name]
    if trial['status'] == 'ok':
        return f'Last: {name} ok'
    return f"Last: {name} NOT VALID ({trial['reason']}). R to redo"


def distance_line(points, width, height, focal_px, palm_m):
    """Stands in for a ruler when placing the hand; as approximate as the palm size it assumes."""
    reach = reach_2d(points, width, height, focal_px, palm_m) if points else None
    return f'Hand about {100*reach:.0f} cm from camera' if reach else None


def observe(result, side):
    """Either side when side is 'Any'. Two hands in view stay ambiguous, as in extract_selected."""
    if side != 'Any':
        return extract_selected(result, side)
    if len(result.hand_landmarks) != 1:
        return dict(extract(result), hand_present=False, gesture='No_hand', landmarks=[])
    return extract(result)


def lost_reason(result, side, frame):
    """What the camera does see, so a missing hand can be fixed instead of guessed at."""
    labels = [max(c, key=lambda x: x.score) for c in result.handedness if c]
    seen = ', '.join(f'{top.category_name} {top.score:.2f}' for top in labels)
    if not labels:
        what = 'no hand in view'
    elif side == 'Any':
        what = f'{len(labels)} hands in view, keep one: sees {seen}'
    else:
        what = f'{side} hand not found: sees {seen}'
    return f'HAND LOST: {what} (brightness {frame.mean():.0f}/255)'


def world_for(result, points):
    """World landmarks of the hand extract_selected chose, matched by its image points."""
    if not points:
        return []
    for hand, world in zip(result.hand_landmarks, result.hand_world_landmarks):
        if hand and hand[0].x == points[0][0] and hand[0].y == points[0][1]:
            return [[float(p.x), float(p.y), float(p.z)] for p in world]
    return []


def main(argv=None, clock=time.monotonic):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--calibration', type=Path, help='file from camera_gestures.calibration; without it f is an estimate')
    parser.add_argument('--palm-length-m', type=float, help='wrist crease to middle-finger base, by ruler; optional')
    parser.add_argument('--palm-width-m', type=float, help='index-finger base to little-finger base, by ruler; optional')
    parser.add_argument('--hand', choices=['Any', 'Left', 'Right'], default='Any')
    parser.add_argument('--camera', type=int, default=0)
    parser.add_argument('--model', type=Path, default=MODEL)
    parser.add_argument('--note', default='', help='lighting, distance or anything else worth keeping')
    parser.add_argument('--only', help='comma-separated steps to run, e.g. E,F_pitch; the rest stay in their own files')
    args = parser.parse_args(argv)
    trials = TRIALS
    if args.only:
        names = args.only.split(',')
        unknown = set(names)-{t.name for t in TRIALS}
        if unknown:
            parser.error(f"Unknown steps: {', '.join(sorted(unknown))}")
        trials = tuple(t for t in TRIALS if t.name in names)
    if not args.model.is_file():
        parser.error('Model missing. Run: python -m camera_gestures.download_model')
    calibration = load_calibration(args.calibration) if args.calibration else None
    palm_measured = args.palm_length_m is not None and args.palm_width_m is not None
    palm_length_m = args.palm_length_m if args.palm_length_m is not None else ASSUMED_PALM_M
    import cv2
    import mediapipe as mp

    options = mp.tasks.vision.GestureRecognizerOptions(
        base_options=mp.tasks.BaseOptions(model_asset_path=str(args.model)),
        running_mode=mp.tasks.vision.RunningMode.VIDEO,
        num_hands=2,
    )
    cap = cv2.VideoCapture(args.camera)
    window = 'Hand axis bench - Q or Esc to quit'
    try:
        if not cap.isOpened():
            raise RuntimeError('Camera unavailable. Close other camera apps; check camera permissions or --camera 1.')
        if calibration:
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, calibration.width)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, calibration.height)
            calibration.require_resolution(int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))
            width, height, focal_px = calibration.width, calibration.height, calibration.focal_px
            principal_px, warnings = list(calibration.mirrored_principal_px()), calibration.warnings()
        else:
            width, height = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            focal_px, principal_px = ASSUMED_F_PER_WIDTH*width, [width/2, height/2]
            warnings = ['no calibration: f is an estimate']
        provisional = calibration is None or 'provisional' in args.calibration.name
        logs = Path('logs')
        logs.mkdir(exist_ok=True)
        stem = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        path = logs/f'{stem}.axis_bench.jsonl'
        runner = TrialRunner(trials)
        start = clock()
        last = -1
        note = reason = None
        with path.open('w', encoding='utf-8') as out, mp.tasks.vision.GestureRecognizer.create_from_options(options) as recognizer:
            def write(record):
                out.write(json.dumps(record, allow_nan=False)+'\n')
                out.flush()
            write(dict(kind='header', width=width, height=height, focal_px=focal_px, principal_px=principal_px,
                       palm_length_m=palm_length_m, palm_width_m=args.palm_width_m, palm_measured=palm_measured,
                       calibration=str(args.calibration) if calibration else None, provisional=provisional,
                       calibration_warnings=warnings,
                       platform=platform.platform(), camera=args.camera, hand=args.hand, note=args.note,
                       mediapipe=mp.__version__, opencv=cv2.__version__, reported_fps=cap.get(cv2.CAP_PROP_FPS)))
            while True:
                ok, frame = cap.read()
                now = max(last+1, int((clock()-start)*1000))
                last = now
                if not ok:
                    raise RuntimeError('Camera frame read failed. This trial stays incomplete; restart and redo it.')
                frame = cv2.flip(frame, 1)
                image = mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                result = recognizer.recognize_for_video(image, now)
                observation = observe(result, args.hand)
                if runner.recording:
                    write(dict(kind='frame', trial=runner.current.name, t_ms=now, hand_present=observation['hand_present'],
                               side=observation['handedness'], gesture=observation['gesture'],
                               landmarks=observation['landmarks'],
                               world_landmarks=world_for(result, observation['landmarks'])))
                finished = runner.tick(now)
                if finished:
                    write(dict(kind='trial_end', trial=finished))
                    note = trial_note(path, finished)
                lines = runner.status(now)
                if note and not runner.recording:
                    lines.append(note)
                if runner.state == 'waiting':
                    distance = distance_line(observation['landmarks'], width, height, focal_px, palm_length_m)
                    if distance:
                        lines.append(distance)
                if not observation['hand_present']:
                    lines.append(lost_reason(result, args.hand, frame))
                what = lines[-1].split(' (brightness')[0] if not observation['hand_present'] else None
                if what != reason:
                    reason = what
                    print(lines[-1] if what else 'Hand found', flush=True)
                if provisional:
                    lines.append('PROVISIONAL focal length')
                for i, line in enumerate(lines):
                    cv2.putText(frame, line, (12, 28+i*28), cv2.FONT_HERSHEY_SIMPLEX, .6, (0, 255, 255), 2)
                cv2.imshow(window, frame)
                key = cv2.waitKey(1) & 0xFF
                if key in (27, ord('q')) or cv2.getWindowProperty(window, cv2.WND_PROP_VISIBLE) < 1:
                    break
                if chr(key) == ' ' and not observation['hand_present']:
                    continue    # a step started with no hand can only come out invalid
                retried = runner.press(chr(key), now)
                if retried:
                    note = None
                    write(dict(kind='retry', trial=retried[0], as_trial=retried[1]))
        print(f'Saved {path}\nReport: python -m camera_gestures.axis_report {path}')
    finally:
        cap.release()
        cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
