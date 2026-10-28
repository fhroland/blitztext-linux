"""Protect this locally customized installation from release replacement."""
from __future__ import annotations

import os
from pathlib import Path

DISABLE_MARKER = Path(__file__).resolve().parent.parent / '.updates-disabled'


def updates_disabled() -> bool:
    return os.environ.get('BLITZTEXT_DISABLE_UPDATES') == '1' or DISABLE_MARKER.exists()
