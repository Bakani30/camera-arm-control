"""Replay a recorded frames.jsonl through the post-MediaPipe logic.

No camera and no MediaPipe inference: logged landmarks, gesture/score, stale
flags and receipt timestamps are fed to the same step() the live app uses.
"""
import argparse
import json
import math
from pathlib import Path
from .control import HandControl
from .pipeline import handle_key, step
from .state import GestureOutput

CENTRE = (.5, .5)
MANUAL_PAUSE = 'MANUAL PAUSE - C TO RESUME'
UNARMED = ('PRESS C TO START', MANUAL_PAUSE, 'HAND CHANGED - PRESS C')
# Inputs replay needs, plus the logged outputs it is compared against.
FIXTURE_FIELDS = ('frame', 'receipt_ms', 'stale', 'hand_present', 'handedness', 'gesture', 'score',
                  'landmarks', 'output', 'screen_target', 'screen_raw', 'target_active',
                  'depth_relative', 'depth_active', 'control_status', 'assigned_hand',
                  'palm_scale_px', 'depth_raw', 'depth_reference_px')
SETTINGS = ('width', 'height', 'threshold', 'dwell_ms', 'drop_ms', 'assigned_hand')


def load(path):
    path = Path(path)
    records = [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]
    meta = json.loads(path.with_name(path.name.replace('.frames.jsonl', '.json')).read_text(encoding='utf-8'))
    return records, meta


def infer_keys(records):
    """Recover C/Space/L/H presses from logged status; the app does not log keys.

    A key pressed after frame N shows up in frame N+1. Arming is C or R: R
    rebases the target at exactly screen centre, C at the held position. C or
    R pressed while already active leaves the status unchanged; it is found
    when frame N+1's raw target is exactly a fresh anchor at frame N, which
    ordinary tracking does not produce.
    """
    keys = {}
    for prev, record in zip(records, records[1:]):
        before, after = prev['control_status'], record['control_status']
        if record['assigned_hand'] != prev['assigned_hand']:
            keys[prev['frame']] = 'l' if record['assigned_hand'] == 'Left' else 'h'
        elif after == MANUAL_PAUSE and before != MANUAL_PAUSE:
            keys[prev['frame']] = ' '
        elif before in UNARMED and after not in UNARMED:
            # Held at centre the two keys act alike; call it C.
            reset = (tuple(prev['screen_target']) != CENTRE
                     and (tuple(record['screen_raw']) == CENTRE or _rebased(CENTRE, prev, record)))
            keys[prev['frame']] = 'r' if reset else 'c'
        elif before == after == 'ACTIVE':
            for key, anchor in (('c', prev['screen_target']), ('r', CENTRE)):
                if _rebased(anchor, prev, record):
                    keys[prev['frame']] = key
    return keys


def _rebased(anchor, prev, record):
    if not (prev['hand_present'] and record['hand_present']) or prev['stale'] or record['stale']:
        return False
    w0, w1 = prev['landmarks'][0][:2], record['landmarks'][0][:2]
    raw = tuple(a + (v-o) for a, v, o in zip(anchor, w1, w0))
    # Clipped values cannot tell a rebase from tracking.
    return all(0 < v < 1 for v in raw) and raw == tuple(record['screen_raw'])


def _resume(control, first):
    """Start mid-recording: only armed state and held XYZ carry over a no-hand frame."""
    if first['hand_present'] or first['output'] != '00' or first['target_active'] or first['depth_active']:
        raise ValueError('resume needs a first frame with no hand, output 00 and paused XYZ')
    control.armed = first['control_status'] not in UNARMED
    control.status = first['control_status']
    control.target.position, control.target.raw = tuple(first['screen_target']), tuple(first['screen_raw'])
    control.depth.value, control.depth.raw = first['depth_relative'], first['depth_raw']
    control.depth.reference = first['depth_reference_px']
    control.side = first['assigned_hand']


