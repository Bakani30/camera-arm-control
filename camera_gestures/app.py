"""Local webcam preview. Outputs are display/log values, never robot commands."""
import argparse
import csv
import hashlib
import json
import platform
import time
from datetime import datetime, timezone
from pathlib import Path
from .state import GestureOutput
from .observation import extract_selected
from .calibration import load_calibration
from .control import HandControl
from .metric import MetricHand
from .pipeline import STALE_MS, handle_key, step
from .display import draw
from .download_model import MODEL


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--classifier', choices=['mediapipe', 'keypoint'], default='mediapipe')
    parser.add_argument('--hand', choices=['Left','Right'], default='Right')
    parser.add_argument('--camera', type=int, default=0)
    parser.add_argument('--model', type=Path, default=MODEL)
    parser.add_argument('--threshold', type=float, default=.7)
    parser.add_argument('--dwell-ms', type=int, default=250)
    parser.add_argument('--drop-ms', type=int, default=None)
    parser.add_argument('--calibration', type=Path, help='file from camera_gestures.calibration; turns on metres, needs --palm-length-m')
    parser.add_argument('--palm-length-m', type=float, help="user's wrist crease to middle-finger base, metres")
    parser.add_argument('--changes-only', action='store_true', help='Log to CSV only when output code changes (default logs all frames)')
    parser.add_argument('--mapping', choices=['relative'], help='draw hand-driven targets on the mock arm and save them; needs --calibration. Moves no hardware')
    args = parser.parse_args()
    if (args.calibration is None) != (args.palm_length_m is None):
        parser.error('--calibration and --palm-length-m go together')
    if args.mapping and args.calibration is None:
        parser.error('--mapping needs --calibration and --palm-length-m')
    state = GestureOutput(args.threshold, args.dwell_ms, drop_ms=args.drop_ms)
    if not args.model.is_file():
        parser.error('Model missing. Run: python -m camera_gestures.download_model')
    import cv2
    import mediapipe as mp

    options = mp.tasks.vision.GestureRecognizerOptions(
        base_options=mp.tasks.BaseOptions(model_asset_path=str(args.model)),
        running_mode=mp.tasks.vision.RunningMode.VIDEO,
        num_hands=2,
    )
    keypoint = None
    if args.classifier == 'keypoint':
        from .keypoint import KeypointClassifier
        keypoint = KeypointClassifier()
    logs = Path('logs')
    logs.mkdir(exist_ok=True)
    stem = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    cap = cv2.VideoCapture(args.camera)
    start = time.monotonic()
    last_timestamp = -1
    previous = None
    calibration = load_calibration(args.calibration) if args.calibration else None
    principal = calibration.mirrored_principal_px() if calibration else None
    metric = MetricHand(calibration.focal_px, args.palm_length_m, principal) if calibration else None
    control = HandControl(args.hand, metric=metric)
    target, depth = control.target, control.depth
    label = 'unlabeled'
    frame_index = 0
    previous_receipt = None
    window = 'Camera gestures - Q or Esc to quit'
    session = target_file = None
    try:
        if not cap.isOpened():
            raise RuntimeError('Camera unavailable. Close other camera apps; check Windows camera permissions or --camera 1.')
        if calibration:
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, calibration.width)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, calibration.height)
            calibration.require_resolution(int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))
        metadata = dict(platform=platform.platform(), python=platform.python_version(),
                        mediapipe=mp.__version__, opencv=cv2.__version__, camera=args.camera,
                        width=cap.get(cv2.CAP_PROP_FRAME_WIDTH), height=cap.get(cv2.CAP_PROP_FRAME_HEIGHT),
                        reported_fps=cap.get(cv2.CAP_PROP_FPS), threshold=args.threshold,
                        dwell_ms=args.dwell_ms, drop_ms=state.drop_ms,
                        log_mode='changes_only' if args.changes_only else 'all_frames', timestamp='monotonic frame receipt, milliseconds',
                        model=str(args.model.resolve()),
                        model_sha256=hashlib.sha256(args.model.read_bytes()).hexdigest(),
                        source='MediaPipe Tasks GestureRecognizer; project diagnostic wrapper',
                        target_units='normalized screen xy, mirrored x/right y/down', target_filter_tau_ms=80, depth_filter_tau_ms=120,
                        depth_units='relative proxy, positive toward camera, not metres',
                        depth_formula='anchor + 1 - reference_palm_scale/current_palm_scale, clipped [-1,1]',
                        assigned_hand=args.hand, handedness_threshold=.8,
                        classifier=args.classifier, mirrored=True, max_gap_ms=500, stale_inference_ms=STALE_MS,
                        focal_px=calibration.focal_px if calibration else None, palm_length_m=args.palm_length_m, principal_px=principal,
                        calibration_rms_px=calibration.rms_px if calibration else None,
                        reported_autofocus=cap.get(cv2.CAP_PROP_AUTOFOCUS),
                        metric_units='metres from re-anchor, mirrored x/right y/down; z_m from camera',
                        mapping=args.mapping)
        if keypoint is not None:
            from .keypoint import SHA256
            metadata.update(keypoint_model_sha256=SHA256, tensorflow=__import__('tensorflow').__version__)
        logs.joinpath(stem+'.json').write_text(json.dumps(metadata, indent=2), encoding='utf-8')
        if args.mapping:
            from arm_contracts.mock_arm import MockArm, render
            from arm_contracts.replay import ReplayWriter
            from .mapping import DRAG_TARGETS_M, MappingConfig
            from .mapping_session import MappingSession
            target_file = ReplayWriter(logs.joinpath(stem+'.ee_target.jsonl'), 'ee_target',
                                  camera=dict(width=metadata['width'], height=metadata['height'], f_px=calibration.focal_px),
                                  notes=f'classifier={args.classifier} palm_length_m={args.palm_length_m} principal_px={principal}')
            session = MappingSession(MockArm(), target_file)
            box = (MappingConfig().box_min_m, MappingConfig().box_max_m)
        with logs.joinpath(stem+'.frames.jsonl').open('w', encoding='utf-8') as frames, logs.joinpath(stem+'.csv').open('w', newline='', encoding='utf-8') as f, mp.tasks.vision.GestureRecognizer.create_from_options(options) as recognizer:
            writer = csv.writer(f)
            writer.writerow(['receipt_ms', 'gesture', 'score', 'output', 'inference_ms'])
            def emit(timestamp, gesture, score, code, inference):
                nonlocal previous
                if not args.changes_only or code != previous:
                    writer.writerow([timestamp, gesture, round(score, 4), code, round(inference, 2)])
                    f.flush()
                if code != previous:
                    print(f'{timestamp} ms | {gesture} | output={code}', flush=True)
                    previous = code
            emit(0, 'startup', 0, '00', 0)
            try:
                while True:
                    ok, frame = cap.read()
                    now = max(last_timestamp+1, int((time.monotonic()-start)*1000))
                    last_timestamp = now
                    if not ok:
                        raise RuntimeError('Camera frame read failed; output reset to 00. Restart after checking camera.')
                    frame = cv2.flip(frame, 1)
                    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
                    tick = time.monotonic()
                    result = recognizer.recognize_for_video(image, now)
                    elapsed = (time.monotonic()-tick)*1000
                    observation = extract_selected(result, control.side)
                    h, w = frame.shape[:2]
                    original_gesture = observation['gesture']
                    original_score = observation['score']
                    keypoint_ms = 0.0
                    if keypoint is not None and observation['hand_present']:
                        begin = time.monotonic()
                        observation['gesture'], observation['score'] = keypoint.predict(observation['landmarks'], w, h)
                        keypoint_ms = (time.monotonic()-begin)*1000
                    gesture, score = observation['gesture'], observation['score']
                    stale = elapsed + keypoint_ms > STALE_MS
                    code, wrist, scale = step(state, control, observation, stale, now, w, h)
                    if session:
                        session.step(control, metric, code, now)
                    interval = now-previous_receipt if previous_receipt is not None else None
                    previous_receipt = now
                    frame_index += 1
                    frames.write(json.dumps(dict(frame=frame_index, receipt_ms=now,
                        inference_ms=elapsed, frame_interval_ms=interval, label=label,
                        stale=stale, output=code, classifier=args.classifier,
                        depth_relative=depth.value, depth_raw=depth.raw, depth_active=depth.active,
                        palm_scale_px=scale, depth_reference_px=depth.reference,
                        assigned_hand=control.side, control_status=control.status,
                        screen_target=target.position, screen_raw=target.raw, target_active=target.active,
                        mediapipe_gesture=original_gesture, mediapipe_score=original_score,
                        keypoint_ms=keypoint_ms,
                        metric_position_m=metric.position_m if metric else None,
                        metric_z_m=metric.z_m if metric else None,
                        metric_active=metric.active if metric else None,
                        **(session.log_fields() if session else {}), **observation), allow_nan=False)+'\n')
                    if frame_index % 30 == 0:
                        frames.flush()
                    emit(now, gesture, score, code, elapsed)
                    h, w = frame.shape[:2]
                    for hand in result.hand_landmarks:
                        for point in hand:
                            cv2.circle(frame, (int(point.x*w), int(point.y*h)), 4, (0, 255, 0), -1)
                    lines = [f'Filtered output: {code}', f'{args.classifier}: {gesture} score={score:.2f}',
                             f'ARM 1: {control.side} | {control.status}',
                             f'Inference: {elapsed:.1f} ms  stale={stale}',
                             f'MediaPipe: {original_gesture} | Label: {label}', '1=palm 2=fist 0=other N=no hand U=unlabeled',
                             'Palm=01 Fist=10; holds while hand present | Q/Esc quit']
                    if metric and metric.z_m is not None:
                        lines.append(f'Metres: X={metric.position_m[0]:+.3f} Y={metric.position_m[1]:+.3f} Z={metric.z_m:.3f}')
                    for i, line in enumerate(lines):
                        cv2.putText(frame, line, (12, 28+i*28), cv2.FONT_HERSHEY_SIMPLEX, .52, (0, 255, 255), 2)
                    cv2.imshow(window, draw(frame, observation, stale, args.threshold, target, depth))
                    if session:
                        cv2.imshow('mock arm', render(session.arm, box=box, marks=DRAG_TARGETS_M))
                    key = cv2.waitKey(1) & 0xFF
                    if key in (27, ord('q')) or cv2.getWindowProperty(window, cv2.WND_PROP_VISIBLE) < 1:
                        break
                    if session and key == ord('r'):
                        session.reset()
                    if handle_key(chr(key), control, wrist, scale, now):
                        state = GestureOutput(args.threshold, args.dwell_ms, drop_ms=args.drop_ms)
                    target, depth = control.target, control.depth
                    label = {ord('1'): 'Open_Palm', ord('2'): 'Closed_Fist', ord('0'): 'Other',
                             ord('n'): 'No_hand', ord('u'): 'unlabeled'}.get(key, label)
            finally:
                emit(int((time.monotonic()-start)*1000), 'shutdown', 0, '00', 0)
    finally:
        if target_file:
            target_file.close()
        cap.release()
        cv2.destroyAllWindows()


if __name__ == '__main__':
    try:
        main()
    except (RuntimeError, ValueError) as exc:
        raise SystemExit(str(exc)) from exc
    except KeyboardInterrupt:
        pass
