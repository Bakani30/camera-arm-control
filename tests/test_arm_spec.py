import json
import math
import tempfile
import unittest
from pathlib import Path

from arm_spec import (DEFAULT_SPEC, forward_kinematics, load_spec, soft_limit_problems, soft_range,
                      tcp_radius_m, validate)

# Expected values come from sources outside arm_spec: SO-101 URDF (so101_new_calib.urdf,
# SO-ARM100 commit a758567c39), D25/D32 in docs/research/03-DECISIONS-GLOSSARY.md and the
# maker datasheets recorded in docs/research/hardware-notes/.


class SmallArmSpecV0Tests(unittest.TestCase):
    def setUp(self):
        self.spec = load_spec()

    def test_joint_chain_matches_so101_urdf_order(self):
        self.assertEqual(
            [j.name for j in self.spec.joints],
            ['shoulder_pan', 'shoulder_lift', 'elbow_flex', 'wrist_flex', 'wrist_roll', 'gripper'],
        )

    def test_base_turns_a_full_circle(self):  # D25
        pan = self.spec.joint('shoulder_pan')
        self.assertAlmostEqual(math.degrees(pan.lower), -180, delta=0.01)
        self.assertAlmostEqual(math.degrees(pan.upper), 180, delta=0.01)

    def test_arm_joints_use_sts3215_with_readback(self):  # D28; wrist_flex user choice 2026-10-29
        for name in ('shoulder_pan', 'shoulder_lift', 'elbow_flex', 'wrist_flex'):
            self.assertEqual(self.spec.joint(name).actuator, 'sts3215_12v', name)
            self.assertTrue(self.spec.actuator(name)['readback'], name)

    def test_wrist_flex_uses_the_urdf_range(self):
        # top-down grasps at 20-25 cm need more than the old MG996R +-79.5deg window
        self.assertAlmostEqual(self.spec.joint('wrist_flex').lower, -1.65806, places=5)
        self.assertAlmostEqual(self.spec.joint('wrist_flex').upper, 1.65806, places=5)

    def test_wrist_roll_and_gripper_use_sts3032_with_readback(self):
        # user choice 2026-10-28 (hardware-notes/2026-10-28-arm-4-1-component-review.md): micro bus servo
        for name in ('wrist_roll', 'gripper'):
            self.assertEqual(self.spec.joint(name).actuator, 'sts3032_6v', name)
            self.assertTrue(self.spec.actuator(name)['readback'], name)

    def test_wrist_roll_reaches_a_quarter_turn_for_sideways_grip(self):
        # presentation model v0: the jaws must be able to close across the arm
        roll = self.spec.joint('wrist_roll')
        self.assertGreaterEqual(math.degrees(roll.upper), 90 + 1, 'needs +90deg plus IK margin')
        self.assertLessEqual(math.degrees(roll.lower), 0)

    def test_sts3032_joints_use_the_urdf_range(self):
        # with no MG996R ears in the way, roll and jaw go back to so101_new_calib.urdf limits
        self.assertAlmostEqual(self.spec.joint('wrist_roll').lower, -2.74385, places=5)
        self.assertAlmostEqual(self.spec.joint('wrist_roll').upper, 2.84121, places=5)
        self.assertAlmostEqual(math.degrees(self.spec.joint('gripper').upper), 100, delta=0.01)

    def test_speed_caps_are_half_the_datasheet_no_load_speed(self):  # D32
        # STS3215 C018: 0.222 s/60deg at 12V; STS3032: 0.09 s/60deg at 6V (shop page)
        self.assertAlmostEqual(self.spec.speed_cap_dps('shoulder_lift'), 0.5 * 60 / 0.222, delta=0.01)
        self.assertAlmostEqual(self.spec.speed_cap_dps('wrist_flex'), 0.5 * 60 / 0.222, delta=0.01)
        self.assertAlmostEqual(self.spec.speed_cap_dps('wrist_roll'), 0.5 * 60 / 0.09, delta=0.01)

    def test_every_actuator_declares_an_acceleration_cap(self):  # D32 trapezoid motion
        for name in ('shoulder_pan', 'wrist_roll'):
            self.assertGreater(self.spec.accel_cap_dps2(name), 0, name)

    def test_soft_limits_keep_clear_of_the_shell_collisions(self):
        # cad/shell_v1 checks: upper link hits the column at -100deg; wrist hits the drum from +80deg elbow
        lo, _ = soft_range(self.spec, 'shoulder_lift')
        self.assertGreaterEqual(math.degrees(lo), -90 - 1e-3)
        _, hi = soft_range(self.spec, 'elbow_flex')
        self.assertLessEqual(math.degrees(hi), 70 + 1e-3)

    def test_soft_range_defaults_to_joint_limits(self):
        j = self.spec.joint('wrist_flex')
        self.assertEqual(soft_range(self.spec, 'wrist_flex'), (j.lower, j.upper))

    def test_tcp_radius_cap_allows_the_zero_pose_and_blocks_full_stretch(self):
        cap = self.spec.raw['soft_limits']['tcp_max_radius_from_pan_axis_m']
        self.assertLess(tcp_radius_m(self.spec, {}), cap)                       # ~0.352 m
        stretched = {'shoulder_lift': math.radians(76.7), 'elbow_flex': math.radians(-74.2),
                     'wrist_flex': math.radians(-6.3)}                           # max reach, FK reference note
        self.assertGreater(tcp_radius_m(self.spec, stretched), cap)

    def test_task_poses_pass_the_soft_limits(self):
        deg = math.radians
        for q in ({}, {'shoulder_pan': deg(25), 'shoulder_lift': deg(-15), 'elbow_flex': deg(35), 'wrist_flex': deg(40)},
                  {'shoulder_lift': deg(30), 'elbow_flex': deg(-45), 'wrist_flex': deg(80)}):
            self.assertEqual(soft_limit_problems(self.spec, q), [], q)

    def test_folding_into_the_base_breaks_the_pair_rule(self):
        # shell v1 sweep: shoulder 45 + elbow 60 drives the wrist into the drum
        q = {'shoulder_lift': math.radians(45), 'elbow_flex': math.radians(60)}
        problems = soft_limit_problems(self.spec, q)
        self.assertEqual(len(problems), 1)
        self.assertIn('shoulder_lift + elbow_flex', problems[0])

    def test_tcp_radius_is_measured_from_the_pan_axis(self):
        # base turned 90deg: the TCP swings round the pan axis, so the radius must not change
        r0 = tcp_radius_m(self.spec, {})
        self.assertAlmostEqual(tcp_radius_m(self.spec, {'shoulder_pan': math.radians(90)}), r0, places=6)

    def test_unknown_joint_name_is_a_key_error(self):
        with self.assertRaises(KeyError):
            self.spec.joint('wrist_yaw')


