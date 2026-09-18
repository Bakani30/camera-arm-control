"""Local webcam preview. Outputs are display/log values, never robot commands."""
import argparse
import csv
import json
import platform
import time
from datetime import datetime, timezone
from pathlib import Path
from .state import GestureOutput
from .download_model import MODEL


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--camera', type=int, default=0)
    parser.add_argument('--model', type=Path, default=MODEL)
    parser.add_argument('--threshold', type=float, default=.7)
    parser.add_argument('--dwell-ms', type=int, default=250)
    parser.add_argument('--drop-ms', type=int, default=None)
    parser.add_argument('--changes-only', action='store_true', help='Log to CSV only when output code changes (default logs all frames)')
    args = parser.parse_args()
    state = GestureOutput(args.threshold, args.dwell_ms, drop_ms=args.drop_ms)
    if not args.model.is_file():
        parser.error('Model missing. Run: python -m camera_gestures.download_model')
    import cv2
    import mediapipe as mp

    options = mp.tasks.vision.GestureRecognizerOptions(
        base_options=mp.tasks.BaseOptions(model_asset_path=str(args.model)),
        running_mode=mp.tasks.vision.RunningMode.VIDEO,
        num_hands=1,
    )
    logs = Path('logs')
    logs.mkdir(exist_ok=True)
    stem = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    cap = cv2.VideoCapture(args.camera)
    start = time.monotonic()
    last_timestamp = -1
    previous = None
    window = 'Camera gestures - Q or Esc to quit'
    try:
        if not cap.isOpened():
            raise RuntimeError('Camera unavailable. Close other camera apps; check Windows camera permissions or --camera 1.')
        metadata = dict(platform=platform.platform(), python=platform.python_version(),
                        mediapipe=mp.__version__, opencv=cv2.__version__, camera=args.camera,
                        width=cap.get(cv2.CAP_PROP_FRAME_WIDTH), height=cap.get(cv2.CAP_PROP_FRAME_HEIGHT),
                        reported_fps=cap.get(cv2.CAP_PROP_FPS), threshold=args.threshold,
                        dwell_ms=args.dwell_ms, drop_ms=state.drop_ms,
                        log_mode='changes_only' if args.changes_only else 'all_frames',
                        timestamp='monotonic frame receipt, milliseconds',
                        model=str(args.model.resolve()))
        logs.joinpath(stem+'.json').write_text(json.dumps(metadata, indent=2), encoding='utf-8')
        with logs.joinpath(stem+'.csv').open('w', newline='', encoding='utf-8') as f, mp.tasks.vision.GestureRecognizer.create_from_options(options) as recognizer:
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
                    gesture, score = 'No_hand', 0.0
                    if result.gestures and result.gestures[0]:
                        top = max(result.gestures[0], key=lambda x: x.score)
                        gesture, score = top.category_name, top.score
                    if elapsed > 500:
                        gesture, score = 'Stale_result', 0.0
                    code = state.update(gesture, score, now)
                    emit(now, gesture, score, code, elapsed)
                    h, w = frame.shape[:2]
                    for hand in result.hand_landmarks:
                        for point in hand:
                            cv2.circle(frame, (int(point.x*w), int(point.y*h)), 4, (0, 255, 0), -1)
                    for i, line in enumerate([f'Output: {code}', f'{gesture} score={score:.2f}',
                                              f'Inference: {elapsed:.1f} ms', 'Palm=01  Fist=10  Unknown=00', 'Q / Esc: quit']):
                        cv2.putText(frame, line, (12, 28+i*28), cv2.FONT_HERSHEY_SIMPLEX, .65, (0, 255, 255), 2)
                    cv2.imshow(window, frame)
                    if cv2.waitKey(1) & 0xFF in (27, ord('q')) or cv2.getWindowProperty(window, cv2.WND_PROP_VISIBLE) < 1:
                        break
            finally:
                emit(int((time.monotonic()-start)*1000), 'shutdown', 0, '00', 0)
    finally:
        cap.release()
        cv2.destroyAllWindows()


if __name__ == '__main__':
    try:
        main()
    except (RuntimeError, ValueError) as exc:
        raise SystemExit(str(exc)) from exc
    except KeyboardInterrupt:
        pass
