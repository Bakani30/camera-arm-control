import json
import math
import tempfile
import unittest
from pathlib import Path

import numpy as np

from arm_contracts.from_camera_log import targets_from_frames
from arm_contracts.messages import ContractError, EndEffectorTarget, JointCommand, RobotState, Receiver, to_line
from arm_contracts.mock_arm import MockArm, main as mock_arm_main, render
from arm_contracts.profiles import small_arm_profile
from arm_contracts.replay import ReplayWriter, read_replay, write_replay
from arm_contracts.scripted import SAMPLE_REPLAY, circle, demo, known_points, square
from arm_spec import forward_kinematics, load_spec, soft_limit_problems
from camera_gestures.mapping import DRAG_TARGETS_M, MappingConfig


def target(seq=1, t_ms=None, **kw):
    fields = dict(robot_id='small_arm', position_m=(0.2, 0.0, 0.1), grip=0.0, mode='track', enabled=True)
    return EndEffectorTarget(t_ms=seq * 10.0 if t_ms is None else t_ms, seq=seq, **{**fields, **kw})


class ReplayFileTests(unittest.TestCase):  # section 7
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / 'run.jsonl'

    def write_lines(self, *lines):
        self.path.write_text('\n'.join(lines) + '\n', encoding='utf-8')

    def header(self, **kw):
        fields = dict(contract='replay_header/0.1', created='2026-10-31T00:00:00Z', kind='ee_target',
                      camera=None, notes='')
        return json.dumps({**fields, **kw})

    def test_round_trip(self):
        messages = [target(1), target(2, mode='hold')]
        write_replay(self.path, 'ee_target', messages, notes='hello')
        header, loaded = read_replay(self.path)
        self.assertEqual(loaded, messages)
        self.assertEqual(header['kind'], 'ee_target')
        self.assertEqual(header['notes'], 'hello')

    def test_stream_output_reads_back(self):
        camera = {'width': 1280, 'height': 720, 'f_px': 900.0}
        messages = [target(1), target(2), target(3, mode='hold')]
        with ReplayWriter(self.path, 'ee_target', camera=camera, notes='live') as writer:
            for message in messages:
                writer.write(message)
        header, loaded = read_replay(self.path)
        self.assertEqual(loaded, messages)
        self.assertEqual((header['camera'], header['notes']), (camera, 'live'))

    def test_stream_keeps_lines_without_close(self):
        writer = ReplayWriter(self.path, 'ee_target')
        self.addCleanup(writer.close)
        writer.write(target(1))
        writer.write(target(2))
        self.assertEqual(read_replay(self.path)[1], [target(1), target(2)])

    def test_stream_with_no_messages_reads_back(self):
        ReplayWriter(self.path, 'ee_target').close()
        self.assertEqual(read_replay(self.path)[1], [])

    def test_stream_refuses_out_of_order_seq(self):
        with ReplayWriter(self.path, 'ee_target') as writer:
            writer.write(target(2))
            with self.assertRaisesRegex(ContractError, 'seq'):
                writer.write(target(2))
        self.assertEqual(read_replay(self.path)[1], [target(2)])

    def test_stream_refuses_an_unknown_kind(self):
        with self.assertRaisesRegex(ContractError, 'kind'):
            ReplayWriter(self.path, 'nonsense')
        self.assertFalse(self.path.exists())

    def test_first_line_is_the_header(self):
        write_replay(self.path, 'ee_target', [target(1)])
        first = json.loads(self.path.read_text(encoding='utf-8').splitlines()[0])
        self.assertEqual(first['contract'], 'replay_header/0.1')

    def test_camera_block_is_kept(self):
        camera = {'width': 1280, 'height': 720, 'f_px': None}
        write_replay(self.path, 'ee_target', [target(1)], camera=camera)
        self.assertEqual(read_replay(self.path)[0]['camera'], camera)

    def test_writer_refuses_what_the_reader_would_refuse(self):
        with self.assertRaisesRegex(ContractError, 'seq'):
            write_replay(self.path, 'ee_target', [target(2), target(2)])

    def test_writer_takes_a_generator(self):
        write_replay(self.path, 'ee_target', (target(k) for k in (1, 2)))
        self.assertEqual(len(read_replay(self.path)[1]), 2)

    def test_reader_refuses_an_unhashable_kind(self):
        self.write_lines(self.header(kind=['ee_target']), to_line(target(1)))
        with self.assertRaises(ContractError):
            read_replay(self.path)

    def test_writer_refuses_a_mixed_or_empty_file(self):
        with self.assertRaises(ContractError):
            write_replay(self.path, 'joint_cmd', [target(1)])
        with self.assertRaises(ContractError):
            write_replay(self.path, 'ee_target', [])
        with self.assertRaises(ContractError):
            write_replay(self.path, 'nope', [target(1)])

    def test_reader_refuses_a_missing_header(self):
        self.write_lines(to_line(target(1)))
        with self.assertRaisesRegex(ContractError, 'header'):
            read_replay(self.path)

    def test_reader_refuses_a_header_of_another_major(self):
        self.write_lines(self.header(contract='replay_header/1.0'), to_line(target(1)))
        with self.assertRaisesRegex(ContractError, 'major'):
            read_replay(self.path)

    def test_reader_refuses_an_unknown_kind(self):
        self.write_lines(self.header(kind='nope'), to_line(target(1)))
        with self.assertRaisesRegex(ContractError, 'nope'):
            read_replay(self.path)

    def test_reader_names_the_broken_line(self):
        self.write_lines(self.header(), to_line(target(1)), '{oops')
        with self.assertRaisesRegex(ContractError, ':3:'):
            read_replay(self.path)

    def test_reader_refuses_mixed_kinds_and_bad_seq(self):
        command = JointCommand(t_ms=1.0, seq=2, robot_id='small_arm', profile_version='small_arm/1.0',
                               joints_rad={'a': 0.0}, grip=0.0, enabled=True, ik_ok=True)
        self.write_lines(self.header(), to_line(target(1)), to_line(command))
        with self.assertRaisesRegex(ContractError, ':3:'):
            read_replay(self.path)
        self.write_lines(self.header(), to_line(target(2)), to_line(target(2)))
        with self.assertRaisesRegex(ContractError, 'seq'):
            read_replay(self.path)

    def test_reader_accepts_windows_line_endings(self):
        self.path.write_bytes((self.header() + '\r\n' + to_line(target(1)) + '\r\n').encode('utf-8'))
        self.assertEqual(len(read_replay(self.path)[1]), 1)

    def test_state_files_work_too(self):
        state = RobotState(t_ms=1.0, seq=1, robot_id='small_arm', joints_commanded_rad={'a': 0.0},
                           joints_measured_rad=None, state_source='commanded_only')
        write_replay(self.path, 'robot_state', [state])
        self.assertEqual(read_replay(self.path)[1], [state])


class ScriptedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # (radius from the pan axis, height) of TCP poses the soft limits allow; radial symmetry covers pan
        spec = load_spec()
        cls.pan_x = spec.joint('shoulder_pan').origin_xyz[0]
        cls.reachable = []
        for lift in range(-90, 91, 5):
            for elbow in range(-90, 71, 5):
                for wrist in range(-90, 91, 15):
                    q = {'shoulder_lift': math.radians(lift), 'elbow_flex': math.radians(elbow),
                         'wrist_flex': math.radians(wrist)}
                    if not soft_limit_problems(spec, q):
                        x, _, z = forward_kinematics(spec, q)
                        cls.reachable.append((x - cls.pan_x, z))

    def assertReachable(self, position):
        x, y, z = position
        radius = math.hypot(x - self.pan_x, y)
        nearest = min(math.hypot(radius - r, z - h) for r, h in self.reachable)
        self.assertLess(nearest, 0.015, position)

    def test_drag_targets_stay_within_the_soft_limits(self):
        for point in DRAG_TARGETS_M:
            self.assertReachable(point)

    def test_mapping_box_stays_within_the_radius_limits(self):
        limits = load_spec().raw['soft_limits']
        config = MappingConfig()
        near = math.hypot(config.box_min_m[0] - self.pan_x, 0)
        far = math.hypot(config.box_max_m[0] - self.pan_x, config.box_max_m[1])
        self.assertGreaterEqual(near, limits['tcp_min_radius_from_pan_axis_m'])
        self.assertLessEqual(far, limits['tcp_max_radius_from_pan_axis_m'])

    def test_circle_keeps_its_radius(self):
        points = circle(center=(0.25, 0.0, 0.12), radius=0.04, points=32)
        self.assertEqual(len(points), 32)
        for p in points:
            x, y, z = p.position_m
            self.assertAlmostEqual(math.hypot(x - 0.25, y), 0.04, places=5)
            self.assertAlmostEqual(z, 0.12)

    def test_square_stays_on_its_outline(self):
        for p in square(center=(0.25, 0.0, 0.12), half_side=0.04, points_per_side=4):
            x, y, _ = p.position_m
            self.assertAlmostEqual(max(abs(x - 0.25), abs(y)), 0.04, places=6)

    def test_scripts_are_valid_streams(self):
        for points in (circle(), square(), demo()):
            rx = Receiver(EndEffectorTarget, small_arm_profile())
            for p in points:
                self.assertIsNotNone(rx.receive(p, p.t_ms).message)
                self.assertEqual(p.source, 'script')
            self.assertEqual(rx.lost, 0)
            times = [p.t_ms for p in points]
            self.assertEqual(times, sorted(times))

    def test_default_scripts_stay_within_the_soft_limits(self):
        for points in (circle(), square(), demo()):
            for p in points:
                self.assertReachable(p.position_m)

    def test_known_points_match_forward_kinematics(self):
        spec = load_spec()
        known = known_points(spec)
        self.assertGreaterEqual(len(known), 3)
        for q, p in known:
            self.assertEqual(soft_limit_problems(spec, q), [])
            for got, want in zip(p.position_m, forward_kinematics(spec, q)):
                self.assertAlmostEqual(got, want, places=5)

    def test_sample_file_matches_the_script(self):
        _, loaded = read_replay(SAMPLE_REPLAY)
        self.assertEqual(loaded, demo())

    def test_demo_holds_and_disables_partway(self):
        modes = {(p.mode, p.enabled) for p in demo()}
        self.assertIn(('hold', True), modes)
        self.assertIn(('track', False), modes)


