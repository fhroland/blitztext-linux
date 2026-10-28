"""Persistence, real PCM metering, overlay lifecycle and AI reachability failures."""
import struct
import wave
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from app.config import Config
from app.workflows import WorkflowType


@pytest.fixture
def qapp():
    from PyQt6.QtWidgets import QApplication
    return QApplication.instance() or QApplication([])


def test_workflow_survives_restart_and_invalid_value_defaults(tmp_path):
    config = Config(config_dir=tmp_path)
    config.preferred_workflow = "emoji_text"
    config.save()
    restored = Config(config_dir=tmp_path)
    assert restored.preferred_workflow == "emoji_text"
    restored._data["preferred_workflow"] = "bad"
    assert restored.preferred_workflow == "transcription"


def test_window_restores_ai_and_only_user_changes_are_saved(qapp, tmp_path):
    from app.main_window import MainWindow
    from tests.test_main_window_widget import _Controller
    ctrl = _Controller()
    ctrl.config = Config(config_dir=tmp_path)
    ctrl.config.preferred_workflow = "emoji_text"
    ctrl.main_window_workflow_changed = MagicMock()
    window = MainWindow(ctrl)
    assert window._selected_workflow() == WorkflowType.EMOJI_TEXT
    assert window._seg_ai.isChecked()
    ctrl.main_window_workflow_changed.assert_not_called()
    window.update_state("RECORDING", WorkflowType.LOCAL, None)
    ctrl.main_window_workflow_changed.assert_not_called()
    window._set_ai_mode(True)
    ctrl.main_window_workflow_changed.assert_called_once_with(WorkflowType.EMOJI_TEXT)
    window.close()


