import unittest
from camera_gestures.target import ScreenTarget
from camera_gestures.display import hand_box

class TargetTests(unittest.TestCase):
    def test_resume_no_jump_and_loss_requires_calibration(self):
        t=ScreenTarget()
        t.calibrate((.2,.2),0,'Left')
        t.update((.4,.3),100,'Left')
        self.assertGreater(t.position[0],.5)
        saved=t.position
        t.update(None,120,'Left')
        t.update((.9,.9),140,'Left')
        self.assertEqual(t.position,saved)
        t.calibrate((.9,.9),150,'Left')
        t.update((.9,.9),160,'Left')
        self.assertEqual(t.position,saved)

    def test_gap_hand_change_and_bounds(self):
        t=ScreenTarget();t.calibrate((.5,.5),0,'Left')
        t.update((3,-3),100,'Left')
        self.assertEqual(t.raw,(1.,0.))
        t.update((.5,.5),110,'Right')
        self.assertFalse(t.active)
        t.calibrate((.5,.5),120,'Right')
        t.update((.5,.5),1000,'Right')
        self.assertFalse(t.active)

    def test_box_clipped_and_missing(self):
        self.assertIsNone(hand_box([],640,480))
        self.assertEqual(hand_box([[-1,-1],[2,2]],640,480),(0,0,639,479))