class MockArmTests(unittest.TestCase):
    def test_starts_with_no_point(self):
        self.assertIsNone(MockArm().position)

    def test_tracks_a_target(self):
        arm = MockArm()
        arm.receive(target(1, position_m=(0.2, 0.1, 0.1), grip=0.5), 10.0)
        self.assertEqual(arm.position, (0.2, 0.1, 0.1))
        self.assertEqual(arm.grip, 0.5)
        self.assertEqual(arm.status, 'moving')

    def test_hold_and_disabled_freeze_the_point(self):
        for stop in (dict(mode='hold'), dict(enabled=False)):
            arm = MockArm()
            arm.receive(target(1, position_m=(0.2, 0.0, 0.1)), 10.0)
            arm.receive(target(2, position_m=(0.3, 0.0, 0.1), **stop), 20.0)
            self.assertEqual(arm.position, (0.2, 0.0, 0.1))
            self.assertNotEqual(arm.status, 'moving')

    def test_bad_message_freezes_the_point_and_keeps_the_reason(self):
        arm = MockArm()
        arm.receive(target(1), 10.0)
        arm.receive('{oops', 20.0)
        self.assertEqual(arm.position, (0.2, 0.0, 0.1))
        self.assertEqual(arm.status, 'invalid')
        self.assertTrue(arm.problem)

    def test_recovers_after_a_stop(self):
        arm = MockArm()
        arm.receive(target(1, mode='hold'), 10.0)
        arm.receive(target(2, position_m=(0.3, 0.0, 0.1)), 20.0)
        self.assertEqual(arm.position, (0.3, 0.0, 0.1))
        self.assertEqual(arm.status, 'moving')
        self.assertIsNone(arm.problem)

    def test_render_default_is_unchanged(self):
        arm = MockArm()
        self.assertTrue(np.array_equal(render(arm), render(arm, box=None, marks=())))

    def test_render_draws_box_and_marks(self):
        arm = MockArm()
        plain = render(arm)
        box = ((.18, -.12, .04), (.33, .12, .20))
        with_box = render(arm, box=box)
        self.assertFalse(np.array_equal(plain, with_box))
        self.assertFalse(np.array_equal(with_box, render(arm, box=box, marks=((.25, 0., .12),))))

    def test_render_changes_when_the_point_moves(self):
        arm = MockArm()
        empty = render(arm)
        self.assertEqual(empty.ndim, 3)
        arm.receive(target(1), 10.0)
        self.assertFalse(np.array_equal(render(arm), empty))

    def test_cli_saves_a_picture_without_a_window(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'mock.png'
            self.assertEqual(mock_arm_main([str(SAMPLE_REPLAY), '--save', str(out)]), 0)
            self.assertGreater(out.stat().st_size, 1000)


def frame(n, screen=(0.5, 0.5), active=True, output='01', depth=0.0, **kw):
    fields = dict(frame=n, receipt_ms=n * 33, output=output, screen_target=list(screen), target_active=active,
                  depth_relative=depth, hand_present=True, stale=False)
    return json.dumps({**fields, **kw})


class CameraLogTests(unittest.TestCase):  # the Friday chain: replay -> current mapping -> mock arm
    def test_screen_center_maps_to_the_box_center(self):
        got = targets_from_frames([frame(1)], center=(0.25, 0.0, 0.12))[0]
        self.assertEqual(got.position_m, (0.25, 0.0, 0.12))
        self.assertEqual(got.source, 'replay')
        self.assertEqual(got.mode, 'track')

    def test_directions(self):
        center = targets_from_frames([frame(1)])[0].position_m
        right = targets_from_frames([frame(1, screen=(1.0, 0.5))])[0].position_m
        up = targets_from_frames([frame(1, screen=(0.5, 0.0))])[0].position_m
        nearer = targets_from_frames([frame(1, depth=1.0)])[0].position_m
        self.assertLess(right[1], center[1])   # screen right -> robot right (-y)
        self.assertGreater(up[2], center[2])   # screen up -> up
        self.assertGreater(nearer[0], center[0])  # hand nearer the camera -> forward

    def test_lost_hand_inactive_target_and_stale_frame_all_hold(self):  # section 6
        for bad in (dict(active=False), dict(hand_present=False), dict(stale=True)):
            self.assertEqual(targets_from_frames([frame(1, **bad)])[0].mode, 'hold', bad)

    def test_only_a_clear_tracking_frame_tracks(self):  # missing or odd values must hold
        missing = json.loads(frame(1))
        del missing['stale']
        odd = json.loads(frame(1))
        odd['target_active'] = 'false'
        for line in (json.dumps(missing), json.dumps(odd)):
            self.assertEqual(targets_from_frames([line])[0].mode, 'hold', line)

    def test_grip_follows_the_code_and_keeps_it_on_00(self):
        got = targets_from_frames([frame(1, output='01'), frame(2, output='10'), frame(3, output='00'),
                                   frame(4, output='01')])
        self.assertEqual([t.grip for t in got], [0.0, 1.0, 1.0, 0.0])

    def test_missing_depth_stays_at_the_box_center(self):
        got = targets_from_frames([frame(1, depth=None)], center=(0.25, 0.0, 0.12))[0]
        self.assertEqual(got.position_m[0], 0.25)

    def test_depth_out_of_range_is_clamped(self):
        far = targets_from_frames([frame(1, depth=5.0)])[0].position_m
        limit = targets_from_frames([frame(1, depth=1.0)])[0].position_m
        self.assertEqual(far, limit)

    def test_nan_in_the_log_is_refused(self):  # clamping NaN would silently pick a box edge
        line = frame(1).replace('[0.5, 0.5]', '[NaN, 0.5]')
        self.assertIn('NaN', line)
        with self.assertRaises(ContractError):
            targets_from_frames([line])

    def test_old_log_format_is_refused(self):
        with self.assertRaisesRegex(ContractError, 'screen_target'):
            targets_from_frames([json.dumps(dict(frame=1, receipt_ms=33, output='00'))])

    def test_seq_and_time_come_from_the_log(self):
        got = targets_from_frames([frame(5), frame(9)])
        self.assertEqual([(t.seq, t.t_ms) for t in got], [(5, 165), (9, 297)])

    def test_chain_ends_on_the_mock_arm_and_stops_on_hand_loss(self):
        lines = [frame(1, screen=(0.4, 0.5)), frame(2, screen=(0.6, 0.5)),
                 frame(3, screen=(0.9, 0.5), hand_present=False, active=False), frame(4, screen=(0.9, 0.5), active=False)]
        arm = MockArm()
        positions = []
        for t in targets_from_frames(lines):
            arm.receive(to_line(t), t.t_ms)
            positions.append(arm.position)
        self.assertNotEqual(positions[0], positions[1])
        self.assertEqual(positions[1], positions[2])
        self.assertEqual(positions[2], positions[3])
        self.assertEqual(arm.status, 'hold')


if __name__ == '__main__':
    unittest.main()
