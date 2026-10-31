import json
import math
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from arm_contracts.messages import (AGE_LIMIT_MS, ArmProfile, ContractError, EndEffectorTarget, JointCommand, Receiver, RobotState,
                                    check_profile, parse_message, stop_reason, to_line)
from arm_contracts.profiles import small_arm_profile

# Expected values come from docs/interfaces/contracts-v0.1.md (sections noted per test).

ARM = ('shoulder_pan', 'shoulder_lift', 'elbow_flex', 'wrist_flex', 'wrist_roll')
POSE = {name: 0.0 for name in ARM}


def target(**kw):
    fields = dict(t_ms=1000.0, seq=1, robot_id='small_arm', position_m=(0.18, 0.02, 0.09), grip=0.35,
                  mode='track', enabled=True)
    return EndEffectorTarget(**{**fields, **kw})


def command(**kw):
    fields = dict(t_ms=1000.0, seq=1, robot_id='small_arm', profile_version='small_arm/1.0',
                  joints_rad=POSE, grip=0.0, enabled=True, ik_ok=True)
    return JointCommand(**{**fields, **kw})


def state(**kw):
    fields = dict(t_ms=1000.0, seq=1, robot_id='small_arm', joints_commanded_rad=POSE,
                  joints_measured_rad=None, state_source='commanded_only')
    return RobotState(**{**fields, **kw})


def as_dict(message, **changes):
    return {**json.loads(to_line(message)), **changes}


class RoundTripTests(unittest.TestCase):
    def test_draft_example_line_parses(self):  # section 2
        line = ('{"contract":"ee_target/0.1","t_ms":1523004.2,"seq":812,"robot_id":"small_arm",'
                '"frame":"robot_base","position_m":[0.18,0.02,0.09],"orientation_wxyz":null,"grip":0.35,'
                '"mode":"track","enabled":true,"source":"live"}')
        message = parse_message(line)
        self.assertIsInstance(message, EndEffectorTarget)
        self.assertEqual(message.seq, 812)
        self.assertEqual(message.position_m, (0.18, 0.02, 0.09))
        self.assertIsNone(message.orientation_wxyz)

    def test_every_message_survives_a_round_trip(self):
        for message in (target(orientation_wxyz=(1.0, 0.0, 0.0, 0.0)), command(), state(),
                        state(joints_measured_rad=POSE, state_source='sim', stopped_reason='stale',
                              ee_measured_position_m=(0.1, 0.0, 0.1))):
            self.assertEqual(parse_message(to_line(message)), message)

    def test_line_carries_kind_and_version(self):
        self.assertEqual(json.loads(to_line(command()))['contract'], 'joint_cmd/0.1')
        self.assertEqual(json.loads(to_line(state()))['contract'], 'robot_state/0.1')

    def test_line_is_one_line(self):
        self.assertNotIn('\n', to_line(target()))

    def test_joint_command_defaults_to_200_ms_max_age(self):  # section 3
        self.assertEqual(command().max_age_ms, 200.0)


class VersionTests(unittest.TestCase):  # section 1
    def test_other_major_is_rejected(self):
        with self.assertRaisesRegex(ContractError, 'major'):
            parse_message(json.dumps(as_dict(target(), contract='ee_target/1.0')))

    def test_newer_minor_with_an_extra_field_is_accepted(self):
        message = parse_message(json.dumps(as_dict(target(), contract='ee_target/0.2', fingers=[1, 2])))
        self.assertEqual(message.seq, 1)

    def test_broken_contract_tags_are_rejected(self):
        for tag in ('ee_target', 'ee_target/x.y', 'nope/0.1', '', 7, None):
            with self.assertRaises(ContractError, msg=repr(tag)):
                parse_message(json.dumps(as_dict(target(), contract=tag)))


