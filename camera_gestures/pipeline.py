"""Post-MediaPipe per-frame logic, shared by the live app and log replay."""
from .depth import palm_scale
from .metric import palm_measure

STALE_MS = 500


def step(state, control, observation, stale, now, width, height):
    """Feed one observation through the gesture filter and hand control."""
    code = state.update('Stale_result' if stale else observation['gesture'],
                        0 if stale else observation['score'], now,
                        has_hand=observation['hand_present'] and not stale)
    wrist = tuple(observation['landmarks'][0][:2]) if observation['hand_present'] and not stale else None
    scale = palm_scale(observation['landmarks'], width, height) if wrist is not None else None
    palm = palm_measure(observation['landmarks'], width, height) if wrist is not None and control.metric is not None else None
    control.update(wrist, scale, now, palm)
    return code, wrist, scale


def handle_key(key, control, wrist, scale, now):
    """Apply a control key after a frame; True means restart the gesture filter."""
    if key == 'c':
        control.calibrate(wrist, scale, now)
    elif key == 'r':
        control.reset()
        control.update(wrist, scale, now)
    elif key == ' ':
        control.pause()
    elif key in ('l', 'h'):
        control.select('Left' if key == 'l' else 'Right')
        return True
    return False
