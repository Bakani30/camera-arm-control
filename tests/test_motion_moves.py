import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'cad' / 'shell_v1'))

from arm_spec import load_spec, soft_limit_problems  # noqa: E402
from motion_moves import (HOLD_MM, PAD_CENTER_BEHIND_TIP_MM, PAN_X, READY, SHELL_TCP_M, SPEC_V0_TCP_M, SURVEY_LAYOUT, Layout, Move, Pose,  # noqa: E402
                          Unreachable, compensated_move_list, fingertip_mm, joint_time_s, move_list, pad_center_tcp,
                          plan_move, polar, solve_ik, tool_direction, tcp_position)


class ForwardTests(unittest.TestCase):
    def setUp(self):
        self.spec = load_spec()

    def test_tool_points_forward_at_zero(self):
        for got, want in zip(tool_direction(self.spec, {}), (1, 0, 0)):
            self.assertAlmostEqual(got, want, places=4)

    def test_pitch_joints_summing_to_90_point_the_tool_down(self):
        q = {'shoulder_lift': 0.5, 'elbow_flex': -0.3, 'wrist_flex': math.pi / 2 - 0.2}
        for got, want in zip(tool_direction(self.spec, q), (0, 0, -1)):
            self.assertAlmostEqual(got, want, places=4)

    def test_shell_tcp_sits_on_the_roll_axis_8_mm_from_the_spec_tcp(self):
        spec_tcp = tcp_position(self.spec, {}, SPEC_V0_TCP_M)
        shell_tcp = tcp_position(self.spec, {}, SHELL_TCP_M)
        self.assertAlmostEqual(math.dist(spec_tcp, shell_tcp) * 1000, 7.9, delta=0.1)


class IkTests(unittest.TestCase):
    def setUp(self):
        self.spec = load_spec()

    def assertSolves(self, xyz, tcp=None, seed=None):
        q = solve_ik(self.spec, Pose(xyz), tcp, seed)
        self.assertLess(math.dist(tcp_position(self.spec, q, tcp), xyz) * 1000, 0.1)
        self.assertAlmostEqual(tool_direction(self.spec, q)[2], -1, places=4)
        return q

    def test_reaches_a_top_down_point_in_front(self):
        self.assertSolves((0.29, 0.0, 0.05))

    def test_reaches_it_for_the_other_tcp_too(self):
        self.assertSolves((0.29, 0.0, 0.05), SHELL_TCP_M)

    def test_positive_y_means_negative_pan(self):  # the pan axis points down in the URDF
        q = self.assertSolves((0.0388, 0.25, 0.05))
        self.assertAlmostEqual(q['shoulder_pan'], -math.pi / 2, delta=0.05)

    def test_elbow_stays_on_the_upper_branch(self):
        q = self.assertSolves((0.29, 0.0, 0.05))
        self.assertLess(q['elbow_flex'], 0.3)

    def test_roll_is_passed_through(self):
        q = solve_ik(self.spec, Pose((0.29, 0.0, 0.05), roll_deg=40))
        self.assertAlmostEqual(q['wrist_roll'], math.radians(40))

    def test_finds_what_a_grid_search_finds(self):  # a solver miss must not read as an arm limit
        for r, z in ((0.15, 0.10), (0.20, 0.10), (0.25, 0.05), (0.20, 0.02), (0.25, 0.02)):
            self.assertSolves((PAN_X + r, 0.0, z))

    def test_out_of_reach_raises(self):
        with self.assertRaises(Unreachable):
            solve_ik(self.spec, Pose((0.9, 0.0, 0.05)))


class TimingTests(unittest.TestCase):
    def test_long_move_reaches_the_speed_cap(self):
        self.assertAlmostEqual(joint_time_s(90, 135, 450), 90 / 135 + 135 / 450, places=6)

    def test_short_move_never_reaches_it(self):
        self.assertAlmostEqual(joint_time_s(10, 135, 450), 2 * math.sqrt(10 / 450), places=6)

    def test_no_travel_takes_no_time(self):
        self.assertEqual(joint_time_s(0, 135, 450), 0)


