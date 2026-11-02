"""Noise and crosstalk numbers from an axis bench file. Reads files only; moves nothing."""
import argparse
import json
import math
from collections import Counter
from pathlib import Path
from statistics import median, pstdev

from .axis_estimators import REACH_METHODS, SCALES, BenchContext, base_gain, hand_angles, position_m
from .metric import _usable

EXPECTED_TRIALS = ('A_near', 'A_mid', 'A_far', 'B', 'C', 'D', 'E', 'F_pitch', 'F_roll')
POINTS = ('wrist', 'center')
TAU_MS = 120
NEUTRAL_MS = 1000
MAX_LOST_PCT = 10
MIN_FPS = 12
MIN_NEUTRAL_SEEN = .8
MAX_NEUTRAL_SPREAD = .04      # of the palm's image length or width
MAX_NEUTRAL_SD_MM = 5         # of reach, at scale 1
MAX_NEUTRAL_SHAPE_ERROR = .25  # width/length against the ruler; a bent palm reads narrower one way
DEFAULT_PALM_SHAPE = .8        # width/length, used only when no open palm was ever seen
MAX_SD_MM = 3
MAX_DRIFT_MM = 10
PITCH_JUDGED_DEG = 35
MAX_CROSSTALK_PCT = 25
Z_FIT_STEP = .05
Z_FIT_STEPS = 60              # gains 0 to 3: z down to about a third of true
# Motion gates read image lengths, not hand_angles: a poor z must not hide a real tilt.
MIN_LENGTH_CHANGE_PCT = {'B': 15, 'C': 10, 'F_pitch': 10}
MIN_WIDTH_CHANGE_PCT = {'D': 15, 'F_roll': 15}
MIN_GESTURE_CHANGES = 10      # five fist-open cycles in trial E


def read_log(path):
    """Header, frames, completed trials. A cut-off last line is fine: the run may have been closed."""
    lines = [line for line in Path(path).read_text(encoding='utf-8').split('\n') if line.strip()]
    records = []
    for i, line in enumerate(lines):
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            if i != len(lines)-1:
                raise ValueError(f'{path}: line {i+1} is not JSON') from None
    if not records or records[0].get('kind') != 'header':
        raise ValueError(f'{path}: no header')
    frames, completed = [], set()
    for record in records[1:]:
        kind = record.get('kind')
        if kind == 'frame':
            frames.append(record)
        elif kind == 'trial_end':
            completed.add(record['trial'])
        elif kind == 'retry':
            completed.discard(record['trial'])
            for frame in frames:
                if frame['trial'] == record['trial']:
                    frame['trial'] = record['as_trial']
    return records[0], frames, completed


def _context(header, frames):
    """Without a ruler value, the palm's width comes from its proportions at the open-palm start of each trial."""
    ctx = BenchContext(header['width'], header['height'], header['focal_px'], header['palm_length_m'],
                       header.get('palm_width_m'), tuple(header['principal_px']))
    if ctx.palm_width_m is not None:
        return ctx
    starts, shapes = {}, []
    for f in _seen(frames, ctx):
        start = starts.setdefault(f['trial'], f['t_ms'])
        length, width = _lengths(f, ctx)
        if f['t_ms']-start <= NEUTRAL_MS and length > 0:
            shapes.append(width/length)
    return ctx._replace(palm_width_m=ctx.palm_m*(median(shapes) if shapes else DEFAULT_PALM_SHAPE))


def _seen(frames, ctx):
    return [f for f in frames if f['hand_present'] and _usable(f['landmarks'], ctx.width, ctx.height)]


def _lengths(frame, ctx):
    p = frame['landmarks']
    def px(a, b):
        return math.hypot((p[a][0]-p[b][0])*ctx.width, (p[a][1]-p[b][1])*ctx.height)
    return px(0, 9), px(5, 17)


def _fit_grid(frames, ctx):
    best, best_sd = None, math.inf
    for step in range(Z_FIT_STEPS+1):
        gain = step*Z_FIT_STEP
        reach = [REACH_METHODS['z_perspective'](f['landmarks'], ctx, gain) for f in frames]
        reach = [r for r in reach if r is not None]
        if len(reach) > 1 and pstdev(reach) < best_sd:
            best, best_sd = gain, pstdev(reach)
    return best


