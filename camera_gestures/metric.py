"""Hand position in metres: Z = f*L/palm_px, X = (u-cx)*Z/f, Y = (v-cy)*Z/f.

Camera-side values for the bubble mapping, independent of robot coordinates.
"""
import math
from collections import namedtuple

PALM_BASE = (0, 5, 9, 17)
PalmMeasure = namedtuple('PalmMeasure', 'u_px v_px length_px')


def _usable(points, width, height):
    if len(points) != 21 or width <= 0 or height <= 0:
        return False
    return all(len(points[i]) >= 2 and all(math.isfinite(v) for v in points[i])
               and all(0 <= v <= 1 for v in points[i][:2]) for i in PALM_BASE)


def palm_center_px(points, width, height):
    """Mean of the palm base points; steadier than the wrist alone."""
    return (sum(points[i][0] for i in PALM_BASE)*width/len(PALM_BASE),
            sum(points[i][1] for i in PALM_BASE)*height/len(PALM_BASE))


def palm_length_px(points, width, height):
    """Wrist to middle-finger base; z restores what tilt hides from the image.

    MediaPipe scales z like x, so z pixels use the image width.
    """
    wrist, knuckle = points[0], points[9]
    dz = (knuckle[2]-wrist[2])*width if len(wrist) > 2 and len(knuckle) > 2 else 0
    return math.hypot((knuckle[0]-wrist[0])*width, (knuckle[1]-wrist[1])*height, dz)


def palm_measure(points, width, height):
    if not _usable(points, width, height):
        return None
    projected = math.hypot((points[9][0]-points[0][0])*width, (points[9][1]-points[0][1])*height)
    if projected < 5:  # Pointing at the camera: z alone would set the scale.
        return None
    return PalmMeasure(*palm_center_px(points, width, height), palm_length_px(points, width, height))


class MetricHand:
    """Position relative to the re-anchor point.

    Back-projects through the principal point: du*Z/f alone would read a push
    toward the camera as sideways motion whenever the hand is off-centre.
    """

    def __init__(self, focal_px, palm_length_m, principal_px):
        if not (math.isfinite(focal_px) and math.isfinite(palm_length_m) and focal_px > 0 and palm_length_m > 0):
            raise ValueError('focal_px and palm_length_m must be positive and finite')
        self.focal_px = focal_px
        self.palm_length_m = palm_length_m
        self.principal_px = tuple(principal_px)
        self.position_m = (0., 0.)
        self.z_m = None
        self.previous = None
        self.active = False

    def pause(self):
        self.previous = None
        self.active = False

    def reset(self):
        self.pause()
        self.position_m = (0., 0.)
        self.z_m = None

    def update(self, measure):
        if measure is None:
            self.pause()
            return
        self.z_m = self.focal_px*self.palm_length_m/measure.length_px
        metres_per_px = self.z_m/self.focal_px
        x, y = (measure.u_px-self.principal_px[0])*metres_per_px, (measure.v_px-self.principal_px[1])*metres_per_px
        if self.previous is not None:
            self.position_m = (self.position_m[0]+x-self.previous[0], self.position_m[1]+y-self.previous[1])
        self.previous = (x, y)
        self.active = True