@pytest.mark.parametrize("sample,expected", [(0, 0), (3276, 2/3), (32767, 1)])
def test_meter_reads_real_pcm_from_wav(tmp_path, sample, expected):
    from app.audio_recorder import AudioRecorder
    recorder = AudioRecorder(tmp_path)
    try:
        with wave.open(str(recorder._wav_file), "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(16000)
            wav.writeframes(struct.pack("<h", sample) * 1600)
        recorder._process = object()  # Meter uses no process control.
        assert recorder.current_level() == pytest.approx(expected, abs=0.01)
    finally:
        recorder._process = None
        recorder._finish_job()


def test_meter_ignores_missing_or_unwritten_audio(tmp_path):
    from app.audio_recorder import AudioRecorder
    recorder = AudioRecorder(tmp_path)
    try:
        recorder._process = object()
        assert recorder.current_level() == 0
        recorder._wav_file.write_bytes(b"RIFF")
        assert recorder.current_level() == 0
    finally:
        recorder._process = None
        recorder._finish_job()


def test_overlay_shows_level_and_hides_without_focus(qapp):
    from PyQt6.QtCore import Qt
    from app.recording_overlay import RecordingOverlay
    overlay = RecordingOverlay(SimpleNamespace(current_level=lambda: 0.73))
    overlay.start("KEY_RIGHTCTRL", "toggle")
    overlay._tick()
    assert overlay.isVisible()
    assert overlay.level.value() == 73
    assert "Ctrl" in overlay.hint.text()
    assert overlay.windowFlags() & Qt.WindowType.WindowDoesNotAcceptFocus
    assert overlay.windowType() == Qt.WindowType.Window
    assert overlay.parentWidget() is None
    assert overlay.testAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
    overlay.stop()
    assert not overlay.isVisible()
    assert not overlay._timer.isActive()


@pytest.mark.parametrize("main_state", ["absent", "hidden", "minimized", "closed"])
def test_recording_overlay_lifecycle_without_visible_main_window(qapp, main_state):
    from PyQt6.QtGui import QIcon
    from PyQt6.QtWidgets import QWidget
    from app.blitztext_linux import BlitztextApp

    window = None if main_state == "absent" else QWidget()
    if window is not None:
        window.update_state = MagicMock()
        window.show()
        if main_state == "hidden":
            window.hide()
        elif main_state == "minimized":
            window.showMinimized()
        else:
            window.close()
    app = SimpleNamespace(
        state="RECORDING", _main_window=window, _recording_overlay=None,
        audio_recorder=SimpleNamespace(current_level=lambda: 0.73),
        config=SimpleNamespace(transcription_hotkey="KEY_RIGHTCTRL", hotkey_mode="toggle"),
        current_workflow=WorkflowType.LOCAL, _tray_error_message=None,
        update_tray_state=MagicMock(),
        tray_icon=SimpleNamespace(icon=QIcon),
    )
    try:
        BlitztextApp._on_state_changed(app)
        overlay = app._recording_overlay
        assert overlay.isVisible()
        assert overlay.parentWidget() is None
        for state in ("TRANSCRIBING", "LLM_REWRITING"):
            app.state = state
            BlitztextApp._on_state_changed(app)
            assert overlay.isVisible()
            assert overlay._timer.isActive()
            assert not overlay.level.isVisible()
            assert overlay.processing.isVisible()
        app.state = "IDLE"
        BlitztextApp._on_state_changed(app)
        assert not overlay.isVisible()
        assert not overlay._timer.isActive()
        app.state = "RECORDING"
        BlitztextApp._on_state_changed(app)
        assert overlay.isVisible()
    finally:
        if app._recording_overlay is not None:
            app._recording_overlay.stop()
            app._recording_overlay.close()
        if window is not None:
            window.close()


def test_processing_keeps_time_and_uses_actual_tray_icons(qapp):
    from PyQt6.QtGui import QColor
    from app import theme
    from app.blitztext_linux import BlitztextApp
    from app.recording_overlay import RecordingOverlay
    from app.i18n import t

    recorder = SimpleNamespace(current_level=MagicMock(return_value=0.73))
    overlay = RecordingOverlay(recorder)
    try:
        with patch("app.recording_overlay.time.monotonic", return_value=100):
            overlay.start("KEY_RIGHTCTRL", "toggle")
        for state, color, message, now in (
            ("RECORDING", theme.STATE_RECORDING, None, 103),
            ("TRANSCRIBING", theme.STATE_PROCESSING, "mainwindow.status.transcribing", 106),
            ("LLM_REWRITING", theme.STATE_REWRITING, "mainwindow.status.processing", 112),
        ):
            icon = BlitztextApp._create_microphone_icon(None, QColor(color))
            recorder.current_level.reset_mock()
            with patch("app.recording_overlay.time.monotonic", return_value=now):
                overlay.set_status(state, icon)
                overlay._tick()
            assert overlay.icon.pixmap().toImage() == icon.pixmap(24, 24).toImage()
            assert overlay.elapsed.text() == f"00:{now - 100:02}"
            if message:
                assert overlay.processing.text() == t(message)
                recorder.current_level.assert_not_called()
            else:
                assert overlay.level.value() == 73
                recorder.current_level.assert_called_once()
        overlay.stop()
        with patch("app.recording_overlay.time.monotonic", return_value=150):
            overlay.start("KEY_RIGHTCTRL", "toggle")
        assert overlay.elapsed.text() == "00:00"
        assert overlay.level.isVisible()
        assert not overlay.processing.isVisible()
    finally:
        overlay.stop()
        overlay.close()


@pytest.mark.parametrize("available,reachable", [(True, True), (True, False), (False, False)])
def test_ai_probe_reports_failure_without_sending_text(available, reachable):
    from app.blitztext_linux import BlitztextApp
    service = MagicMock()
    service.is_available.return_value = available
    if not reachable:
        service.client.with_options.return_value.models.list.side_effect = OSError("offline")
    app = SimpleNamespace(config=SimpleNamespace(preferred_workflow="text_improver"),
                          llm_service=service, ai_probe_finished=MagicMock())
    def thread(**kwargs):
        return SimpleNamespace(start=kwargs["target"])
    with patch("threading.Thread", side_effect=thread):
        BlitztextApp._check_restored_ai_mode(app)
    app.ai_probe_finished.emit.assert_called_once_with(available and reachable)
    service.client.chat.completions.create.assert_not_called()


def test_dictation_hotkey_uses_saved_workflow():
    from app.blitztext_linux import BlitztextApp
    app = SimpleNamespace(config=SimpleNamespace(preferred_workflow="text_improver"),
                          _on_workflow_triggered=MagicMock())
    BlitztextApp._on_hotkey_workflow_triggered(app, WorkflowType.TRANSCRIPTION)
    app._on_workflow_triggered.assert_called_once_with(WorkflowType.TEXT_IMPROVER)


def test_ctrl_names_distinguish_sides_in_both_languages():
    from app.hotkey_service import hotkey_display_name
    from app.i18n import get_language, set_language
    previous = get_language()
    try:
        set_language("de")
        assert hotkey_display_name("KEY_RIGHTCTRL") == "Rechte Ctrl"
        assert hotkey_display_name("KEY_LEFTCTRL") == "Linke Ctrl"
        set_language("en")
        assert hotkey_display_name("KEY_RIGHTCTRL") == "Right Ctrl"
    finally:
        set_language(previous)
