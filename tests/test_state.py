import unittest
from camera_gestures.state import GestureOutput


class GestureTests(unittest.TestCase):
    def test_palm_and_fist_require_dwell(self):
        s = GestureOutput()
        self.assertEqual(s.update('Open_Palm', .9, 0), '00')
        self.assertEqual(s.update('Open_Palm', .9, 249), '00')
        self.assertEqual(s.update('Open_Palm', .9, 250), '01')
        # During transition to fist, hold previous output '01' until fist is sustained for dwell_ms
        self.assertEqual(s.update('Closed_Fist', .9, 300), '01')
        self.assertEqual(s.update('Closed_Fist', .9, 549), '01')
        self.assertEqual(s.update('Closed_Fist', .9, 550), '10')

    def test_intermediate_transition_holds_previous_value(self):
        s = GestureOutput()
        s.update('Open_Palm', .9, 0)
        self.assertEqual(s.update('Open_Palm', .9, 250), '01')
        # Intermediate/noisy frames during hand movement hold previous '01'
        self.assertEqual(s.update('None', 0.0, 300), '01')
        self.assertEqual(s.update('Victory', 0.9, 350), '01')
        self.assertEqual(s.update('Closed_Fist', 0.9, 400), '01')
        self.assertEqual(s.update('Closed_Fist', 0.9, 649), '01')
        self.assertEqual(s.update('Closed_Fist', 0.9, 650), '10')

    def test_hand_present_never_drops_to_00(self):
        s = GestureOutput(drop_ms=250)
        s.update('Open_Palm', .9, 0)
        self.assertEqual(s.update('Open_Palm', .9, 250), '01')
        # Stream frames with hand present at 100ms intervals (well below max_gap_ms)
        # Even after long duration (> drop_ms), if hand is present, it must NEVER drop to '00'
        for t in range(300, 3000, 100):
            gesture = 'Victory' if t < 1500 else 'None'
            self.assertEqual(s.update(gesture, 0.4, t, has_hand=True), '01')

    def test_no_hand_clears_after_drop_ms(self):
        s = GestureOutput(drop_ms=250)
        s.update('Open_Palm', .9, 0)
        self.assertEqual(s.update('Open_Palm', .9, 250), '01')
        # Hand lost: within drop_ms holds previous '01'
        self.assertEqual(s.update('No_hand', 0.0, 300, has_hand=False), '01')
        self.assertEqual(s.update('No_hand', 0.0, 549, has_hand=False), '01')
        # Hand lost sustained >= drop_ms clears to '00'
        self.assertEqual(s.update('No_hand', 0.0, 550, has_hand=False), '00')
        # After clearing to '00', reacquisition requires full dwell_ms
        self.assertEqual(s.update('Open_Palm', .9, 600, has_hand=True), '00')
        self.assertEqual(s.update('Open_Palm', .9, 850, has_hand=True), '01')

    def test_long_gap_resets(self):
        s = GestureOutput()
        s.update('Closed_Fist', .9, 0)
        self.assertEqual(s.update('Closed_Fist', .9, 250), '10')
        self.assertEqual(s.update('Closed_Fist', .9, 1000), '00')

    def test_alternating_never_emits(self):
        s = GestureOutput()
        for i in range(20):
            self.assertEqual(s.update(['Open_Palm', 'Closed_Fist'][i % 2], .9, i*50), '00')

    def test_timing_validation(self):
        with self.assertRaises(ValueError):
            GestureOutput(drop_ms=-1)


if __name__ == '__main__':
    unittest.main()
