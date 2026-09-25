import unittest
from camera_gestures.keypoint import normalize

class NormalizeTests(unittest.TestCase):
    def test_translation_and_scale(self):
        points=[[.1+i*.01,.1+i*.02] for i in range(21)]
        shifted=[[p[0]*2+.1,p[1]*2] for p in points]
        a,b=normalize(points,1000,1000),normalize(shifted,1000,1000)
        for x,y in zip(a,b): self.assertAlmostEqual(x,y,delta=.005)

    def test_degenerate_and_missing(self):
        self.assertIsNone(normalize([],640,480))
        self.assertIsNone(normalize([[.5,.5]]*21,640,480))
        self.assertIsNone(normalize([[float('nan'),0]]*21,640,480))
