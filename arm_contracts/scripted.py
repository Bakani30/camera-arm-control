"""Scripted end-effector targets, so lanes B and C can run without a camera."""
import argparse
import math
from pathlib import Path

from arm_contracts.messages import EndEffectorTarget
from arm_contracts.replay import write_replay
from arm_spec import forward_kinematics, load_spec

SAMPLE_REPLAY = Path(__file__).with_name('samples') / 'demo.ee_target.jsonl'
SAMPLE_CREATED = '2026-10-31T00:00:00+00:00'
DEFAULT_CENTER = (0.25, 0.0, 0.12)  # in front of the base, inside the soft limits (tests check this)
ROBOT_ID = 'small_arm'
TRACK = dict(mode='track', enabled=True)


def _stream(steps, dt_ms, robot_id=ROBOT_ID, grip=0.0):
    """Targets from (position, extra fields) steps. Rounding to 1 um keeps files equal across platforms."""
    return [EndEffectorTarget(t_ms=i * dt_ms, seq=i + 1, robot_id=robot_id, grip=grip, source='script',
                              position_m=tuple(round(v, 6) for v in position), **{**TRACK, **extra})
            for i, (position, extra) in enumerate(steps)]


def _circle_positions(center, radius, points):
    return [(center[0] + radius * math.cos(2 * math.pi * i / points),
             center[1] + radius * math.sin(2 * math.pi * i / points), center[2]) for i in range(points)]


def circle(center=DEFAULT_CENTER, radius=0.04, points=64, period_s=8.0, robot_id=ROBOT_ID, grip=0.0):
    steps = [(p, {}) for p in _circle_positions(center, radius, points)]
    return _stream(steps, period_s * 1000 / points, robot_id, grip)


def square(center=DEFAULT_CENTER, half_side=0.04, points_per_side=16, period_s=8.0, robot_id=ROBOT_ID, grip=0.0):
    corners = [(half_side, half_side), (-half_side, half_side), (-half_side, -half_side), (half_side, -half_side)]
    steps = []
    for (ax, ay), (bx, by) in zip(corners, corners[1:] + corners[:1]):
        for i in range(points_per_side):
            f = i / points_per_side
            steps.append(((center[0] + ax + (bx - ax) * f, center[1] + ay + (by - ay) * f, center[2]), {}))
    return _stream(steps, period_s * 1000 / len(steps), robot_id, grip)


def known_points(spec=None):
    """(pose, target) pairs whose target is the FK of the pose: ground truth for testing IK."""
    spec = spec or load_spec()
    deg = math.radians
    poses = ({},
             {'shoulder_pan': deg(25), 'shoulder_lift': deg(-15), 'elbow_flex': deg(35), 'wrist_flex': deg(40)},
             {'shoulder_lift': deg(30), 'elbow_flex': deg(-45), 'wrist_flex': deg(80)})
    targets = _stream([(forward_kinematics(spec, q), {}) for q in poses], 1000.0)
    return list(zip(poses, targets))


def demo():
    """The sample replay: one circle, then a hold, a disable and a return. The held targets jump away on purpose."""
    path = _circle_positions(DEFAULT_CENTER, 0.04, 32)
    away = (DEFAULT_CENTER[0], DEFAULT_CENTER[1] + 0.08, DEFAULT_CENTER[2])
    steps = [(p, {}) for p in path]
    steps += [(away, {'mode': 'hold'})] * 4 + [(away, {'enabled': False})] * 4 + [(path[0], {})] * 4
    return _stream(steps, 125.0)


def main(argv=None):
    parser = argparse.ArgumentParser(description='Write a scripted ee_target replay file.')
    parser.add_argument('shape', choices=('circle', 'square', 'demo'))
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--created', default=None, help='ISO-8601 header time (default now)')
    args = parser.parse_args(argv)
    messages = dict(circle=circle, square=square, demo=demo)[args.shape]()
    write_replay(args.out, 'ee_target', messages, created=args.created, notes=f'scripted {args.shape}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
