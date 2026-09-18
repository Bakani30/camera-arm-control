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

    def test_invalid_input_clears_after_drop_ms(self):
        for gesture, score in [('None', 1), ('Victory', .9), ('Open_Palm', .69), ('Open_Palm', float('nan'))]:
            s = GestureOutput(drop_ms=250)
            s.update('Open_Palm', .9, 0)
            self.assertEqual(s.update('Open_Palm', .9, 250), '01')
            # Short invalid input within drop_ms holds previous '01'
            self.assertEqual(s.update(gesture, score, 260), '01')
            # Invalid input sustained >= drop_ms clears to '00'
            self.assertEqual(s.update(gesture, score, 510), '00')
            # After clearing to '00', reacquisition requires full dwell_ms
            self.assertEqual(s.update('Open_Palm', .9, 520), '00')
            self.assertEqual(s.update('Open_Palm', .9, 770), '01')

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