def fit_z_gain(frames, ctx):
    """The z gain that keeps the reach steadiest through trial C, where only the wrist angle should change."""
    return _fit_grid(_seen([f for f in frames if f['trial'] == 'C'], ctx), ctx)


def _filtered(samples):
    """First-order low-pass over (t_ms, values); same tau as the depth filter in the mapper."""
    out, state, last = [], None, None
    for t, values in samples:
        if state is None:
            state = list(values)
        else:
            alpha = 1-math.exp(-max(0, t-last)/TAU_MS)
            state = [s+alpha*(v-s) for s, v in zip(state, values)]
        last = t
        out.append((t, list(state)))
    return out


def _axes(frames, ctx, read, point):
    """(t_ms, [reach, lateral, vertical]) in metres for every frame this reading can use."""
    samples = []
    for f in frames:
        z = read(f['landmarks'], ctx)
        if z is not None:
            samples.append((f['t_ms'], [z, *position_m(f['landmarks'], ctx, z, point)]))
    return _filtered(samples)


def _sd_row(series, gain):
    sds = [pstdev(column)*gain*1000 for column in zip(*(values for _, values in series))]
    return sds, sds[0] <= MAX_SD_MM


def _stroke_row(series, gain):
    """The push has no set length, so there is no pass mark: a wrong scale is what the scale setting is for."""
    columns = list(zip(*(values for _, values in series)))
    return [(max(c)-min(c))*gain*1000 for c in columns], None


def _drift_row(series, gain):
    start = series[0][0]
    neutral = [values for t, values in series if t-start <= NEUTRAL_MS]
    rest = [values for t, values in series if t-start > NEUTRAL_MS] or neutral
    base = [median(column) for column in zip(*neutral)]
    drift = [max(abs(values[i]-base[i]) for values in rest)*gain*1000 for i in range(3)]
    return drift, max(drift) <= MAX_DRIFT_MM


def _rows(trial, series, gain):
    if trial.startswith('A_'):
        return _sd_row(series, gain)
    if trial == 'B':
        return _stroke_row(series, gain)
    return _drift_row(series, gain)


def _angle_series(frames, ctx):
    read = [(f['t_ms'], hand_angles(f['landmarks'], ctx)) for f in frames]
    return _filtered([(t, a) for t, a in read if a is not None])


def _angles(frames, ctx):
    series = [values for _, values in _angle_series(frames, ctx)]
    if not series:
        return {}
    pitch, roll = zip(*series)
    return dict(pitch_sd_deg=pstdev(pitch), roll_sd_deg=pstdev(roll),
                pitch_range_deg=max(pitch)-min(pitch), roll_range_deg=max(roll)-min(roll))


def _motion(frames, ctx):
    """How much the trial really moved, from the palm's image lengths and the gesture labels."""
    lengths = _filtered([(f['t_ms'], _lengths(f, ctx)) for f in frames])
    if not lengths:
        return dict(length_change_pct=0, width_change_pct=0, gesture_changes=0)
    length, width = zip(*(values for _, values in lengths))
    gestures = [f['gesture'] for f in frames if f['gesture'] in ('Open_Palm', 'Closed_Fist')]
    return dict(length_change_pct=100*(1-min(length)/max(length)), width_change_pct=100*(1-min(width)/max(width)),
                gesture_changes=sum(a != b for a, b in zip(gestures, gestures[1:])))


def _within_pitch_limit(frames, ctx):
    """Set C goes to the tracking limit, but its pass mark is about the ±30 degree part."""
    start = frames[0]['t_ms']
    head = [hand_angles(f['landmarks'], ctx) for f in frames if f['t_ms']-start <= NEUTRAL_MS]
    head = [a[0] for a in head if a is not None]
    if not head:
        return frames
    neutral = median(head)
    kept = []
    for f in frames:
        a = hand_angles(f['landmarks'], ctx)
        if a is not None and abs(a[0]-neutral) <= PITCH_JUDGED_DEG:
            kept.append(f)
    return kept or frames