class ParseRejectionTests(unittest.TestCase):
    def test_not_json_or_not_an_object(self):
        for line in ('', '{', '[1, 2]', '3'):
            with self.assertRaises(ContractError, msg=line):
                parse_message(line)

    def test_nan_and_infinity_in_the_raw_line(self):  # section 5.1; python's json accepts these by default
        good = to_line(target())
        for bad in (good.replace('0.18', 'NaN'), good.replace('0.18', 'Infinity'), good.replace('0.18', '-Infinity')):
            with self.assertRaises(ContractError, msg=bad):
                parse_message(bad)

    def test_missing_field(self):
        data = as_dict(target())
        del data['grip']
        with self.assertRaisesRegex(ContractError, 'grip'):
            parse_message(json.dumps(data))

    def test_integer_too_large_for_a_float(self):  # math.isfinite would raise OverflowError
        with self.assertRaises(ContractError):
            parse_message(json.dumps(as_dict(target(), t_ms=10**400)))


class ValueRuleTests(unittest.TestCase):  # section 5
    def test_numbers_must_be_finite(self):
        for bad in (math.nan, math.inf, -math.inf):
            with self.assertRaises(ContractError):
                target(position_m=(bad, 0.0, 0.0))
            with self.assertRaises(ContractError):
                target(t_ms=bad)
            with self.assertRaises(ContractError):
                command(joints_rad={**POSE, 'elbow_flex': bad})

    def test_booleans_are_not_numbers(self):
        with self.assertRaises(ContractError):
            target(position_m=(True, 0.0, 0.0))
        with self.assertRaises(ContractError):
            target(grip=True)
        with self.assertRaises(ContractError):
            target(seq=True)

    def test_flags_must_be_real_booleans(self):
        with self.assertRaises(ContractError):
            target(enabled=1)
        with self.assertRaises(ContractError):
            command(ik_ok=0)

    def test_grip_range(self):
        for good in (0, 0.5, 1):
            self.assertEqual(target(grip=good).grip, good)
        for bad in (-0.01, 1.01):
            with self.assertRaises(ContractError):
                target(grip=bad)

    def test_quaternion_must_be_unit_length(self):
        self.assertIsNotNone(target(orientation_wxyz=(1.0005, 0.0, 0.0, 0.0)).orientation_wxyz)
        for bad in ((1.01, 0.0, 0.0, 0.0), (0.0, 0.0, 0.0, 0.0), (1.0, 0.0, 0.0)):
            with self.assertRaises(ContractError, msg=bad):
                target(orientation_wxyz=bad)

    def test_position_needs_three_numbers(self):
        with self.assertRaises(ContractError):
            target(position_m=(0.1, 0.2))
        with self.assertRaises(ContractError):
            target(position_m='abc')

    def test_seq_is_a_non_negative_integer(self):
        for bad in (-1, 1.5):
            with self.assertRaises(ContractError):
                target(seq=bad)

    def test_closed_word_lists(self):
        with self.assertRaises(ContractError):
            target(mode='fast')
        with self.assertRaises(ContractError):
            target(source='dream')
        with self.assertRaises(ContractError):
            target(frame='camera')  # robot_base only in v0.1
        with self.assertRaises(ContractError):
            state(state_source='guess')

    def test_max_age_must_be_positive(self):
        for bad in (0, -5):
            with self.assertRaises(ContractError):
                command(max_age_ms=bad)

    def test_commanded_angles_cannot_pose_as_measured(self):  # section 4
        with self.assertRaises(ContractError):
            state(state_source='commanded_only', joints_measured_rad=POSE)

    def test_readback_sources_need_measured_angles(self):  # section 4
        for source in ('sim', 'servo_readback'):
            with self.assertRaises(ContractError):
                state(state_source=source, joints_measured_rad=None)