def replay(records, width, height, assigned_hand='Right', threshold=.7, dwell_ms=250,
           drop_ms=None, keys=None, resume=False):
    """Return per-frame outputs; keys maps frame -> key pressed after that frame."""
    keys = keys or {}
    state = GestureOutput(threshold, dwell_ms, drop_ms=drop_ms)
    control = HandControl(assigned_hand)
    if resume:
        _resume(control, records[0])
    results = []
    for record in records:
        now = record['receipt_ms']
        observation = {k: record[k] for k in ('hand_present', 'gesture', 'score', 'landmarks')}
        code, wrist, scale = step(state, control, observation, record['stale'], now, width, height)
        results.append(dict(frame=record['frame'], receipt_ms=now, output=code,
                            screen_target=control.target.position, screen_raw=control.target.raw,
                            target_active=control.target.active, depth_relative=control.depth.value,
                            depth_active=control.depth.active, control_status=control.status,
                            assigned_hand=control.side, palm_scale_px=scale, depth_raw=control.depth.raw,
                            depth_reference_px=control.depth.reference))
        key = keys.get(record['frame'])
        if key is not None and handle_key(key, control, wrist, scale, now):
            state = GestureOutput(threshold, dwell_ms, drop_ms=drop_ms)
    return results


def replay_file(path):
    records, meta = load(path)
    settings = {k: meta[k] for k in SETTINGS if k in meta}
    keys = {int(frame): key for frame, key in meta['keys']} if 'keys' in meta else infer_keys(records)
    return records, replay(records, keys=keys, resume=meta.get('resume', False), **settings)


def compare(records, results, xy_tol=1e-9, depth_tol=1e-9):
    """List (frame, field, logged, replayed) where replay departs from the log."""
    mismatches = []
    for record, result in zip(records, results):
        for field in ('output', 'target_active', 'depth_active', 'control_status', 'assigned_hand'):
            if record[field] != result[field]:
                mismatches.append((record['frame'], field, record[field], result[field]))
        for field, tol in (('screen_target', xy_tol), ('screen_raw', xy_tol), ('depth_relative', depth_tol),
                           ('depth_raw', depth_tol), ('palm_scale_px', xy_tol), ('depth_reference_px', xy_tol)):
            logged, replayed = record[field], result[field]
            if logged is None or replayed is None:
                close = logged is replayed
            elif isinstance(logged, list):
                close = all(math.isclose(a, b, abs_tol=tol) for a, b in zip(logged, replayed))
            else:
                close = math.isclose(logged, replayed, abs_tol=tol)
            if not close:
                mismatches.append((record['frame'], field, logged, replayed))
    return mismatches


def excerpt(path, first, last, out, resume=False):
    """Write frames first..last as a fixture: inputs and logged outputs only, no paths."""
    records, meta = load(path)
    keys = infer_keys(records)
    chosen = [{k: r[k] for k in FIXTURE_FIELDS} for r in records if first <= r['frame'] <= last]
    if not chosen:
        raise ValueError(f'no frames between {first} and {last}')
    for r in chosen:  # Post-MediaPipe logic reads x, y only.
        r['landmarks'] = [p[:2] for p in r['landmarks']]
    out = Path(out)
    out.with_name(out.name + '.frames.jsonl').write_text(
        ''.join(json.dumps(r) + '\n' for r in chosen), encoding='utf-8')
    fixture_meta = {k: meta[k] for k in SETTINGS + ('classifier', 'mediapipe', 'mirrored')}
    fixture_meta.update(source=Path(path).name,
                        frames=[first, last], resume=resume,
                        keys=[[f, k] for f, k in sorted(keys.items()) if first <= f <= last])
    out.with_name(out.name + '.json').write_text(json.dumps(fixture_meta, indent=2) + '\n', encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('log', type=Path, help='path to <stamp>.frames.jsonl')
    parser.add_argument('--excerpt', nargs=2, type=int, metavar=('FIRST', 'LAST'))
    parser.add_argument('--out', type=Path, help='fixture stem for --excerpt')
    parser.add_argument('--resume', action='store_true', help='excerpt starts mid-recording')
    args = parser.parse_args()
    if args.excerpt:
        if args.out is None:
            parser.error('--excerpt needs --out')
        excerpt(args.log, *args.excerpt, args.out, args.resume)
        return 0
    records, results = replay_file(args.log)
    mismatches = compare(records, results)
    print(f'{len(records)} frames, {len(mismatches)} mismatches')
    for mismatch in mismatches[:20]:
        print(*mismatch)
    return 1 if mismatches or not records else 0


if __name__ == '__main__':
    raise SystemExit(main())