def _neutral_problem(frames, ctx):
    start = frames[0]['t_ms']
    head = [f for f in frames if f['t_ms']-start <= NEUTRAL_MS]
    seen = _seen(head, ctx)
    if len(seen) < MIN_NEUTRAL_SEEN*len(head):
        return 'hand not seen during the neutral second'
    lengths, widths = zip(*(_lengths(f, ctx) for f in seen))
    if min(lengths) == 0 or min(widths) == 0:
        return 'neutral pose points at the camera'
    if max(pstdev(lengths)/(sum(lengths)/len(lengths)), pstdev(widths)/(sum(widths)/len(widths))) > MAX_NEUTRAL_SPREAD:
        return 'hand moved during the neutral second'
    reach = [REACH_METHODS['z_perspective'](f['landmarks'], ctx) for f in seen]
    reach = [z for z in reach if z is not None]
    if len(reach) > 1 and pstdev(reach)*base_gain()*1000 > MAX_NEUTRAL_SD_MM:
        return 'hand moved during the neutral second'
    shape = median(w/l for l, w in zip(lengths, widths))/(ctx.palm_width_m/ctx.palm_m)
    if abs(shape-1) > MAX_NEUTRAL_SHAPE_ERROR:
        return 'neutral pose not flat to the camera, or palm sizes off'
    return None


def _motion_problem(trial, motion):
    if motion['length_change_pct'] < MIN_LENGTH_CHANGE_PCT.get(trial, 0):
        return 'too little motion: palm length barely changed'
    if motion['width_change_pct'] < MIN_WIDTH_CHANGE_PCT.get(trial, 0):
        return 'too little motion: palm width barely changed'
    if trial == 'E' and motion['gesture_changes'] < MIN_GESTURE_CHANGES:
        return 'too little motion: too few fist-open changes'
    return None


def _status(trial, frames, seen, completed, ctx, motion):
    """(status, why) for a trial; only 'ok' is judged."""
    if trial not in completed:
        return 'incomplete', 'trial did not finish'
    if 100*(1-len(seen)/len(frames)) > MAX_LOST_PCT:
        return 'invalid', 'hand lost too often'
    gaps = [b['t_ms']-a['t_ms'] for a, b in zip(frames, frames[1:])]
    if gaps and 1000/median(gaps) < MIN_FPS:
        return 'invalid', 'frame rate too low'
    problem = _neutral_problem(frames, ctx) or _motion_problem(trial, motion)
    return ('invalid', problem) if problem else ('ok', None)


def _crosstalk(trial, frames, ctx):
    """How far the axis not commanded follows the commanded one: a slope, so noise alone reads near zero."""
    series = [values for _, values in _angle_series(frames, ctx)]
    if len(series) < 2:
        return None
    pitch, roll = zip(*series)
    told, other = (pitch, roll) if trial == 'F_pitch' else (roll, pitch)
    mean_told, mean_other = sum(told)/len(told), sum(other)/len(other)
    variance = sum((t-mean_told)**2 for t in told)
    if variance == 0:
        return None
    return 100*abs(sum((t-mean_told)*(o-mean_other) for t, o in zip(told, other))/variance)


def _summarize_trial(trial, frames, completed, ctx, fit):
    seen = _seen(frames, ctx)
    gaps = [b['t_ms']-a['t_ms'] for a, b in zip(frames, frames[1:])]
    motion = _motion(seen, ctx)
    status, reason = _status(trial, frames, seen, completed, ctx, motion)
    sides = Counter(f['side'] for f in seen if f.get('side'))
    result = dict(status=status, reason=reason, side=sides.most_common(1)[0][0] if sides else None,
                  lost_pct=100*(1-len(seen)/len(frames)),
                  median_fps=1000/median(gaps) if gaps and median(gaps) > 0 else None,
                  angles=_angles(seen, ctx), motion=motion, methods={})
    judged = status == 'ok'
    if trial.startswith('F_'):
        result['crosstalk_pct'] = _crosstalk(trial, seen, ctx)
        result['passed'] = None if not judged or result['crosstalk_pct'] is None else result['crosstalk_pct'] <= MAX_CROSSTALK_PCT
        return result
    within = _within_pitch_limit(seen, ctx) if trial == 'C' and seen else seen
    readers = dict(REACH_METHODS)
    if fit:
        readers['z_perspective_fit'] = lambda points, c: REACH_METHODS['z_perspective'](points, c, fit)
    for method, read in readers.items():
        for point in POINTS:
            series = _axes(within, ctx, read, point)
            if not series:
                continue
            scales = {}
            for scale in SCALES:
                values, passed = _rows(trial, series, base_gain()*scale)
                scales[str(scale)] = dict(reach_mm=values[0], lateral_mm=values[1], vertical_mm=values[2],
                                          passed=passed if judged else None)
            result['methods'].setdefault(method, {})[point] = dict(scale=scales)
    return result