class ProfileTests(unittest.TestCase):  # sections 3 and 5.3-5.4
    def setUp(self):
        self.profile = small_arm_profile()

    def test_small_arm_profile_comes_from_the_spec(self):
        self.assertEqual(self.profile.robot_id, 'small_arm')
        self.assertEqual(self.profile.version, 'small_arm/1.0')
        self.assertEqual(self.profile.joints, ARM)  # the gripper travels in grip, not joints_rad

    def test_matching_messages_pass(self):
        for message in (target(), command(), state(), state(joints_measured_rad=POSE, state_source='sim')):
            check_profile(message, self.profile)

    def test_other_robot_is_rejected(self):
        for message in (target(robot_id='industrial_sim'), command(robot_id='industrial_sim'),
                        state(robot_id='industrial_sim')):
            with self.assertRaisesRegex(ContractError, 'robot_id'):
                check_profile(message, self.profile)

    def test_other_profile_version_is_rejected(self):
        with self.assertRaisesRegex(ContractError, 'profile_version'):
            check_profile(command(profile_version='small_arm/0.2'), self.profile)

    def test_missing_and_extra_joints_are_rejected(self):
        short = {k: v for k, v in POSE.items() if k != 'elbow_flex'}
        for joints in (short, {**POSE, 'gripper': 0.0}):
            with self.assertRaisesRegex(ContractError, 'joints'):
                check_profile(command(joints_rad=joints), self.profile)

    def test_state_joint_names_are_checked_both_ways(self):
        short = {k: v for k, v in POSE.items() if k != 'elbow_flex'}
        with self.assertRaises(ContractError):
            check_profile(state(joints_commanded_rad=short), self.profile)
        with self.assertRaises(ContractError):
            check_profile(state(joints_measured_rad=short, state_source='sim'), self.profile)

    def test_a_custom_profile_is_enough(self):  # adding an arm = adding a profile
        check_profile(command(robot_id='two', profile_version='two/1', joints_rad={'a': 0.0}),
                      ArmProfile('two', 'two/1', ('a',)))


class StopReasonTests(unittest.TestCase):  # section 6
    def test_tracking_target_moves(self):
        self.assertIsNone(stop_reason(target(), 1000.0))
        self.assertIsNone(stop_reason(target(mode='fine'), 1000.0))

    def test_target_hold_and_disabled_stop(self):
        self.assertEqual(stop_reason(target(mode='hold'), 1000.0), 'hold')
        self.assertEqual(stop_reason(target(enabled=False), 1000.0), 'disabled')

    def test_fresh_command_moves(self):
        self.assertIsNone(stop_reason(command(), 1000.0))
        self.assertIsNone(stop_reason(command(), 1200.0))

    def test_command_flags_stop(self):
        self.assertEqual(stop_reason(command(enabled=False), 1000.0), 'disabled')
        self.assertEqual(stop_reason(command(ik_ok=False), 1000.0), 'ik')

    def test_old_command_is_stale(self):
        self.assertEqual(stop_reason(command(), 1200.1), 'stale')

    def test_command_from_the_future_is_stale(self):  # another clock: its age means nothing
        self.assertEqual(stop_reason(command(), 999.0), 'stale')

    def test_state_reports_its_own_reason(self):
        self.assertEqual(stop_reason(state(stopped_reason='estop'), 1000.0), 'estop')
        self.assertIsNone(stop_reason(state(), 1000.0))


