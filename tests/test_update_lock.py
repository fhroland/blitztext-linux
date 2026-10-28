"""The customized installation cannot check, download or install releases."""
from unittest.mock import MagicMock

import pytest

from app import update_policy
from app.update_service import Release, UpdateError, UpdateService


@pytest.fixture
def lock(tmp_path, monkeypatch):
    marker = tmp_path / '.updates-disabled'
    marker.write_text('Preserve local changes\n')
    monkeypatch.setattr(update_policy, 'DISABLE_MARKER', marker)
    monkeypatch.delenv('BLITZTEXT_DISABLE_UPDATES', raising=False)
    monkeypatch.setenv('XDG_DATA_HOME', str(tmp_path / 'data'))
    return marker


def test_marker_wins_even_when_environment_flag_is_zero(lock, monkeypatch):
    monkeypatch.setenv('BLITZTEXT_DISABLE_UPDATES', '0')
    assert update_policy.updates_disabled()


def test_launcher_environment_alone_blocks_updates(lock, monkeypatch):
    lock.unlink()
    monkeypatch.setenv('BLITZTEXT_DISABLE_UPDATES', '1')
    assert update_policy.updates_disabled()


def test_blocked_service_never_fetches_or_creates_release_directory(lock, monkeypatch):
    service = UpdateService()
    fetch = MagicMock()
    monkeypatch.setattr(service, '_fetch', fetch)
    with pytest.raises(UpdateError, match='disabled'):
        service.check_for_update('1.0.0')
    with pytest.raises(UpdateError, match='disabled'):
        service.install_release(Release('2.0.0', 'unused', 'a' * 64))
    fetch.assert_not_called()
    assert not service.releases_dir.exists()


def test_direct_fetch_is_also_blocked(lock, monkeypatch):
    opener = MagicMock()
    monkeypatch.setattr('app.update_service.urllib.request.build_opener', opener)
    with pytest.raises(UpdateError, match='disabled'):
        UpdateService()._fetch('https://api.github.com/repos/TimInTech/blitztext-linux/releases/latest', 100)
    opener.assert_not_called()


def test_ui_and_direct_controller_calls_cannot_update(lock):
    from PyQt6.QtWidgets import QApplication
    from app.update_widget import UpdateWidget
    qapp = QApplication.instance() or QApplication([])
    service = MagicMock()
    widget = UpdateWidget(service=service)
    assert not widget.check_button.isEnabled()
    assert not widget.install_button.isEnabled()
    assert widget.status_label.text()
    widget._controller.release = Release('2.0.0', 'unused', 'a' * 64)
    widget._controller.check()
    widget._controller.install()
    assert widget._job is None
    service.check_for_update.assert_not_called()
    service.install_release.assert_not_called()
    widget.close()
