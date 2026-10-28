"""Exercise real evdev worker event handling without touching input devices."""
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from app.hotkey_service import HotkeyWorker
from app.workflows import WorkflowType


def run_events(events, mode="toggle", key="KEY_RIGHTCTRL", split=False):
    ec = pytest.importorskip("evdev").ecodes
    worker = HotkeyWorker(hotkey_mode=mode, transcription_key=key)
    emitted = []
    stopped = []
    worker.workflow_triggered.connect(emitted.append)
    worker.recording_stop.connect(lambda: stopped.append(True))
    snapshots = []
    batches = [[event] for event in events] if split else [events]
    device = MagicMock(fd=10, path="/dev/input/fake")
    device.read.side_effect = [
        [SimpleNamespace(type=ec.EV_KEY, code=getattr(ec, code), value=value)
         for code, value in batch] for batch in batches
    ]
    calls = 0

    def select_events(*args):
        nonlocal calls
        snapshots.append(list(emitted))
        calls += 1
        if calls > len(batches):
            worker.stop()
            return [], [], []
        return [10], [], []

    with patch("app.hotkey_service._discover_keyboards", return_value=[device]), \
         patch("select.select", side_effect=select_events):
        worker.run()
    return emitted, stopped, snapshots


@pytest.mark.parametrize("split", [False, True])
@pytest.mark.parametrize("events", [
    [("KEY_RIGHTCTRL", 1), ("KEY_X", 1), ("KEY_X", 0), ("KEY_RIGHTCTRL", 0)],
    [("KEY_RIGHTCTRL", 1), ("KEY_X", 1), ("KEY_RIGHTCTRL", 0), ("KEY_X", 0)],
    [("KEY_X", 1), ("KEY_RIGHTCTRL", 1), ("KEY_X", 0), ("KEY_RIGHTCTRL", 0)],
    [("KEY_LEFTSHIFT", 1), ("KEY_RIGHTCTRL", 1), ("KEY_LEFTSHIFT", 0), ("KEY_RIGHTCTRL", 0)],
    [("KEY_RIGHTCTRL", 1), ("KEY_LEFTSHIFT", 1), ("KEY_LEFTSHIFT", 0), ("KEY_RIGHTCTRL", 0)],
    [("KEY_RIGHTCTRL", 0)],  # No observed press (e.g. service restarted).
])
def test_combinations_never_toggle(events, split):
    emitted, stopped, _ = run_events(events, split=split)
    assert emitted == []
    assert stopped == []


def test_standalone_ctrl_triggers_only_on_release_even_with_repeat():
    emitted, stopped, snapshots = run_events([
        ("KEY_RIGHTCTRL", 1), ("KEY_RIGHTCTRL", 2), ("KEY_RIGHTCTRL", 0),
    ], split=True)
    assert snapshots[:3] == [[], [], []]
    assert emitted == [WorkflowType.TRANSCRIPTION]
    assert stopped == []


def test_cancelled_combination_does_not_block_next_standalone_press():
    emitted, _, _ = run_events([
        ("KEY_RIGHTCTRL", 1), ("KEY_X", 1), ("KEY_X", 0), ("KEY_RIGHTCTRL", 0),
        ("KEY_RIGHTCTRL", 1), ("KEY_RIGHTCTRL", 0),
    ])
    assert emitted == [WorkflowType.TRANSCRIPTION]


def test_hold_mode_still_starts_on_press():
    emitted, _, snapshots = run_events([
        ("KEY_RIGHTCTRL", 1), ("KEY_RIGHTCTRL", 0),
    ], mode="hold", split=True)
    assert snapshots[1] == [WorkflowType.TRANSCRIPTION]
    assert emitted == [WorkflowType.TRANSCRIPTION]


def test_pause_still_starts_on_press():
    emitted, _, snapshots = run_events([
        ("KEY_PAUSE", 1), ("KEY_PAUSE", 0),
    ], key="KEY_PAUSE", split=True)
    assert snapshots[1] == [WorkflowType.TRANSCRIPTION]
    assert emitted == [WorkflowType.TRANSCRIPTION]


@pytest.mark.parametrize("meta,shift", [
    ("KEY_LEFTMETA", "KEY_LEFTSHIFT"), ("KEY_RIGHTMETA", "KEY_RIGHTSHIFT"),
])
@pytest.mark.parametrize("key,expected", [
    ("KEY_D", WorkflowType.LOCAL),
    ("KEY_V", WorkflowType.TEXT_IMPROVER),
    ("KEY_S", WorkflowType.DAMPF_ABLASSEN),
    ("KEY_E", WorkflowType.EMOJI_TEXT),
    ("KEY_H", None), ("KEY_T", None),
])
def test_workflow_shortcuts_dvse(meta, shift, key, expected):
    emitted, _, _ = run_events([
        (meta, 1), (shift, 1), (key, 1),
        (key, 0), (shift, 0), (meta, 0),
    ])
    assert emitted == ([] if expected is None else [expected])