class ReceiverTests(unittest.TestCase):  # sections 5.5-5.6
    def setUp(self):
        self.rx = Receiver(EndEffectorTarget, small_arm_profile())

    def test_good_line_passes(self):
        got = self.rx.receive(to_line(target()), 1000.0)
        self.assertEqual(got.message, target())
        self.assertIsNone(got.problem)
        self.assertIsNone(got.stop)

    def test_objects_are_accepted_too(self):  # in-process calls first, section 8
        self.assertEqual(self.rx.receive(target(), 1000.0).message, target())

    def test_repeated_and_older_seq_are_dropped(self):
        self.rx.receive(target(seq=5), 1000.0)
        for seq in (5, 4):
            got = self.rx.receive(target(seq=seq), 1000.0)
            self.assertIsNone(got.message)
            self.assertIn('seq', got.problem)
            self.assertEqual(got.stop, 'invalid')

    def test_a_dropped_message_does_not_move_the_seq_mark(self):
        self.rx.receive(target(seq=5), 1000.0)
        self.rx.receive(target(seq=3), 1000.0)
        self.assertIsNotNone(self.rx.receive(target(seq=6), 1000.0).message)

    def test_a_bad_message_does_not_move_the_seq_mark(self):
        self.rx.receive(target(seq=5), 1000.0)
        self.rx.receive(target(seq=9, robot_id='industrial_sim'), 1000.0)
        self.assertIsNotNone(self.rx.receive(target(seq=6), 1000.0).message)

    def test_seq_gaps_count_as_lost(self):
        self.rx.receive(target(seq=1), 1000.0)
        self.assertIsNotNone(self.rx.receive(target(seq=4), 1000.0).message)
        self.assertEqual(self.rx.lost, 2)

    def test_garbage_means_hold_with_a_reason(self):
        got = self.rx.receive('{not json', 1000.0)
        self.assertIsNone(got.message)
        self.assertTrue(got.problem)
        self.assertEqual(got.stop, 'invalid')
        self.assertEqual(self.rx.rejected, 1)

    def test_wrong_kind_is_rejected(self):
        got = self.rx.receive(to_line(command()), 1000.0)
        self.assertIsNone(got.message)
        self.assertIn('joint_cmd', got.problem)

    def test_wrong_robot_is_rejected(self):
        got = self.rx.receive(target(robot_id='industrial_sim'), 1000.0)
        self.assertIsNone(got.message)
        self.assertIn('robot_id', got.problem)

    def test_valid_hold_passes_with_a_stop(self):
        got = self.rx.receive(target(mode='hold'), 1000.0)
        self.assertIsNotNone(got.message)
        self.assertIsNone(got.problem)
        self.assertEqual(got.stop, 'hold')

    def test_stale_command_passes_with_a_stop(self):
        rx = Receiver(JointCommand, small_arm_profile())
        got = rx.receive(command(), 5000.0)
        self.assertIsNotNone(got.message)
        self.assertEqual(got.stop, 'stale')

    def test_messages_are_frozen(self):
        message = target()
        with self.assertRaises(AttributeError):
            message.seq = 2
        self.assertEqual(replace(message, seq=2).seq, 2)