class PlanTests(unittest.TestCase):
    def setUp(self):
        self.spec = load_spec()
        self.moves = move_list()

    def test_moves_chain_from_ready_back_to_ready(self):
        names = [m.name for m in self.moves]
        self.assertEqual(len(names), len(set(names)))
        self.assertEqual(self.moves[0].start, READY)
        task = [m for m in self.moves if m.task]
        for a, b in zip(task, task[1:]):
            self.assertEqual(a.goal, b.start, b.name)
        self.assertEqual(task[-1].goal, READY)

    def test_every_task_move_has_a_camera_style_straight_path(self):
        for move in self.moves:
            plan = plan_move(self.spec, move, samples=9)
            self.assertEqual(len(plan.samples), 9, move.name)

    def test_first_and_last_samples_hit_the_poses(self):
        move = self.moves[1]  # descends to the grasp height, which is reachable
        plan = plan_move(self.spec, move, samples=5)
        self.assertLess(math.dist(tcp_position(self.spec, plan.samples[-1].q), move.goal.xyz) * 1000, 0.1)
        self.assertEqual(plan.samples[-1].opening_mm, move.goal.opening_mm)

    def test_a_reachable_layout_gives_no_unreachable_samples(self):
        layout = Layout(polar(0.20, 0), polar(0.20, 72), polar(0.16, -45), 0.07)
        for move in move_list(layout):
            if move.name != '15_reach_far_table':
                plan = plan_move(self.spec, move, samples=5)
                self.assertFalse(any(s.unreachable for s in plan.samples), move.name)

    def test_time_comes_from_the_slowest_joint(self):
        plan = plan_move(self.spec, self.moves[1], samples=5)
        self.assertGreater(plan.time_s, 0)
        self.assertIn(plan.slowest_joint, ('shoulder_pan', 'shoulder_lift', 'elbow_flex', 'wrist_flex', 'wrist_roll'))

    def test_joint_paths_have_no_jumps(self):  # IK must stay on one branch along a move
        for move in self.moves:
            plan = plan_move(self.spec, move, samples=17)
            for a, b in zip(plan.samples, plan.samples[1:]):
                if a.unreachable or b.unreachable:
                    continue
                for name in a.q:
                    self.assertLess(abs(a.q[name] - b.q[name]), math.radians(45), f'{move.name} {name}')

    def test_soft_limit_breaks_are_reported_not_hidden(self):
        plan = plan_move(self.spec, self.moves[1], samples=5)
        for sample in plan.samples:
            self.assertEqual(sample.limit_problems, soft_limit_problems(self.spec, sample.q, sample.opening_mm))

    def test_the_tcp_choice_changes_the_joint_angles(self):
        move = self.moves[1]
        spec_plan = plan_move(self.spec, move, samples=3)
        shell_plan = plan_move(self.spec, move, samples=3, tcp=SHELL_TCP_M)
        self.assertNotEqual(spec_plan.samples[-1].q, shell_plan.samples[-1].q)


class OpeningTests(unittest.TestCase):  # values measured from wrist_gripper_v1 at each opening
    def test_fingertip_follows_the_four_bar(self):
        self.assertAlmostEqual(fingertip_mm(57), 86.7)
        self.assertAlmostEqual(fingertip_mm(40), 97.0)
        self.assertAlmostEqual(fingertip_mm(0), 106.3)

    def test_fingertip_interpolates_between_measured_openings(self):
        self.assertAlmostEqual(fingertip_mm(45), (97.0 + 91.8) / 2)

    def test_pad_center_tcp_sits_on_the_roll_axis_behind_the_tip(self):
        x, y, z = pad_center_tcp(40)
        self.assertEqual((x, y), (0.0, 0.0))
        self.assertAlmostEqual(-z * 1000, 97.0 - 13.0)

    def test_pad_center_stays_put_while_the_fingers_close(self):
        spec = load_spec()
        move = Move('close', Pose((PAN_X + 0.2, 0.0, 0.02)), Pose((PAN_X + 0.2, 0.0, 0.02), opening_mm=HOLD_MM))
        plan = plan_move(spec, move, samples=5, tcp=pad_center_tcp)
        for sample in plan.samples:
            got = tcp_position(spec, sample.q, pad_center_tcp(sample.opening_mm))
            self.assertLess(math.dist(got, move.start.xyz) * 1000, 0.1)
        self.assertNotEqual(plan.samples[0].q['elbow_flex'], plan.samples[-1].q['elbow_flex'])

    def test_a_fixed_tcp_still_works(self):
        spec = load_spec()
        plan = plan_move(spec, Move('m', READY, READY), samples=3, tcp=SHELL_TCP_M)
        self.assertLess(math.dist(tcp_position(spec, plan.samples[0].q, SHELL_TCP_M), READY.xyz) * 1000, 0.1)


class ArcPathTests(unittest.TestCase):
    def setUp(self):
        self.spec = load_spec()

    def radius(self, sample):
        x, y, _ = tcp_position(self.spec, sample.q)
        return math.hypot(x - PAN_X, y)

    def test_arc_keeps_its_distance_from_the_pan_axis(self):
        a, b = Pose((*polar(0.20, 72), 0.06)), Pose((*polar(0.16, -45), 0.06))
        straight = plan_move(self.spec, Move('s', a, b), samples=17)
        arc = plan_move(self.spec, Move('a', a, b, arc=True), samples=17)
        self.assertLess(min(self.radius(s) for s in straight.samples), 0.10)
        self.assertGreater(min(self.radius(s) for s in arc.samples), 0.15)

    def test_arc_takes_the_short_way_round(self):
        a, b = Pose((*polar(0.20, 170), 0.06)), Pose((*polar(0.20, -170), 0.06))
        plan = plan_move(self.spec, Move('a', a, b, arc=True), samples=9)
        pans = [math.degrees(s.q['shoulder_pan']) for s in plan.samples]
        self.assertAlmostEqual(abs(pans[4]), 180, delta=1)

    def test_compensated_moves_reach_everything_at_the_survey_layout(self):
        for move in compensated_move_list(SURVEY_LAYOUT):
            if move.name.startswith('15'):
                continue                              # 33 cm is beyond reach on purpose
            plan = plan_move(self.spec, move, samples=9, tcp=pad_center_tcp)
            self.assertFalse(any(s.unreachable for s in plan.samples), move.name)

    def test_compensated_moves_clear_the_block_with_open_fingers(self):
        hover = next(m for m in compensated_move_list(SURVEY_LAYOUT) if m.name.startswith('02')).start
        self.assertGreaterEqual(hover.xyz[2] * 1000 - PAD_CENTER_BEHIND_TIP_MM, 40 + 5)  # tip above the block top


if __name__ == '__main__':
    unittest.main()
