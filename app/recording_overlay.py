"""Non-activating recording indicator with the actual microphone level."""
from __future__ import annotations

import time
import os
import shutil

from PyQt6.QtCore import Qt, QTimer, QProcess
from PyQt6.QtWidgets import QApplication, QHBoxLayout, QLabel, QProgressBar, QVBoxLayout, QWidget

from app.hotkey_service import hotkey_display_name
from app.i18n import t
from app import theme


class RecordingOverlay(QWidget):
    def __init__(self, recorder, parent=None):
        super().__init__(parent)
        self._recorder = recorder
        self._started = 0.0
        self._state = "IDLE"
        # A Tool window can be suppressed by the compositor when the app's
        # normal windows are hidden/minimized (the usual tray-only operation).
        # Keep the indicator independent and visible without activating it.
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint |
                            Qt.WindowType.WindowStaysOnTopHint |
                            Qt.WindowType.WindowDoesNotAcceptFocus |
                            Qt.WindowType.WindowTransparentForInput)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        # Exact title also scopes the local KWin "acceptfocus=false" rule:
        # Wayland/KWin otherwise activates a new top-level despite Qt's flags.
        self.setWindowTitle("Blitztext recording indicator")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground)
        self._positioner = QProcess(self)
        self.setFixedSize(250, 108)
        self.setObjectName("recordingOverlay")
        self.setStyleSheet('''
            QWidget#recordingOverlay { background: #202327; border: 1px solid #56534a;
                                       border-radius: 12px; }
            QLabel { color: #f2f1ed; background: transparent; border: none; }
            QLabel#activeTitle { font-size: 14px; font-weight: 600; }
            QLabel#stopHint { color: #bab8b1; font-size: 11px; }
            QLabel#processingStatus { font-size: 12px; }
            QProgressBar { border: none; background: #3b4047; border-radius: 4px; }
            QProgressBar::chunk { background: #e6c878; border-radius: 4px; }
        ''')
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(5)
        header = QHBoxLayout()
        header.setSpacing(7)
        self.icon = QLabel()
        self.icon.setFixedSize(24, 24)
        header.addWidget(self.icon)
        self.title = QLabel(t("overlay.recording"))
        self.title.setObjectName("activeTitle")
        header.addWidget(self.title, 1)
        self.elapsed = QLabel("00:00")
        self.elapsed.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.addWidget(self.elapsed)
        layout.addLayout(header)
        activity = QWidget()
        activity.setFixedHeight(20)
        activity_layout = QVBoxLayout(activity)
        activity_layout.setContentsMargins(0, 0, 0, 0)
        self.level = QProgressBar()
        self.level.setRange(0, 100)
        self.level.setTextVisible(False)
        self.level.setFixedHeight(6)
        activity_layout.addWidget(self.level)
        self.processing = QLabel()
        self.processing.setObjectName("processingStatus")
        self.processing.setAlignment(Qt.AlignmentFlag.AlignCenter)
        activity_layout.addWidget(self.processing)
        self.processing.hide()
        layout.addWidget(activity)
        self.hint = QLabel()
        self.hint.setObjectName("stopHint")
        self.hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.hint)
        self._timer = QTimer(self)
        self._timer.setInterval(80)
        self._timer.timeout.connect(self._tick)
        self._error_timer = QTimer(self)
        self._error_timer.setSingleShot(True)
        self._error_timer.setInterval(4000)
        self._error_timer.timeout.connect(self.stop)

    def start(self, key: str, mode: str) -> None:
        if self._state == "RECORDING" and self.isVisible():
            return
        self._error_timer.stop()
        self._started = time.monotonic()
        self._state = "RECORDING"
        self.title.setText(t("overlay.recording"))
        self.title.setStyleSheet(f"color: {theme.STATE_RECORDING};")
        self.processing.hide()
        self.level.show()
        self.hint.setText(t("overlay.release" if mode == "hold" else "overlay.stop").format(
            key=hotkey_display_name(key)))
        self.level.setValue(0)
        self.elapsed.setText("00:00")
        self._show_indicator()

    def set_status(self, state: str, icon) -> None:
        """Keep the recording indicator open until the whole workflow finishes."""
        self._error_timer.stop()
        self._state = state
        self.set_tray_icon(icon)
        if state in ("TRANSCRIBING", "LLM_REWRITING"):
            self.title.setText(t("overlay.processing"))
            color = theme.STATE_REWRITING if state == "LLM_REWRITING" else theme.STATE_PROCESSING
            self.title.setStyleSheet(f"color: {color};")
            self.level.hide()
            self.processing.setText(t("mainwindow.status.transcribing" if state == "TRANSCRIBING"
                                      else "mainwindow.status.processing"))
            self.processing.show()
            self.hint.setText(t("overlay.wait"))
            if not self.isVisible():
                self._started = time.monotonic()
                self.elapsed.setText("00:00")
                self._show_indicator()

    def show_error(self, icon) -> None:
        """Keep the failed workflow visible briefly; the tray retains the error."""
        self.set_tray_icon(icon)
        if self._state == "ERROR":
            return
        self._state = "ERROR"
        self._timer.stop()
        self.title.setText(t("overlay.error"))
        self.title.setStyleSheet(f"color: {theme.STATE_ERROR};")
        self.level.hide()
        self.processing.setText(t("overlay.failed"))
        self.processing.show()
        self.hint.setText(t("overlay.error_hint"))
        self._error_timer.start()

    def set_tray_icon(self, icon) -> None:
        self.icon.setPixmap(icon.pixmap(24, 24))

    def _show_indicator(self) -> None:
        screen = QApplication.primaryScreen()
        if screen is not None:
            area = screen.availableGeometry()
            self.move(area.center() - self.rect().center())
        self.show()
        if QApplication.platformName() == "wayland" and shutil.which("kdotool"):
            # Wayland ignores move() for ordinary top-level windows. Ask KWin
            # to position only this process's indicator and keep it above other
            # windows. KWin/Wayland may ignore Qt's WindowStaysOnTopHint.
            # Set the compositor state explicitly without activating the box.
            QTimer.singleShot(120, self._center_on_kde)
        self._timer.start()

    def _center_on_kde(self) -> None:
        screen = QApplication.primaryScreen()
        if not self.isVisible() or screen is None:
            return
        point = screen.availableGeometry().center() - self.rect().center()
        self._positioner.start("kdotool", [
            "search", "--all", "--pid", str(os.getpid()), "--title",
            "^Blitztext recording indicator$",
            "windowstate", "--add", "ABOVE", "--remove", "BELOW",
            "windowmove", str(point.x()), str(point.y()),
        ])
        QTimer.singleShot(1500, self._positioner.kill)

    def stop(self) -> None:
        self._error_timer.stop()
        self._state = "IDLE"
        self._timer.stop()
        self.hide()
        self.level.setValue(0)

    def _tick(self) -> None:
        seconds = int(time.monotonic() - self._started)
        self.elapsed.setText(f"{seconds // 60:02d}:{seconds % 60:02d}")
        if self._state == "RECORDING":
            self.level.setValue(round(self._recorder.current_level() * 100))
