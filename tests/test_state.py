import unittest
from camera_gestures.state import GestureOutput


class GestureTests(unittest.TestCase):
    def test_palm_and_fist_require_dwell(self):
        s = GestureOutput()
        self.assertEqual(s.update('Open_Palm', .9, 0), '00')
        self.assertEqual(s.update('Open_Palm', .9, 249), '00')
        self.assertEqual(s.update('Open_Palm', .9, 250), '01')
        self.assertEqual(s.update('Closed_Fist', .9, 300), '00')
        self.assertEqual(s.update('Closed_Fist', .9, 550), '10')

    def test_invalid_input_clears_and_requires_reacquisition(self):
        for gesture, score in [('None', 1), ('Victory', .9), ('Open_Palm', .69), ('Open_Palm', float('nan'))]:
            s = GestureOutput()
            s.update('Open_Palm', .9, 0)
            self.assertEqual(s.update('Open_Palm', .9, 250), '01')
            self.assertEqual(s.update(gesture, score, 260), '00')
            self.assertEqual(s.update('Open_Palm', .9, 270), '00')
            self.assertEqual(s.update('Open_Palm', .9, 520), '01')

    def test_long_gap_resets(self):
        s = GestureOutput()
        s.update('Closed_Fist', .9, 0)
        self.assertEqual(s.update('Closed_Fist', .9, 250), '10')
        self.assertEqual(s.update('Closed_Fist', .9, 1000), '00')

    def test_alternating_never_emits(self):
        s = GestureOutput()
        for i in range(20):
            self.assertEqual(s.update(['Open_Palm', 'Closed_Fist'][i % 2], .9, i*50), '00')


if __name__ == '__main__':
    unittest.main()