def summarize(header, frames, completed):
    ctx = _context(header, [f for f in frames if '#retry' not in f['trial']])
    trials = {}
    for f in frames:
        if '#retry' not in f['trial']:
            trials.setdefault(f['trial'], []).append(f)
    fit = None
    if 'C' in trials:
        seen = _seen(trials['C'], ctx)
        if _status('C', trials['C'], seen, completed, ctx, _motion(seen, ctx))[0] == 'ok':
            fit = fit_z_gain(frames, ctx)
    return dict(header=header, z_gain_fit=fit, z_accuracy_pct=100/fit if fit else None,
                z_fit_at_edge=fit is not None and (fit <= 0 or fit >= Z_FIT_STEPS*Z_FIT_STEP),
                not_run=[name for name in EXPECTED_TRIALS if name not in trials],
                trials={name: _summarize_trial(name, group, completed, ctx, fit) for name, group in trials.items()})


def _verdict(passed):
    return 'not judged' if passed is None else 'pass' if passed else 'FAIL'


def format_table(summary):
    h = summary['header']
    lines = [f"camera {h['camera']} on {h['platform']} | calibration {h['calibration']}"
             + (' (provisional focal length)' if h['provisional'] else ''),
             (f"palm {100*h['palm_length_m']:.1f} x {100*h['palm_width_m']:.1f} cm by ruler" if h.get('palm_width_m')
              else f"palm size estimated from the open palm, mm are approximate (length assumed {100*h['palm_length_m']:.0f} cm)")
             + f" | note: {h['note'] or '-'}"]
    lines += [f'calibration warning: {w}' for w in h.get('calibration_warnings', [])]
    if summary['z_gain_fit'] is not None:
        accuracy = 'n/a' if summary['z_accuracy_pct'] is None else f"{summary['z_accuracy_pct']:.0f}%"
        edge = ' | at the edge of the search, so z may be worse' if summary['z_fit_at_edge'] else ''
        lines.append(f"z gain fit {summary['z_gain_fit']:.2f} (z about {accuracy} true){edge}")
    if summary['not_run']:
        lines.append(f"not run: {', '.join(summary['not_run'])}")
    for name, t in summary['trials'].items():
        fps = '-' if t['median_fps'] is None else f"{t['median_fps']:.0f}"
        why = f" ({t['reason']})" if t['reason'] else ''
        hand = f" | hand {t['side']}" if t['side'] else ''
        lines.append(f"\n{name}: {t['status']}{why} | lost {t['lost_pct']:.0f}% | {fps} fps{hand}")
        a, m = t['angles'], t['motion']
        if a:
            lines.append(f"  pitch range {a['pitch_range_deg']:.0f} deg, roll range {a['roll_range_deg']:.0f} deg | "
                         f"palm length change {m['length_change_pct']:.0f}%, width change {m['width_change_pct']:.0f}% | "
                         f"gesture changes {m['gesture_changes']}")
        if name.startswith('F_') and t.get('crosstalk_pct') is not None:
            lines.append(f"  crosstalk {t['crosstalk_pct']:.0f}% {_verdict(t['passed'])}")
        for method, points in t['methods'].items():
            for point, by_scale in points.items():
                r = by_scale['scale']['1.0']
                lines.append(f"  {method:17} {point:6} reach {r['reach_mm']:6.1f}  lateral {r['lateral_mm']:6.1f}  "
                             f"vertical {r['vertical_mm']:6.1f} mm  {_verdict(r['passed'])}"
                             f"  scale 1.25 {_verdict(by_scale['scale']['1.25']['passed'])}")
    return '\n'.join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('log', type=Path)
    args = parser.parse_args(argv)
    summary = summarize(*read_log(args.log))
    print(format_table(summary))
    stem = args.log.name.removesuffix('.jsonl').removesuffix('.axis_bench')
    target = args.log.with_name(stem+'.axis_summary.json')
    if target == args.log:
        parser.error(f'{args.log} looks like a summary, not a bench file')
    target.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f'\nSaved {target}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
