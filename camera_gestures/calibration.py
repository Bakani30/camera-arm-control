"""Checkerboard camera calibration: focal length saved with its image resolution."""
import argparse
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path

MIN_VIEWS = 5


@dataclass(frozen=True)
class CameraCalibration:
    focal_px: float
    fx_px: float
    fy_px: float
    cx_px: float
    cy_px: float
    width: int
    height: int
    rms_px: float
    views: int

    def save(self, path):
        Path(path).write_text(json.dumps(asdict(self), indent=2)+'\n', encoding='utf-8')

    def mirrored_principal_px(self):
        """Principal point in the flipped frame the app feeds to MediaPipe."""
        return (self.width-self.cx_px, self.cy_px)

    def require_resolution(self, width, height):
        if (width, height) != (self.width, self.height):
            raise ValueError(f'Camera gives {width}x{height}; calibration is for {self.width}x{self.height}.')


def load_calibration(path):
    try:
        calibration = CameraCalibration(**json.loads(Path(path).read_text(encoding='utf-8')))
    except (OSError, TypeError, json.JSONDecodeError) as exc:
        raise ValueError(f'Cannot read calibration {path}: {exc}') from exc
    if not (isinstance(calibration.focal_px, (int, float)) and math.isfinite(calibration.focal_px)
            and calibration.focal_px > 0 and calibration.width > 0 and calibration.height > 0):
        raise ValueError(f'Calibration {path} has no usable focal length or resolution.')
    return calibration


def calibrate_views(image_points, pattern, square_m, width, height):
    """image_points: inner-corner arrays, one per view; pattern: (cols, rows)."""
    if len(image_points) < MIN_VIEWS:
        raise ValueError(f'Need at least {MIN_VIEWS} checkerboard views, got {len(image_points)}.')
    import cv2
    import numpy as np

    cols, rows = pattern
    grid = np.zeros((cols*rows, 3), np.float32)
    grid[:, :2] = np.mgrid[0:cols, 0:rows].T.reshape(-1, 2)*square_m
    # A webcam and a few views: fitting fewer distortion terms keeps f stable.
    flags = cv2.CALIB_ZERO_TANGENT_DIST | cv2.CALIB_FIX_K3
    rms, camera, _, _, _ = cv2.calibrateCamera([grid]*len(image_points), image_points, (width, height),
                                               None, None, flags=flags)
    fx, fy = float(camera[0, 0]), float(camera[1, 1])
    return CameraCalibration((fx+fy)/2, fx, fy, float(camera[0, 2]), float(camera[1, 2]),
                             width, height, float(rms), len(image_points))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--camera', type=int, default=0)
    parser.add_argument('--width', type=int, default=1280)
    parser.add_argument('--height', type=int, default=720)
    parser.add_argument('--cols', type=int, default=9, help='inner corners across')
    parser.add_argument('--rows', type=int, default=6, help='inner corners down')
    parser.add_argument('--square-mm', type=float, required=True, help='printed square size, measured with a ruler')
    parser.add_argument('--views', type=int, default=15)
    parser.add_argument('--out', type=Path, default=Path('logs/camera_calibration.json'))
    args = parser.parse_args()
    import cv2

    pattern = (args.cols, args.rows)
    cap = cv2.VideoCapture(args.camera)
    views = []
    window = 'Calibration - Space to capture, Q or Esc to finish'
    try:
        if not cap.isOpened():
            raise RuntimeError('Camera unavailable. Close other camera apps; check Windows camera permissions or --camera 1.')
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, args.width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, args.height)
        while len(views) < args.views:
            ok, frame = cap.read()
            if not ok:
                raise RuntimeError('Camera frame read failed.')
            height, width = frame.shape[:2]
            if (width, height) != (args.width, args.height):
                raise ValueError(f'Camera gives {width}x{height}, not {args.width}x{args.height}.')
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            found, corners = cv2.findChessboardCorners(gray, pattern)
            cv2.drawChessboardCorners(frame, pattern, corners, found)
            cv2.putText(frame, f'{len(views)}/{args.views} found={found}', (12, 28),
                        cv2.FONT_HERSHEY_SIMPLEX, .7, (0, 255, 255), 2)
            cv2.imshow(window, frame)
            key = cv2.waitKey(1) & 0xFF
            if key in (27, ord('q')):
                break
            if key == ord(' ') and found:
                criteria = (cv2.TERM_CRITERIA_EPS+cv2.TERM_CRITERIA_MAX_ITER, 30, .001)
                views.append(cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria))
    finally:
        cap.release()
        cv2.destroyAllWindows()
    calibration = calibrate_views(views, pattern, args.square_mm/1000, args.width, args.height)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    calibration.save(args.out)
    print(f'f={calibration.focal_px:.1f} px at {args.width}x{args.height}, '
          f'rms={calibration.rms_px:.3f} px, {calibration.views} views -> {args.out}')


if __name__ == '__main__':
    try:
        main()
    except (RuntimeError, ValueError) as exc:
        raise SystemExit(str(exc)) from exc
