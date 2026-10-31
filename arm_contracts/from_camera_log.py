"""Turn a camera log (logs/*.frames.jsonl) into ee_target messages for the Friday chain.

The box mapping here is a placeholder: screen and depth proxy are not metres. P002 and P006 (lane A)
replace it, and this module should go away with them. Nothing here is a measure of accuracy.
"""
import argparse
from pathlib import Path

from arm_contracts.messages import ContractError, EndEffectorTarget, load_line
from arm_contracts.replay import write_replay
from arm_contracts.scripted import DEFAULT_CENTER, ROBOT_ID

BOX_HALF_M = (0.08, 0.12, 0.08)  # forward, left, up
GRIP_BY_CODE = {'01': 0.0, '10': 1.0}  # palm opens, fist closes; 00 keeps the last grip


def _clamp(value, low, high):
    return max(low, min(high, value))


def targets_from_frames(lines, robot_id=ROBOT_ID, center=DEFAULT_CENTER, half=BOX_HALF_M):
    targets, grip = [], 0.0
    for line in lines:
        frame = load_line(line)
        if 'screen_target' not in frame:
            raise ContractError(f"frame {frame.get('frame')}: no screen_target, log is older than HandControl")
        screen_x, screen_y = frame['screen_target']
        depth = frame.get('depth_relative') or 0.0
        grip = GRIP_BY_CODE.get(frame.get('output'), grip)
        # anything but a clear yes holds: a missing or odd field must not mean track
        tracking = frame.get('target_active') is True and frame.get('hand_present') is True and frame.get('stale') is False
        position = (center[0] + half[0] * _clamp(depth, -1.0, 1.0),
                    center[1] - half[1] * 2 * (_clamp(screen_x, 0.0, 1.0) - 0.5),
                    center[2] - half[2] * 2 * (_clamp(screen_y, 0.0, 1.0) - 0.5))
        targets.append(EndEffectorTarget(t_ms=frame['receipt_ms'], seq=frame['frame'], robot_id=robot_id,
                                         position_m=tuple(round(v, 6) for v in position), grip=grip,
                                         mode='track' if tracking else 'hold', enabled=True, source='replay'))
    return targets


def main(argv=None):
    parser = argparse.ArgumentParser(description='Convert a camera frames.jsonl log to an ee_target replay file.')
    parser.add_argument('frames', type=Path)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args(argv)
    targets = targets_from_frames(args.frames.read_text(encoding='utf-8').splitlines())
    write_replay(args.out, 'ee_target', targets, notes=f'placeholder box mapping from {args.frames.name}; not metric')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
