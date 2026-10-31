"""Contract v0.1 messages: a message object that exists has passed the value rules (contract section 5)."""
import json
import math
import re
from dataclasses import asdict, dataclass, fields, replace

MAJOR, MINOR = 0, 1
QUATERNION_TOLERANCE = 1e-3
DEFAULT_MAX_AGE_MS = 200.0
AGE_LIMIT_MS = 500.0     # the oldest message a receiver acts on, whatever the message asks for
MAX_POSITION_M = 10.0    # no arm in this project is this big: anything past it is a broken sender
MAX_JOINT_RAD = 4 * math.pi
MODES = ('track', 'hold', 'fine')
SOURCES = ('live', 'replay', 'script')
STATE_SOURCES = ('sim', 'servo_readback', 'commanded_only')
_CONTRACT_TAG = re.compile(r'([a-z_]+)/([0-9]{1,4})\.([0-9]{1,4})')


class ContractError(ValueError):
    pass


def _number(name, value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ContractError(f'{name} must be a number, got {value!r}')
    try:
        finite = math.isfinite(value)
    except OverflowError:  # an int too large for a float
        finite = False
    if not finite:
        raise ContractError(f'{name} must be finite, got {value!r}')
    return value


def _vector(name, value, size, limit):
    if not isinstance(value, (list, tuple)) or len(value) != size:
        raise ContractError(f'{name} must hold {size} numbers, got {value!r}')
    return tuple(_bounded(name, v, limit) for v in value)


def _bounded(name, value, limit):
    if abs(_number(name, value)) > limit:
        raise ContractError(f'{name} is past {limit}: {value!r}')
    return value


def _name(name, value):
    if not isinstance(value, str) or not value:
        raise ContractError(f'{name} must be a non-empty string, got {value!r}')
    return value


def _flag(name, value):
    if not isinstance(value, bool):
        raise ContractError(f'{name} must be true or false, got {value!r}')
    return value


def _choice(name, value, allowed):
    if value not in allowed:
        raise ContractError(f'{name} must be one of {allowed}, got {value!r}')
    return value


def _grip(value):
    if not 0 <= _number('grip', value) <= 1:
        raise ContractError(f'grip must be within 0..1, got {value!r}')
    return value


def _joints(name, value):
    if not isinstance(value, dict) or not value:
        raise ContractError(f'{name} must map joint names to angles, got {value!r}')
    return {_name(name, k): _bounded(f'{name}.{k}', v, MAX_JOINT_RAD) for k, v in value.items()}


def _stamp(message):
    _number('t_ms', message.t_ms)
    if isinstance(message.seq, bool) or not isinstance(message.seq, int) or message.seq < 0:
        raise ContractError(f'seq must be a non-negative integer, got {message.seq!r}')
    _name('robot_id', message.robot_id)


def _set(message, name, value):
    object.__setattr__(message, name, value)


@dataclass(frozen=True)
class EndEffectorTarget:
    """Section 2: where the gripper tip should be. Knows nothing about the arm model."""
    t_ms: float
    seq: int
    robot_id: str
    position_m: tuple
    grip: float
    mode: str              # no default: a sender states whether the arm may move
    enabled: bool
    orientation_wxyz: tuple = None
    source: str = 'live'
    frame: str = 'robot_base'
    kind = 'ee_target'

    def __post_init__(self):
        _stamp(self)
        _set(self, 'position_m', _vector('position_m', self.position_m, 3, MAX_POSITION_M))
        _grip(self.grip)
        if self.orientation_wxyz is not None:
            _set(self, 'orientation_wxyz', _vector('orientation_wxyz', self.orientation_wxyz, 4, 2.0))
            length = math.sqrt(sum(v * v for v in self.orientation_wxyz))
            if abs(length - 1) > QUATERNION_TOLERANCE:
                raise ContractError(f'orientation_wxyz must have length 1, got {length}')
        _choice('mode', self.mode, MODES)
        _flag('enabled', self.enabled)
        _choice('source', self.source, SOURCES)
        _choice('frame', self.frame, ('robot_base',))


@dataclass(frozen=True)
class JointCommand:
    """Section 3: joint angles for one arm profile. joints_rad leaves the gripper out; grip carries it."""
    t_ms: float
    seq: int
    robot_id: str
    profile_version: str
    joints_rad: dict
    grip: float
    enabled: bool          # no defaults: forgetting these after a failed IK must not mean move
    ik_ok: bool
    max_age_ms: float = DEFAULT_MAX_AGE_MS
    kind = 'joint_cmd'

    def __post_init__(self):
        _stamp(self)
        _name('profile_version', self.profile_version)
        _set(self, 'joints_rad', _joints('joints_rad', self.joints_rad))
        _grip(self.grip)
        if _number('max_age_ms', self.max_age_ms) <= 0:
            raise ContractError(f'max_age_ms must be positive, got {self.max_age_ms!r}')
        _flag('enabled', self.enabled)
        _flag('ik_ok', self.ik_ok)


@dataclass(frozen=True)
class RobotState:
    """Section 4: what the adapter sent and, when something measured it, where the arm is."""
    t_ms: float
    seq: int
    robot_id: str
    joints_commanded_rad: dict
    joints_measured_rad: dict
    state_source: str
    ee_measured_position_m: tuple = None
    stopped_reason: str = None
    kind = 'robot_state'

    def __post_init__(self):
        _stamp(self)
        _set(self, 'joints_commanded_rad', _joints('joints_commanded_rad', self.joints_commanded_rad))
        _choice('state_source', self.state_source, STATE_SOURCES)
        if self.state_source == 'commanded_only':
            if self.joints_measured_rad is not None:
                raise ContractError('commanded_only cannot carry measured angles')
        else:
            if self.joints_measured_rad is None:
                raise ContractError(f'{self.state_source} needs joints_measured_rad')
            _set(self, 'joints_measured_rad', _joints('joints_measured_rad', self.joints_measured_rad))
        if self.ee_measured_position_m is not None:
            _set(self, 'ee_measured_position_m', _vector('ee_measured_position_m', self.ee_measured_position_m, 3, MAX_POSITION_M))
        if self.stopped_reason is not None:
            _name('stopped_reason', self.stopped_reason)


KINDS = {cls.kind: cls for cls in (EndEffectorTarget, JointCommand, RobotState)}


def parse_contract_tag(tag):
    """(kind, minor) from a tag such as 'ee_target/0.1'; another major version is rejected."""
    match = _CONTRACT_TAG.fullmatch(tag) if isinstance(tag, str) else None
    if not match:
        raise ContractError(f'bad contract tag {tag!r}')
    if int(match[2]) != MAJOR:
        raise ContractError(f'{tag}: major version must be {MAJOR}')
    return match[1], int(match[3])


def _reject_constant(constant):
    raise ContractError(f'{constant} is not a finite number')


def _reject_duplicates(pairs):
    """Python's json keeps the last of two equal keys, so a line could say enabled twice and mean either."""
    data = {}
    for key, value in pairs:
        if key in data:
            raise ContractError(f'duplicate key {key!r}')
        data[key] = value
    return data


def load_line(line):
    """The JSON object in one line. Python's json would accept NaN and Infinity without parse_constant."""
    try:
        data = json.loads(line, parse_constant=_reject_constant, object_pairs_hook=_reject_duplicates)
    except (ValueError, RecursionError) as error:
        raise ContractError(f'not JSON: {str(error)[:200]}') from error
    if not isinstance(data, dict):
        raise ContractError(f'expected an object, got {data!r}')
    return data


def parse_message(line):
    """A checked message from one JSON line. Fields from a newer minor version are ignored."""
    data = load_line(line)
    kind, _ = parse_contract_tag(data.get('contract'))
    if kind not in KINDS:
        raise ContractError(f'unknown message kind {kind!r}')
    cls = KINDS[kind]
    missing = [f.name for f in fields(cls) if f.name not in data]
    if missing:
        raise ContractError(f'{kind}: missing {missing}')
    return cls(**{f.name: data[f.name] for f in fields(cls)})


def to_line(message):
    """One JSON line, without the trailing newline."""
    data = {'contract': f'{message.kind}/{MAJOR}.{MINOR}', **asdict(message)}
    return json.dumps(data, allow_nan=False, separators=(',', ':'))


@dataclass(frozen=True)
class ArmProfile:
    robot_id: str
    version: str
    joints: tuple


def _check_joint_names(name, joints, profile):
    missing = set(profile.joints) - set(joints)
    extra = set(joints) - set(profile.joints)
    if missing or extra:
        raise ContractError(f'{name}: joints missing {sorted(missing)}, extra {sorted(extra)}')


def check_profile(message, profile):
    """Rules 5.3-5.4: the message belongs to this profile. Raises ContractError if not."""
    if message.robot_id != profile.robot_id:
        raise ContractError(f'robot_id {message.robot_id!r}, loaded {profile.robot_id!r}')
    if isinstance(message, JointCommand):
        if message.profile_version != profile.version:
            raise ContractError(f'profile_version {message.profile_version!r}, loaded {profile.version!r}')
        _check_joint_names('joints_rad', message.joints_rad, profile)
    if isinstance(message, RobotState):
        _check_joint_names('joints_commanded_rad', message.joints_commanded_rad, profile)
        if message.joints_measured_rad is not None:
            _check_joint_names('joints_measured_rad', message.joints_measured_rad, profile)


def stop_reason(message, now_ms, age_limit_ms=AGE_LIMIT_MS):
    """Section 6: why the arm must hold on this message, None if it may move.

    now_ms must come from the sender's clock: t_ms is its monotonic clock, so age is only
    meaningful on one machine, and a message from the future means the clocks differ.
    A command may ask for a shorter age than age_limit_ms, never a longer one.
    """
    if isinstance(message, RobotState):
        return message.stopped_reason
    if not message.enabled:
        return 'disabled'
    if isinstance(message, EndEffectorTarget):
        if message.mode == 'hold':
            return 'hold'
        limit = age_limit_ms
    else:
        if not message.ik_ok:
            return 'ik'
        limit = min(message.max_age_ms, age_limit_ms)
    return None if 0 <= now_ms - message.t_ms <= limit else 'stale'


@dataclass(frozen=True)
class Received:
    message: object
    problem: str
    stop: str


class Receiver:
    """Rules 5.3-5.6 for one sender: a bad or out-of-order message is dropped and means hold."""

    def __init__(self, message_type, profile, age_limit_ms=AGE_LIMIT_MS):
        """profile has no default: pass None only where no arm can move, such as reading a file."""
        self.message_type = message_type
        self.profile = profile
        self.age_limit_ms = age_limit_ms
        self.last_seq = None
        self.last_heard_ms = None
        self.lost = 0
        self.rejected = 0

    def _check(self, data):
        message = parse_message(data) if isinstance(data, str) else data
        if not isinstance(message, self.message_type):
            raise ContractError(f'expected {self.message_type.kind}, got {getattr(message, "kind", type(message).__name__)}')
        message = replace(message)                     # its dicts can change after it was built: check it again
        if self.profile is not None:
            check_profile(message, self.profile)
        if self.last_seq is not None and message.seq <= self.last_seq:
            raise ContractError(f'seq {message.seq} is not after {self.last_seq}')
        return message

    def receive(self, data, now_ms):
        """data is one JSON line or a message object. Check .stop before moving; .problem is for the log.

        Nothing a sender can put in data may stop the loop: every failure here means hold.
        """
        try:
            _number('now_ms', now_ms)
            message = self._check(data)
        except (ValueError, TypeError, OverflowError, RecursionError) as error:
            self.rejected += 1
            return Received(None, str(error)[:300], 'invalid')
        if self.last_seq is not None:
            self.lost += message.seq - self.last_seq - 1
        self.last_seq = message.seq
        self.last_heard_ms = now_ms
        return Received(message, None, stop_reason(message, now_ms, self.age_limit_ms))

    def silence_stop(self, now_ms):
        """'silent' when no good message arrived within the age limit. A control loop calls this every cycle."""
        heard = self.last_heard_ms
        return None if heard is not None and 0 <= now_ms - heard <= self.age_limit_ms else 'silent'

    def reset(self):
        """Forget the sender, after its restart: until then its low seq numbers are dropped and the arm holds."""
        self.last_seq = None
        self.last_heard_ms = None
