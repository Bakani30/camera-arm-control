"""Connects the relative mapper to contract messages, the mock arm and a replay file."""
from arm_contracts.messages import EndEffectorTarget
from arm_contracts.scripted import ROBOT_ID

from .mapping import MappingConfig, RelativeMapper


def _target(output, now_ms, seq, source):
    return EndEffectorTarget(t_ms=now_ms, seq=seq, robot_id=ROBOT_ID, grip=output.grip, mode=output.mode,
                             position_m=tuple(round(v, 6) for v in output.position_m),
                             enabled=output.enabled, source=source)


class MappingSession:
    def __init__(self, arm, writer=None, config=MappingConfig(), source='live'):
        self.arm = arm
        self.writer = writer
        self.source = source
        self.mapper = RelativeMapper(config)
        self.seq = 0
        self.reset_pending = False
        self.reanchor_pending = False
        self.fields = {}

    def reset(self):
        self.mapper.reset()
        self.reset_pending = True

    def reanchor(self):
        self.mapper.reanchor()
        self.reanchor_pending = True

    def step(self, control, metric, code, now_ms):
        output = self.mapper.update(control.armed, metric.position_m, metric.z_m, metric.active, code, now_ms)
        self.seq += 1
        message = _target(output, now_ms, self.seq, self.source)
        self.arm.receive(message, now_ms)
        if self.writer is not None:
            self.writer.write(message)
        self.fields = dict(armed=control.armed, mapping_reset=self.reset_pending,
                           mapping_reanchor=self.reanchor_pending,
                           mapping_position_m=message.position_m, mapping_mode=message.mode,
                           mapping_enabled=message.enabled, mapping_grip=message.grip)
        self.reset_pending = self.reanchor_pending = False
        return message

    def log_fields(self):
        """What a frame log needs, beside the metric_* fields, to recompute this frame."""
        return self.fields


def targets_from_records(records, config=MappingConfig()):
    """Recompute the targets of a frame log. They are marked script: nothing here saw a camera."""
    mapper = RelativeMapper(config)
    targets = []
    for seq, r in enumerate(records, start=1):
        if r['mapping_reset']:
            mapper.reset()
        if r['mapping_reanchor']:
            mapper.reanchor()
        output = mapper.update(r['armed'], r['metric_position_m'], r['metric_z_m'], r['metric_active'],
                               r['output'], r['receipt_ms'])
        targets.append(_target(output, r['receipt_ms'], seq, 'script'))
    return targets
