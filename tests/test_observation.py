import unittest
from types import SimpleNamespace as N
from camera_gestures.observation import extract

class ObservationTests(unittest.TestCase):
    def test_missing_hand_cannot_reuse_gesture(self):
        r = N(hand_landmarks=[], gestures=[[N(category_name='Open_Palm', score=.9)]], handedness=[])
        self.assertEqual(extract(r)['gesture'], 'No_hand')
        self.assertEqual(extract(r)['landmarks'], [])

    def test_visible_hand_without_class_is_unknown(self):
        r = N(hand_landmarks=[[N(x=.1,y=.2,z=-.1)]], gestures=[], handedness=[])
        o = extract(r)
        self.assertTrue(o['hand_present'])
        self.assertEqual(o['gesture'], 'Unknown')

    def test_raw_score_and_points_preserved(self):
        r = N(hand_landmarks=[[N(x=.1,y=.2,z=-.1)]],
              gestures=[[N(category_name='Closed_Fist',score=.8)]],
              handedness=[[N(category_name='Left')]])
        self.assertEqual(extract(r),dict(hand_present=True,gesture='Closed_Fist',score=.8,
                                        handedness='Left',landmarks=[[.1,.2,-.1]]))
