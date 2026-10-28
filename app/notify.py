"""Desktop notifications for BlitztextLinux.

Notifications never fail hard. If notify-send is unavailable, the message is
silently skipped.
"""
from __future__ import annotations

import logging
from html import escape
import shutil
import subprocess

logger = logging.getLogger("blitztext.notify")

_NOTIFY_TIMEOUT = 5.0


def notify(
    title: str,
    body: str,
    urgency: str = "normal",
    icon: str = "audio-input-microphone",
) -> bool:
    """Send a native notification; return success without raising on OS errors."""
    if shutil.which("notify-send") is None:
        logger.debug("notify-send nicht gefunden -- Benachrichtigung uebersprungen.")
        return False
    try:
        result = subprocess.run(
            ["notify-send", "--app-name=Blitztext", "-u", urgency, "-i", icon,
             "--", title, escape(body)],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=_NOTIFY_TIMEOUT,
        )
        return result.returncode == 0
    except (FileNotFoundError, OSError, subprocess.TimeoutExpired):
        return False


def is_available() -> bool:
    return shutil.which("notify-send") is not None