class FailClosedTests(unittest.TestCase):  # each of these once let the arm move, or killed the receiver
    def setUp(self):
        self.rx = Receiver(EndEffectorTarget, small_arm_profile())

    def test_old_target_is_stale(self):
        self.assertEqual(stop_reason(target(), 1000.0 + AGE_LIMIT_MS + 1), 'stale')

    def test_target_from_the_future_is_stale(self):
        self.assertEqual(stop_reason(target(), 999.0), 'stale')

    def test_a_command_cannot_grant_itself_a_longer_age(self):
        self.assertEqual(stop_reason(command(max_age_ms=1e308), 1000.0 + AGE_LIMIT_MS + 1), 'stale')

    def test_a_command_can_ask_for_a_shorter_age(self):
        self.assertEqual(stop_reason(command(max_age_ms=50.0), 1051.0), 'stale')
        self.assertIsNone(stop_reason(command(max_age_ms=50.0), 1049.0))

    def test_a_silent_sender_means_hold(self):
        self.assertEqual(self.rx.silence_stop(1000.0), 'silent')  # nothing received yet
        self.rx.receive(target(), 1000.0)
        self.assertIsNone(self.rx.silence_stop(1000.0 + AGE_LIMIT_MS))
        self.assertEqual(self.rx.silence_stop(1000.0 + AGE_LIMIT_MS + 1), 'silent')

    def test_a_changed_object_is_checked_again(self):
        rx = Receiver(JointCommand, small_arm_profile())
        message = command()
        message.joints_rad['shoulder_pan'] = math.nan
        got = rx.receive(message, 1000.0)
        self.assertIsNone(got.message)
        self.assertEqual(got.stop, 'invalid')

    def test_the_profile_must_be_stated(self):
        with self.assertRaises(TypeError):
            Receiver(JointCommand)

    def test_safety_fields_have_no_defaults(self):
        for missing in ('enabled', 'ik_ok'):
            fields = dict(t_ms=1.0, seq=1, robot_id='small_arm', profile_version='small_arm/1.0',
                          joints_rad=POSE, grip=0.0, enabled=True, ik_ok=True)
            del fields[missing]
            with self.assertRaises(TypeError, msg=missing):
                JointCommand(**fields)
        for missing in ('enabled', 'mode'):
            fields = dict(t_ms=1.0, seq=1, robot_id='small_arm', position_m=(0.1, 0.0, 0.1), grip=0.0,
                          mode='track', enabled=True)
            del fields[missing]
            with self.assertRaises(TypeError, msg=missing):
                EndEffectorTarget(**fields)

    def test_duplicate_keys_are_rejected(self):
        line = to_line(target()).replace('"enabled":true', '"enabled":false,"enabled":true')
        self.assertIn('"enabled":false,"enabled":true', line)
        with self.assertRaisesRegex(ContractError, 'enabled'):
            parse_message(line)

    def test_odd_contract_tags_are_rejected(self):
        for tag in ('ee_target/\u0660.\u0661', 'ee_target/0.1\n', 'ee_target/0.' + '1' * 5000):
            with self.assertRaises(ContractError, msg=repr(tag[:20])):
                parse_message(json.dumps(as_dict(target(), contract=tag)))

    def test_hostile_lines_mean_hold_instead_of_a_crash(self):
        huge_quaternion = json.dumps(as_dict(target(), orientation_wxyz=[10 ** 200, 0, 0, 0]))
        for line in (huge_quaternion, '[' * 200000, json.dumps(as_dict(target(), contract='x/' + '9' * 5000))):
            got = self.rx.receive(line, 1000.0)
            self.assertIsNone(got.message)
            self.assertEqual(got.stop, 'invalid')

    def test_a_bad_clock_means_hold_and_keeps_the_seq(self):
        got = self.rx.receive(target(seq=5), None)
        self.assertEqual(got.stop, 'invalid')
        self.assertIsNotNone(self.rx.receive(target(seq=5), 1000.0).message)

    def test_impossible_sizes_are_rejected(self):
        with self.assertRaises(ContractError):
            target(position_m=(1e300, 0.0, 0.0))
        with self.assertRaises(ContractError):
            command(joints_rad={**POSE, 'elbow_flex': 1e308})

    def test_every_flag_and_name_is_type_checked(self):
        for bad in (dict(enabled='false'), dict(ik_ok='false'), dict(robot_id=7), dict(profile_version=7),
                    dict(joints_rad={**POSE, 'elbow_flex': 'x'})):
            with self.assertRaises(ContractError, msg=bad):
                command(**bad)
        with self.assertRaises(ContractError):
            state(stopped_reason=7)
        with self.assertRaises(ContractError):
            state(joints_measured_rad={**POSE, 'elbow_flex': math.nan}, state_source='sim')

    def test_seq_zero_is_remembered(self):
        self.rx.receive(target(seq=0), 1000.0)
        self.assertIsNone(self.rx.receive(target(seq=0), 1000.0).message)

    def test_a_restarted_sender_needs_an_explicit_reset(self):
        self.rx.receive(target(seq=9), 1000.0)
        self.assertIsNone(self.rx.receive(target(seq=1), 1000.0).message)
        self.rx.reset()
        self.assertIsNotNone(self.rx.receive(target(seq=1), 1000.0).message)


if __name__ == '__main__':
    unittest.main()
