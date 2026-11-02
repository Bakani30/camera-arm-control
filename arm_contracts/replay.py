"""Replay files (contract section 7): a header line, then messages of one kind."""
import json
from datetime import datetime, timezone
from pathlib import Path

from arm_contracts.messages import KINDS, MAJOR, MINOR, ContractError, Receiver, load_line, parse_contract_tag, to_line

HEADER_KIND = 'replay_header'
HEADER_FIELDS = ('created', 'kind', 'camera', 'notes')


def _header_line(kind, camera, notes, created):
    if kind not in KINDS:
        raise ContractError(f'unknown message kind {kind!r}')
    header = dict(contract=f'{HEADER_KIND}/{MAJOR}.{MINOR}', created=created or datetime.now(timezone.utc).isoformat(),
                  kind=kind, camera=camera, notes=notes)
    return json.dumps(header, allow_nan=False, separators=(',', ':'))


def _checked(receiver, message):
    got = receiver.receive(message, 0.0)              # refuse here what read_replay would refuse later
    if got.problem:
        raise ContractError(got.problem)
    return message


def write_replay(path, kind, messages, camera=None, notes='', created=None):
    header = _header_line(kind, camera, notes, created)
    messages = list(messages)
    if not messages:
        raise ContractError('a replay file needs at least one message')
    receiver = Receiver(KINDS[kind], None)
    lines = [header] + [to_line(_checked(receiver, m)) for m in messages]
    with Path(path).open('w', encoding='utf-8', newline='\n') as file:
        file.write('\n'.join(lines) + '\n')


class ReplayWriter:
    """A replay file written line by line, so a run that crashes keeps every message it sent."""

    def __init__(self, path, kind, camera=None, notes='', created=None):
        header = _header_line(kind, camera, notes, created)
        self.receiver = Receiver(KINDS[kind], None)
        self.file = Path(path).open('w', encoding='utf-8', newline='\n')
        self._line(header)

    def _line(self, line):
        self.file.write(line + '\n')
        self.file.flush()

    def write(self, message):
        self._line(to_line(_checked(self.receiver, message)))

    def close(self):
        self.file.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()


def _read_header(line):
    header = load_line(line)
    tag_kind, _ = parse_contract_tag(header.get('contract'))
    if tag_kind != HEADER_KIND:
        raise ContractError(f'first line must be a {HEADER_KIND}, got {tag_kind}')
    missing = [name for name in HEADER_FIELDS if name not in header]
    if missing:
        raise ContractError(f'{HEADER_KIND}: missing {missing}')
    if not isinstance(header['kind'], str) or header['kind'] not in KINDS:
        raise ContractError(f"unknown message kind {header['kind']!r}")
    return header


def read_replay(path):
    """(header, messages). Any broken line raises ContractError naming path:line."""
    lines = Path(path).read_text(encoding='utf-8-sig').splitlines()
    if not lines:
        raise ContractError(f'{path}:1: empty file, expected a {HEADER_KIND}')
    try:
        header = _read_header(lines[0])
    except ContractError as error:
        raise ContractError(f'{path}:1: {error}') from error
    receiver = Receiver(KINDS[header['kind']], None)  # a file moves nothing; check_profile is the player's job
    messages = []
    for number, line in enumerate(lines[1:], start=2):
        got = receiver.receive(line, 0.0)  # now_ms only drives stop, which a file reader ignores
        if got.problem:
            raise ContractError(f'{path}:{number}: {got.problem}')
        messages.append(got.message)
    return header, messages
