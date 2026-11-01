"""Numbers for the M0 camera checks, from an ee_target file. Reads files only; moves nothing."""
import argparse
import math
from pathlib import Path
from statistics import pstdev

from arm_contracts.replay import read_replay

from .mapping import DRAG_TARGETS_M


def track_segments(messages):
    """One entry per unbroken run of track messages. Take the hand out of frame between trials to split them."""
    runs, current = [], []
    for m in messages:
        if m.mode == 'track':
            current.append(m)
        elif current:
            runs.append(current)
            current = []
    if current:
        runs.append(current)
    return [dict(seconds=(run[-1].t_ms-run[0].t_ms)/1000,
                 net_m=tuple(b-a for a, b in zip(run[0].position_m, run[-1].position_m)),
                 std_mm=tuple(1000*pstdev(axis) for axis in zip(*(m.position_m for m in run))))
            for run in runs]


def target_times(messages, targets, radius_m=.01, dwell_ms=1000):
    """Seconds to settle on each target in turn, timed from the previous one; None from the first one missed."""
    times = [None]*len(targets)
    index, started, entered = 0, messages[0].t_ms if messages else 0, None
    for m in messages:
        if index == len(targets):
            break
        if m.mode != 'track' or math.dist(m.position_m, targets[index]) > radius_m:
            entered = None
            continue
        if entered is None:
            entered = m.t_ms
        if m.t_ms-entered >= dwell_ms:
            times[index] = (m.t_ms-started)/1000
            index, started, entered = index+1, m.t_ms, None
    return times


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('replay', type=Path)
    parser.add_argument('--targets', action='store_true', help='also time the numbered targets shown on the mock arm')
    args = parser.parse_args(argv)
    _, messages = read_replay(args.replay)
    for i, s in enumerate(track_segments(messages), start=1):
        net = ' '.join(f'{100*v:+.1f}' for v in s['net_m'])
        std = ' '.join(f'{v:.2f}' for v in s['std_mm'])
        print(f"segment {i}: {s['seconds']:.1f} s | net x y z cm: {net} | std x y z mm: {std}")
    if args.targets:
        for i, t in enumerate(target_times(messages, DRAG_TARGETS_M), start=1):
            print(f"target {i}: {'not reached' if t is None else f'{t:.1f} s'}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
