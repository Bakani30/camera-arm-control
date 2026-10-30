"""On-screen stand-in for a real arm: draws the end-effector target. Runs no IK and moves no hardware."""
import argparse
from collections import deque
from pathlib import Path

import cv2
import numpy as np

from arm_contracts.messages import EndEffectorTarget, Receiver
from arm_contracts.profiles import small_arm_profile
from arm_contracts.replay import read_replay

TRAIL = 400
PANEL = 440
MARGIN = 20
METRES = 0.5  # the panels show this much
GRID = 0.1
COLORS = dict(moving=(90, 220, 90), waiting=(160, 160, 160))
STOP_COLOR = (60, 60, 240)


class MockArm:
    """The point follows targets the receiver lets through and freezes on anything else (contract section 6)."""

    def __init__(self, profile=None):
        self.receiver = Receiver(EndEffectorTarget, profile or small_arm_profile())
        self.position = None
        self.grip = 0.0
        self.status = 'waiting'
        self.problem = None
        self.trail = deque(maxlen=TRAIL)

    def receive(self, data, now_ms):
        got = self.receiver.receive(data, now_ms)
        self.problem = got.problem
        self.status = got.stop or 'moving'
        if got.stop is None:
            self.position = got.message.position_m
            self.grip = got.message.grip
            self.trail.append(self.position)


def _top(p):  # looking down: forward is up the panel, the robot's left is left
    scale = (PANEL - 2 * MARGIN) / METRES
    return int(PANEL / 2 - p[1] * scale), int(PANEL - MARGIN - p[0] * scale)


def _side(p):  # from the robot's right: forward is right, up is up
    scale = (PANEL - 2 * MARGIN) / METRES
    return int(PANEL + MARGIN + p[0] * scale), int(PANEL - MARGIN - p[2] * scale)


def _grid(image, x0, y0):
    size = PANEL - 2 * MARGIN
    for i in range(int(METRES / GRID) + 1):
        step = int(i * size * GRID / METRES)
        cv2.line(image, (x0, y0 + step), (x0 + size, y0 + step), (55, 55, 55), 1)
        cv2.line(image, (x0 + step, y0), (x0 + step, y0 + size), (55, 55, 55), 1)


def render(arm):
    image = np.full((PANEL + 60, 2 * PANEL, 3), 30, dtype=np.uint8)
    _grid(image, MARGIN, MARGIN)
    _grid(image, PANEL + MARGIN, MARGIN)
    color = COLORS.get(arm.status, STOP_COLOR)
    for project in (_top, _side):
        points = np.array([project(p) for p in arm.trail], dtype=np.int32)
        if len(points) > 1:
            cv2.polylines(image, [points], False, (150, 150, 90), 1)
        if arm.position is not None:
            cv2.circle(image, project(arm.position), 6, color, -1)
    cv2.putText(image, 'top (grid 10 cm)', (MARGIN, PANEL + 14), cv2.FONT_HERSHEY_SIMPLEX, .45, (200, 200, 200), 1)
    cv2.putText(image, 'side', (PANEL + MARGIN, PANEL + 14), cv2.FONT_HERSHEY_SIMPLEX, .45, (200, 200, 200), 1)
    where = 'no target' if arm.position is None else ' '.join(f'{v:+.3f}' for v in arm.position) + ' m'
    cv2.putText(image, f'{arm.status} | {where} | grip {arm.grip:.2f}', (MARGIN, PANEL + 42),
                cv2.FONT_HERSHEY_SIMPLEX, .55, color, 1)
    return image


def main(argv=None):
    parser = argparse.ArgumentParser(description='Play an ee_target replay file on the mock arm.')
    parser.add_argument('replay', type=Path)
    parser.add_argument('--save', type=Path, help='run with no window and save the last picture (PNG)')
    parser.add_argument('--speed', type=float, default=1.0)
    args = parser.parse_args(argv)
    _, messages = read_replay(args.replay)
    arm = MockArm()
    previous = None
    for message in messages:
        arm.receive(message, message.t_ms)
        if args.save:
            continue
        cv2.imshow('mock arm', render(arm))
        wait = 1 if previous is None else max(1, int((message.t_ms - previous) / args.speed))
        previous = message.t_ms
        if cv2.waitKey(wait) & 0xFF in (ord('q'), 27):
            break
    if args.save:  # imencode + write_bytes: cv2.imwrite fails on non-ASCII paths on Windows
        args.save.write_bytes(cv2.imencode('.png', render(arm))[1].tobytes())
    else:
        cv2.destroyAllWindows()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
