"""Candidate readings of hand reach and angle, compared by the axis bench. No camera libraries."""
import math
from collections import namedtuple

from .metric import _usable, palm_center_px

BenchContext = namedtuple('BenchContext', 'width height focal_px palm_m palm_width_m principal_px')

SCALES = (.5, 1., 1.25)
WORKSPACE_M = (.15, .24, .16)     # reach, lateral, vertical of small_arm_v1's mapping box
HAND_STROKE_M = (.30, .62, .31)   # estimated usable hand travel on the same axes


def base_gain():
    """Gain at scale 1, shared by every axis so the arm moves in the hand's direction."""
    return max(w/s for w, s in zip(WORKSPACE_M, HAND_STROKE_M))


def _knuckle_px(points, width, height):
    """Wrist and middle-finger base in pixels, or None where palm_measure would refuse the frame."""
    if not _usable(points, width, height):
        return None
    u0, v0 = points[0][0]*width, points[0][1]*height
    u9, v9 = points[9][0]*width, points[9][1]*height
    if math.hypot(u9-u0, v9-v0) < 5:  # Pointing at the camera: z alone would set the scale.
        return None
    return u0, v0, u9, v9


def _dz_px(points, width, z_gain):
    return (points[9][2]-points[0][2])*width*z_gain


def reach_2d(points, width, height, focal_px, palm_m):
    px = _knuckle_px(points, width, height)
    return px and focal_px*palm_m/math.hypot(px[2]-px[0], px[3]-px[1])


def reach_z(points, width, height, focal_px, palm_m, z_gain=1.):
    """The formula in metric.palm_length_px."""
    px = _knuckle_px(points, width, height)
    return px and focal_px*palm_m/math.hypot(px[2]-px[0], px[3]-px[1], _dz_px(points, width, z_gain))


def reach_z_perspective(points, width, height, focal_px, palm_m, principal_px, z_gain=1.):
    """Also undoes perspective: the knuckle sits nearer or farther than the wrist by dz."""
    px = _knuckle_px(points, width, height)
    if not px:
        return None
    dz, (cx, cy) = _dz_px(points, width, z_gain), principal_px
    g = 1+dz/focal_px
    length = math.hypot((px[2]-cx)/focal_px*g-(px[0]-cx)/focal_px,
                        (px[3]-cy)/focal_px*g-(px[1]-cy)/focal_px, dz/focal_px)
    return palm_m/length if length > 0 else None


def reach_bones(points, width, height, focal_px, palm_m, palm_width_m):
    """Keeps the palm bone tilt shortens least: length under roll, width under pitch."""
    px = _knuckle_px(points, width, height)
    if not px:
        return None
    across = math.hypot((points[5][0]-points[17][0])*width, (points[5][1]-points[17][1])*height)
    return focal_px/max(math.hypot(px[2]-px[0], px[3]-px[1])/palm_m, across/palm_width_m)


REACH_METHODS = {
    '2d': lambda p, c, z_gain=1.: reach_2d(p, c.width, c.height, c.focal_px, c.palm_m),
    'z': lambda p, c, z_gain=1.: reach_z(p, c.width, c.height, c.focal_px, c.palm_m, z_gain),
    'z_perspective': lambda p, c, z_gain=1.: reach_z_perspective(p, c.width, c.height, c.focal_px, c.palm_m,
                                                                 c.principal_px, z_gain),
    'bones': lambda p, c, z_gain=1.: reach_bones(p, c.width, c.height, c.focal_px, c.palm_m, c.palm_width_m),
}


def position_m(points, ctx, z_m, point):
    """Back-project the wrist or palm centre through the principal point, as MetricHand does."""
    if point == 'wrist':
        u, v = points[0][0]*ctx.width, points[0][1]*ctx.height
    elif point == 'center':
        u, v = palm_center_px(points, ctx.width, ctx.height)
    else:
        raise ValueError(f'Unknown point: {point}')
    return (u-ctx.principal_px[0])*z_m/ctx.focal_px, (v-ctx.principal_px[1])*z_m/ctx.focal_px


def hand_angles(points, ctx):
    """(pitch, roll) in degrees; positive pitch tips the fingers toward the camera."""
    if not _usable(points, ctx.width, ctx.height) or any(len(points[i]) < 3 for i in (0, 5, 9, 17)):
        return None
    def bone(a, b):
        return ((points[b][0]-points[a][0])*ctx.width, (points[b][1]-points[a][1])*ctx.height,
                (points[b][2]-points[a][2])*ctx.width)
    along, across = bone(0, 9), bone(5, 17)
    # The knuckle row is not square to the palm; without this, pure pitch reads as roll.
    squared = sum(v*v for v in along)
    if squared > 0:
        share = sum(a*b for a, b in zip(across, along))/squared
        across = tuple(a-share*b for a, b in zip(across, along))
    return (math.degrees(math.atan2(-along[2], math.hypot(along[0], along[1]))),
            math.degrees(math.atan2(across[2], math.hypot(across[0], across[1]))))
