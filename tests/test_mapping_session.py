import unittest

from arm_contracts.messages import to_line
from arm_contracts.mock_arm import MockArm
from camera_gestures.control import HandControl
from camera_gestures.mapping import MappingConfig
from camera_gestures.mapping_session import MappingSession, targets_from_records
from camera_gestures.metric import MetricHand, PalmMeasure
from camera_gestures.pipeline import handle_key

WRIST, SCALE = (.5, .5), 100.
PALM = 198.  # 0.5 m away with f=900 and L=0.11


class Rig:
    def __init__(self, **session):
        self.metric = MetricHand(900., .11, (640., 360.))
        self.control = HandControl('Right', metric=self.metric)
        self.arm = MockArm()
        self.session = MappingSession(self.arm, source='script', **session)
        self.now = 0
        self.records = []

    def start(self):
        self.control.calibrate(WRIST, SCALE, self.now)

    def frame(self, u=640., code='00', palm=PALM, usable=True, hand=True):
        self.now += 33
        measure = PalmMeasure(u, 360., palm) if usable else None
        self.control.update(WRIST if hand else None, SCALE if hand else None, self.now, measure if hand else None)
        message = self.session.step(self.control, self.metric, code, self.now)
        self.records.append(dict(receipt_ms=self.now, output=code, metric_position_m=self.metric.position_m,
                                 metric_z_m=self.metric.z_m, metric_active=self.metric.active,
                                 **self.session.log_fields()))
        return message


class SessionTests(unittest.TestCase):
    def test_messages_pass_the_receiver(self):
        rig = Rig()
        rig.start()
        for i in range(5):
            message = rig.frame(u=640.+i)
            self.assertIsNone(rig.arm.problem)
            self.assertIsNone(message.orientation_wxyz)
            self.assertEqual((message.frame, message.robot_id, message.source), ('robot_base', 'small_arm', 'script'))
            self.assertEqual(message.seq, i+1)
            self.assertEqual(message.t_ms, rig.now)

    def test_palm_unusable_holds_while_control_is_active(self):
        rig = Rig()
        rig.start()
        rig.frame()
        message = rig.frame(usable=False)
        self.assertEqual(rig.control.status, 'ACTIVE')
        self.assertEqual((message.mode, message.enabled), ('hold', True))

    def test_hand_switch_disables_at_once(self):
        rig = Rig()
        rig.start()
        rig.frame()
        rig.control.select('Left')
        message = rig.frame()
        self.assertEqual((message.mode, message.enabled), ('hold', False))

    def test_loss_turns_to_hold_in_the_same_frame(self):
        rig = Rig()
        rig.start()
        rig.frame()
        self.assertEqual(rig.frame(hand=False).mode, 'hold')

    def test_mock_follows_and_freezes(self):
        rig = Rig(config=MappingConfig(tau_lateral_ms=0, tau_depth_ms=0))
        rig.start()
        rig.frame()
        rig.frame(u=660.)
        moved = rig.arm.position
        self.assertLess(moved[1], 0.)
        rig.frame(hand=False)
        self.assertEqual(rig.arm.status, 'hold')
        self.assertEqual(rig.arm.position, moved)

    def test_position_is_rounded_like_scripted_targets(self):
        rig = Rig()
        rig.start()
        rig.frame()
        for v in rig.frame(u=641.234567).position_m:
            self.assertEqual(v, round(v, 6))

    def test_reset_key_then_tracking_slides_back(self):
        config = MappingConfig(tau_lateral_ms=0, tau_depth_ms=0)
        rig = Rig(config=config)
        rig.start()
        rig.frame()
        for i in range(1, 8):
            away = rig.frame(u=640.+i*20).position_m
        rig.session.reset()
        handle_key('r', rig.control, WRIST, SCALE, rig.now)
        last = away
        for _ in range(5):
            now = rig.frame(u=800.).position_m
            step = sum((a-b)**2 for a, b in zip(now, last))**.5
            self.assertLessEqual(step, .25*.033+2e-6)
            last = now
        self.assertGreater(last[1], away[1])

    def test_records_recompute_to_the_same_targets(self):
        rig = Rig()
        rig.start()
        sent = [rig.frame(), rig.frame(u=650., code='10'), rig.frame(u=660., code='10'), rig.frame(hand=False)]
        rig.session.reset()
        handle_key('r', rig.control, WRIST, SCALE, rig.now)
        sent += [rig.frame(u=700.), rig.frame(u=700., code='01'), rig.frame(u=700., usable=False)]
        rig.control.pause()
        sent += [rig.frame(u=700.)]
        again = targets_from_records(rig.records)
        self.assertEqual(len(again), len(sent))
        for want, got in zip(sent, again):
            self.assertEqual((got.position_m, got.mode, got.enabled, got.grip, got.seq, got.t_ms),
                             (want.position_m, want.mode, want.enabled, want.grip, want.seq, want.t_ms))
            self.assertEqual(got.source, 'script')

    def test_log_fields_record_the_reset_once(self):
        rig = Rig()
        rig.start()
        rig.frame()
        rig.session.reset()
        handle_key('r', rig.control, WRIST, SCALE, rig.now)
        rig.frame()
        rig.frame()
        self.assertEqual([r['mapping_reset'] for r in rig.records], [False, True, False])

    def test_message_lines_are_valid_contract_json(self):
        rig = Rig()
        rig.start()
        self.assertIn('"contract":"ee_target/0.1"', to_line(rig.frame()))


if __name__ == '__main__':
    unittest.main()
