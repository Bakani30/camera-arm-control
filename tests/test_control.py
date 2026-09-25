import unittest
from types import SimpleNamespace as N
from camera_gestures.control import HandControl
from camera_gestures.observation import extract_selected

class ControlTests(unittest.TestCase):
    def test_return_at_new_position_and_scale_preserves_xyz(self):
        c=HandControl();c.calibrate((.4,.4),100,0)
        c.update((.5,.5),120,100)
        saved=(c.target.position,c.depth.value)
        c.update(None,None,130)
        c.update((.1,.9),60,200)
        self.assertEqual(saved,(c.target.position,c.depth.value))
        self.assertTrue(c.target.active and c.depth.active)
        c.update((.2,.9),60,230)
        self.assertGreater(c.target.position[0],saved[0][0])

    def test_manual_pause_reset_and_switch(self):
        c=HandControl();c.calibrate((.4,.4),100,0);c.pause()
        c.update((.8,.8),140,100);self.assertFalse(c.target.active)
        c.reset();c.update(None,None,150)
        self.assertEqual((c.target.position,c.depth.value),((.5,.5),0))
        c.update((.8,.8),140,200);self.assertTrue(c.target.active)
        c.select('Left');c.update((.1,.1),100,220)
        self.assertFalse(c.armed)

    def test_only_selected_side_and_ambiguity(self):
        left=[N(category_name='Left',score=.99)]
        right=[N(category_name='Right',score=.99)]
        points=[[N(x=.2,y=.3,z=0)],[N(x=.7,y=.8,z=0)]]
        r=N(handedness=[left,right],hand_landmarks=points,gestures=[[],[]])
        self.assertEqual(extract_selected(r,'Right')['landmarks'][0][0],.7)
        r.handedness=[left,left]
        self.assertFalse(extract_selected(r,'Right')['hand_present'])
        self.assertFalse(extract_selected(r,'Left')['hand_present'])