class ForwardKinematicsTests(unittest.TestCase):
    # Worked examples from an independent numpy FK over so101_new_calib.urdf, recorded with its
    # inputs in docs/research/hardware-notes/2026-10-23-so101-fk-reference.md
    def setUp(self):
        self.spec = load_spec()

    def assertPosition(self, actual, expected):
        for a, e in zip(actual, expected):
            self.assertAlmostEqual(a, e, delta=0.001)

    def test_tcp_at_zero_pose(self):
        self.assertPosition(forward_kinematics(self.spec, {}), (0.39136, 0.0, 0.22647))

    def test_tcp_with_base_turned_90_degrees(self):
        q = {'shoulder_pan': math.radians(90)}
        self.assertPosition(forward_kinematics(self.spec, q), (0.03883, -0.35253, 0.22647))

    def test_tcp_in_a_mixed_pose(self):
        q = {'shoulder_pan': math.radians(-45), 'shoulder_lift': math.radians(30),
             'elbow_flex': math.radians(-60), 'wrist_flex': math.radians(40),
             'wrist_roll': math.radians(70)}
        self.assertPosition(forward_kinematics(self.spec, q), (0.31391, 0.26441, 0.24158))

    def test_stretched_pose_reaches_411_mm_from_shoulder_axis(self):
        q = {'shoulder_lift': math.radians(76.7), 'elbow_flex': math.radians(-74.2),
             'wrist_flex': math.radians(-6.3)}
        tx, ty, _ = forward_kinematics(self.spec, q)
        sx, sy, _ = forward_kinematics(self.spec, q, frame='upper_arm_link')
        self.assertAlmostEqual(math.hypot(tx - sx, ty - sy), 0.4108, delta=0.001)


