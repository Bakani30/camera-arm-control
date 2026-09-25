import unittest
from camera_gestures.depth import RelativeDepth, palm_scale

class DepthTests(unittest.TestCase):
    def test_scale_ignores_fingertips_and_respects_aspect(self):
        p=[[.5,.5,0] for _ in range(21)]
        p[0]=[.5,.7,0];p[9]=[.5,.5,0];p[5]=[.4,.5,0];p[17]=[.6,.5,0]
        base=palm_scale(p,640,480)
        p[8]=[.1,.1,0];self.assertEqual(base,palm_scale(p,640,480))
        self.assertAlmostEqual(base*2,palm_scale(p,1280,960))
        self.assertIsNone(palm_scale([],640,480))

    def test_directions_and_recalibration(self):
        d=RelativeDepth();d.calibrate(100,0,'Left')
        d.update(125,100,'Left',True)
        self.assertAlmostEqual(d.raw,.2)
        self.assertGreater(d.value,0)
        value=d.value;d.calibrate(125,110,'Left');d.update(125,120,'Left',True)
        self.assertAlmostEqual(d.value,value)
        d=RelativeDepth();d.calibrate(100,0,'Left');d.update(80,100,'Left',True)
        self.assertLess(d.value,0)

    def test_loss_does_not_auto_resume(self):
        d=RelativeDepth();d.calibrate(100,0,'Left');d.update(None,100,'Left',True)
        d.update(120,120,'Left',True);self.assertFalse(d.active)
        self.assertEqual(d.value,0)
        d.calibrate(100,130,'Left');d.update(120,800,'Left',True)
        self.assertFalse(d.active)
