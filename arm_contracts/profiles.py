"""Arm profiles that the contract code checks joint names against."""
from arm_contracts.messages import ArmProfile
from arm_spec import load_spec


def small_arm_profile(spec=None):
    """The real small arm from arm_spec. The gripper is left out: it travels in the grip field."""
    spec = spec or load_spec()
    version = spec.raw['spec']
    return ArmProfile(version.split('/')[0], version, tuple(j.name for j in spec.joints if j.name != 'gripper'))
