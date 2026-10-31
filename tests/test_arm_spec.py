import json
import math
import tempfile
import unittest
from pathlib import Path

import arm_spec
from arm_spec import (DEFAULT_SPEC, V0_SPEC, crank_rad, fingertip_mm, forward_kinematics, gate_problems, load_spec,
                      opening_for_crank, soft_limit_problems, soft_range, tcp_radius_m, tcp_xyz_for_opening, validate)

# Expected values come from sources outside arm_spec: SO-101 URDF (so101_new_calib.urdf,
# SO-ARM100 commit a758567c39), D25/D32 in docs/research/03-DECISIONS-GLOSSARY.md and the
# maker datasheets recorded in docs/research/hardware-notes/.


class SmallArmSpecV0Tests(unittest.TestCase):
    def setUp(self):
        self.spec = load_spec(V0_SPEC)

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
        self.spec = load_spec(V0_SPEC)

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


class SmallArmSpecV1Tests(unittest.TestCase):
    # Expected values come from cad/shell_v1 (wrist_gripper_v1 at each opening, part volumes) and
    # docs/research/hardware-notes/2026-10-31-motion-test-results.md.
    def setUp(self):
        self.spec = load_spec()

    def test_default_is_v1_and_consistent(self):
        self.assertEqual(self.spec.raw['spec'], 'small_arm/1.0')
        self.assertEqual(validate(self.spec), [])

    def test_arm_joint_frames_did_not_change(self):
        v0 = load_spec(V0_SPEC)
        for name in ('shoulder_pan', 'shoulder_lift', 'elbow_flex', 'wrist_flex', 'wrist_roll'):
            a, b = self.spec.joint(name), v0.joint(name)
            self.assertEqual((a.origin_xyz, a.origin_rpy, a.axis, a.lower, a.upper), (b.origin_xyz, b.origin_rpy, b.axis, b.lower, b.upper), name)

    def test_tcp_is_the_pad_center_on_the_roll_axis(self):
        self.assertEqual(self.spec.tcp['origin_xyz'][:2], [0.0, 0.0])
        x, y, z = forward_kinematics(self.spec, {})
        self.assertAlmostEqual(x, 0.29323 + 0.084, places=4)
        self.assertAlmostEqual(y, -0.00018, places=4)
        self.assertAlmostEqual(z, 0.23437, places=4)

    def test_spec_tcp_is_the_table_value_at_the_holding_width(self):
        self.assertAlmostEqual(tcp_xyz_for_opening(self.spec, 40)[2], self.spec.tcp['origin_xyz'][2], places=6)

    def test_fingertip_follows_the_four_bar(self):
        self.assertAlmostEqual(fingertip_mm(self.spec, 57), 86.7)
        self.assertAlmostEqual(fingertip_mm(self.spec, 40), 97.0)
        self.assertAlmostEqual(fingertip_mm(self.spec, 0), 106.3)
        self.assertAlmostEqual(fingertip_mm(self.spec, 45), (97.0 + 91.8) / 2)

    def test_pad_center_moves_with_the_opening(self):
        self.assertEqual(tcp_xyz_for_opening(self.spec, 57)[:2], (0.0, 0.0))
        self.assertAlmostEqual(tcp_xyz_for_opening(self.spec, 57)[2], -0.0737, places=6)
        self.assertAlmostEqual(tcp_xyz_for_opening(self.spec, 0)[2], -0.0933, places=6)

    def test_crank_angle_follows_the_opening(self):
        self.assertAlmostEqual(math.degrees(crank_rad(self.spec, 0)), 8.92, places=2)
        self.assertAlmostEqual(math.degrees(crank_rad(self.spec, 40)), 40.92, places=2)
        self.assertAlmostEqual(math.degrees(crank_rad(self.spec, 57)), 60.17, places=2)

    def test_opening_outside_the_gripper_range_is_an_error(self):
        for bad in (-1, 58):
            with self.assertRaises(ValueError):
                fingertip_mm(self.spec, bad)
            with self.assertRaises(ValueError):
                crank_rad(self.spec, bad)

    def test_gripper_joint_is_the_shell_crank(self):
        j = self.spec.joint('gripper')
        self.assertAlmostEqual(math.degrees(j.lower), 8.92, places=2)
        self.assertAlmostEqual(math.degrees(j.upper), 60.17, places=2)
        self.assertEqual(j.child, 'finger_crank_link')
        got = forward_kinematics(self.spec, {}, 'finger_crank_link')
        for a, b in zip(got, (0.30303, -0.00018, 0.24137)):
            self.assertAlmostEqual(a, b, places=4)

    def test_masses_come_from_the_shell(self):
        masses = self.spec.raw['link_mass_kg']
        self.assertNotIn('moving_jaw_so101_v1_link', masses)
        self.assertAlmostEqual(sum(masses.values()), 0.8933, delta=0.001)
        self.assertAlmostEqual(masses['gripper_link'], 0.0705, delta=0.001)

    def test_top_down_near_the_pan_axis_breaks_the_soft_limits(self):
        # motion test: open fingers hit the column at r <= 110 mm with the tool straight down
        q = {'shoulder_lift': math.radians(-40), 'elbow_flex': math.radians(40), 'wrist_flex': math.radians(90)}
        self.assertLess(tcp_radius_m(self.spec, q), 0.125)
        self.assertTrue(any('pan axis' in p for p in soft_limit_problems(self.spec, q)))

    def test_task_poses_pass_the_soft_limits(self):
        deg = math.radians
        for q in ({}, {'shoulder_pan': deg(25), 'shoulder_lift': deg(-15), 'elbow_flex': deg(35), 'wrist_flex': deg(40)},
                  {'shoulder_lift': deg(30), 'elbow_flex': deg(-45), 'wrist_flex': deg(80)}):
            self.assertEqual(soft_limit_problems(self.spec, q), [], q)

    def assertBroken(self, word, opening=None, **deg):
        q = {k: math.radians(v) for k, v in deg.items()}
        problems = soft_limit_problems(self.spec, q, opening)
        self.assertTrue(any(word in p for p in problems), (deg, problems))

    def test_tool_below_the_table_breaks_the_soft_limits(self):  # poses that overlap the table in the sweep
        self.assertBroken('table', 57, shoulder_lift=45, elbow_flex=30, wrist_flex=-30)
        self.assertBroken('table', 57, shoulder_lift=0, elbow_flex=45, wrist_flex=45)

    def test_forearm_on_the_table_counts_while_the_tcp_is_above_it(self):
        q = {'shoulder_lift': math.radians(60), 'elbow_flex': math.radians(15), 'wrist_flex': math.radians(-90)}
        self.assertGreater(forward_kinematics(self.spec, q)[2], 0.03)
        self.assertBroken('table', 57, shoulder_lift=60, elbow_flex=15, wrist_flex=-90)

    def test_finger_roots_count_when_the_tool_tilts_up(self):  # the tip is the high end of the finger here
        self.assertBroken('finger roots', 57, shoulder_lift=60, elbow_flex=0, wrist_flex=-75)

    def test_tool_over_a_base_leg_breaks_the_soft_limits(self):
        self.assertBroken('leg', 57, shoulder_pan=36, shoulder_lift=-15, elbow_flex=60, wrist_flex=15)

    def test_folded_near_the_column_breaks_the_soft_limits(self):
        self.assertBroken('pan axis', 57, shoulder_lift=-75, elbow_flex=60, wrist_flex=75)

    def test_top_down_grasp_at_table_height_is_allowed(self):
        # pad centre 20 mm over the table at 20 cm, from the motion test scenario E
        for opening, q in ((57, {'shoulder_lift': 0.2177, 'elbow_flex': 0.3289, 'wrist_flex': 1.0243}),):
            self.assertEqual(soft_limit_problems(self.spec, q, opening), [])

    def test_unknown_opening_checks_the_worse_end(self):
        # fingers reach furthest when closed, so a pose that only clears the table open must fail without an opening
        q = {'shoulder_lift': 0.2177, 'elbow_flex': 0.3289, 'wrist_flex': 1.0243}
        self.assertEqual(soft_limit_problems(self.spec, q, 57), [])
        self.assertTrue(any('table' in p for p in soft_limit_problems(self.spec, q)))

    def test_unknown_or_broken_values_are_problems_not_crashes(self):
        self.assertTrue(soft_limit_problems(self.spec, {'shoulder_lfit': 1.0}))
        for bad in (math.inf, math.nan, 'x', None):
            self.assertTrue(soft_limit_problems(self.spec, {'elbow_flex': bad}), bad)
        self.assertTrue(soft_limit_problems(self.spec, {}, 999))
        self.assertTrue(soft_limit_problems(self.spec, {}, math.nan))

    def test_no_opening_checks_every_row_of_the_table(self):
        seen = []
        real = arm_spec.fingertip_mm
        try:
            arm_spec.fingertip_mm = lambda spec, opening: seen.append(opening) or real(spec, opening)
            soft_limit_problems(self.spec, {})
        finally:
            arm_spec.fingertip_mm = real
        self.assertEqual(sorted(seen), [r['opening_mm'] for r in self.spec.raw['gripper_kinematics']['by_opening']])

    def test_gate_needs_every_arm_joint(self):
        pose = {'shoulder_pan': 0.0, 'shoulder_lift': 0.0, 'elbow_flex': 0.0, 'wrist_flex': 0.0, 'wrist_roll': 0.0}
        self.assertEqual(gate_problems(self.spec, pose, 40), [])
        short = {k: v for k, v in pose.items() if k != 'wrist_flex'}
        self.assertTrue(any('wrist_flex' in p for p in gate_problems(self.spec, short, 40)))

    def test_gate_stops_a_gripper_angle_that_disagrees_with_the_opening(self):
        pose = {'shoulder_pan': 0.0, 'shoulder_lift': 0.0, 'elbow_flex': 0.0, 'wrist_flex': 0.0, 'wrist_roll': 0.0}
        self.assertEqual(gate_problems(self.spec, {**pose, 'gripper': crank_rad(self.spec, 40)}, 40), [])
        self.assertTrue(any('gripper' in p for p in gate_problems(self.spec, {**pose, 'gripper': crank_rad(self.spec, 10)}, 40)))

    def test_gate_reads_the_opening_from_the_gripper_angle(self):
        pose = {'shoulder_pan': 0.0, 'shoulder_lift': 0.2177, 'elbow_flex': 0.3289, 'wrist_flex': 1.0243, 'wrist_roll': 0.0}
        self.assertEqual(gate_problems(self.spec, {**pose, 'gripper': crank_rad(self.spec, 57)}), [])

    def test_opening_from_crank_undoes_crank_from_opening(self):
        for opening in (0, 7, 25, 40, 57):
            self.assertAlmostEqual(opening_for_crank(self.spec, crank_rad(self.spec, opening)), opening, places=6)
        with self.assertRaises(ValueError):
            opening_for_crank(self.spec, 2.0)

    def changed(self, edit):
        data = json.loads(Path(DEFAULT_SPEC).read_text(encoding='utf-8'))
        edit(data)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'spec.json'
            path.write_text(json.dumps(data), encoding='utf-8')
            return validate(load_spec(path))

    def test_validate_rejects_a_floor_frame_the_spec_does_not_have(self):
        def edit(d):
            d['soft_limits']['floor']['frames'][0]['frame'] = 'no_such_link'
        self.assertTrue(any('floor' in p for p in self.changed(edit)))

    def test_validate_rejects_a_min_radius_over_the_max(self):
        def edit(d):
            d['soft_limits']['tcp_min_radius_from_pan_axis_m'] = 0.5
        self.assertTrue(any('radius' in p for p in self.changed(edit)))

    def test_validate_rejects_a_tcp_off_the_table(self):
        def edit(d):
            d['tcp']['origin_xyz'][2] = -0.098
        self.assertTrue(any('tcp' in p for p in self.changed(edit)))

    def test_validate_rejects_an_unsorted_gripper_table(self):
        def edit(d):
            d['gripper_kinematics']['by_opening'].reverse()
        self.assertTrue(any('by_opening' in p for p in self.changed(edit)))

    def test_validate_rejects_a_crank_outside_the_joint(self):
        def edit(d):
            d['gripper_kinematics']['by_opening'][-1]['crank_deg'] = 90.0
        self.assertTrue(any('crank' in p for p in self.changed(edit)))


if __name__ == '__main__':
    unittest.main()