class ValidateTests(unittest.TestCase):
    def broken(self, change):
        data = json.loads(DEFAULT_SPEC.read_text(encoding='utf-8'))
        change(data)
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'spec.json'
            path.write_text(json.dumps(data), encoding='utf-8')
            return validate(load_spec(path))

    @staticmethod
    def joint(data, name):
        return next(j for j in data['joints'] if j['name'] == name)

    def test_shipped_v0_has_no_problems(self):
        self.assertEqual(validate(load_spec()), [])

    def test_reports_joint_range_beyond_actuator_travel(self):
        def widen(d):
            self.joint(d, 'wrist_flex').update(lower=-3.5, upper=3.5)  # 401deg, wider than STS3215's 360deg
        problems = self.broken(widen)
        self.assertEqual(len(problems), 1)
        self.assertIn('wrist_flex', problems[0])

    def test_reports_speed_cap_that_is_not_the_agreed_fraction(self):
        def speed_up(d):
            d['actuators']['sts3032_6v']['speed_cap_dps'] = 300.0  # below no-load, but not 50%
        problems = self.broken(speed_up)
        self.assertEqual(len(problems), 1)
        self.assertIn('sts3032_6v', problems[0])

    def test_reports_base_that_does_not_turn_a_full_circle(self):
        def narrow(d):
            self.joint(d, 'shoulder_pan').update(lower=-1.91986, upper=1.91986)  # URDF +-110deg
        problems = self.broken(narrow)
        self.assertEqual(len(problems), 1)
        self.assertIn('shoulder_pan', problems[0])

    def test_base_rule_holds_even_if_the_file_redefines_the_range(self):  # D25 is not a file setting
        def narrow_both(d):
            self.joint(d, 'shoulder_pan').update(lower=-1.91986, upper=1.91986)
            d['base']['pan_range_deg'] = 220
        problems = self.broken(narrow_both)
        self.assertTrue(any('shoulder_pan' in p for p in problems))

    def test_reports_soft_limit_outside_the_joint_limit(self):
        def loosen(d):
            d['soft_limits']['joints']['shoulder_lift']['lower'] = -2.0  # past the -100deg joint limit
        problems = self.broken(loosen)
        self.assertEqual(len(problems), 1)
        self.assertIn('shoulder_lift', problems[0])

    def test_reports_soft_limit_on_unknown_joint(self):
        def typo(d):
            d['soft_limits']['joints']['elbow'] = {'upper': 1.0}
        problems = self.broken(typo)
        self.assertEqual(len(problems), 1)
        self.assertIn('elbow', problems[0])

    def test_reports_pair_rule_on_unknown_joint(self):
        def typo(d):
            d['soft_limits']['pairs'][0]['joints'][1] = 'elbow'
        problems = self.broken(typo)
        self.assertEqual(len(problems), 1)
        self.assertIn('elbow', problems[0])

    def test_reports_missing_acceleration_cap(self):
        def drop(d):
            del d['actuators']['sts3215_12v']['accel_cap_dps2']
        problems = self.broken(drop)
        self.assertEqual(len(problems), 1)
        self.assertIn('sts3215_12v', problems[0])


if __name__ == '__main__':
    unittest.main()
