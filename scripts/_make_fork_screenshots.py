"""Capture the fork's real Qt status box, menus and tray icons for its READMEs.

Run from the repository root:
    PYTHONPATH=. QT_QPA_PLATFORM=offscreen .venv/bin/python scripts/_make_fork_screenshots.py

Uses an isolated configuration and a synthetic meter/time for reproducible
illustrations. Does not record audio, read user configuration, contact an AI
service, start a hotkey worker, or capture other desktop windows.
"""
from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QApplication

from app import theme
from app.blitztext_linux import BlitztextApp
from app.config import Config
from app.i18n import get_language, set_language
from app.llm_service import LLMService
from app.recording_overlay import RecordingOverlay


def save(widget, path: Path, app: QApplication) -> None:
    widget.ensurePolished()
    widget.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen)
    widget.show()
    app.processEvents()
    if not widget.grab().save(str(path)):
        raise RuntimeError(f"Could not save {path}")
    print(path)


def main() -> None:
    out = Path(__file__).resolve().parents[1] / "docs/screenshots/linux"
    out.mkdir(parents=True, exist_ok=True)
    app = QApplication.instance() or QApplication([])
    app.setQuitOnLastWindowClosed(False)
    theme.apply_theme(app)
    previous_language = get_language()
    colors = {"idle": theme.STATE_IDLE, "recording": theme.STATE_RECORDING,
              "processing": theme.STATE_PROCESSING, "rewriting": theme.STATE_REWRITING,
              "error": theme.STATE_ERROR}
    for state, color in colors.items():
        icon = BlitztextApp._create_microphone_icon(None, QColor(color))
        if not icon.pixmap(128, 128).save(str(out / f"tray-{state}.png")):
            raise RuntimeError(f"Could not save tray-{state}.png")

    try:
        for language in ("en", "de"):
            set_language(language)
            box = RecordingOverlay(SimpleNamespace(current_level=lambda: 0.65))
            box.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen)
            box.start("KEY_RIGHTCTRL", "toggle")
            for state, seconds in (("RECORDING", 7), ("TRANSCRIBING", 9),
                                   ("LLM_REWRITING", 12), ("ERROR", 12)):
                color = colors[{"RECORDING": "recording", "TRANSCRIBING": "processing",
                                "LLM_REWRITING": "rewriting", "ERROR": "error"}[state]]
                icon = BlitztextApp._create_microphone_icon(None, QColor(color))
                if state == "ERROR":
                    box.show_error(icon)
                    box._error_timer.stop()
                else:
                    box.set_status(state, icon)
                with patch("app.recording_overlay.time.monotonic", return_value=100.0 + seconds):
                    box._started = 100.0
                    box._tick()
                # Freeze only the preview; production continues to update normally.
                box._timer.stop()
                save(box, out / f"overlay-{state.lower()}-{language}.png", app)
            box.stop()
            box.close()

            with TemporaryDirectory(prefix="blitztext-readme-") as temporary:
                config = Config(config_dir=Path(temporary))
                config.ui_language = language
                config.transcription_hotkey = "KEY_RIGHTCTRL"
                config.hotkey_mode = "toggle"
                with patch("app.blitztext_linux.Config.load", return_value=config), \
                     patch("app.blitztext_linux.AudioRecorder", return_value=SimpleNamespace()), \
                     patch.object(BlitztextApp, "start_hotkey_worker"), \
                     patch.object(LLMService, "is_available", return_value=True):
                    tray = BlitztextApp(app)
                    save(tray.menu, out / f"tray-menu-{language}.png", app)
                    tray.menu.close()
                    tray.tray_icon.hide()
                    tray.deleteLater()
                    app.processEvents()
    finally:
        set_language(previous_language)


if __name__ == "__main__":
    main()
