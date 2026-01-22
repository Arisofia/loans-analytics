import pytest

from src.api import main as api_main


def test_sanitize_and_resolve_valid(tmp_path):
    allowed = tmp_path / "allowed"
    allowed.mkdir()
    # create a file inside allowed
    file = allowed / "a.csv"
    file.write_text("ok")

    resolved = api_main._sanitize_and_resolve("a.csv", allowed)
    assert resolved == file.resolve()


def test_sanitize_and_resolve_rejects_absolute(tmp_path):
    allowed = tmp_path / "allowed"
    allowed.mkdir()
    with pytest.raises(ValueError):
        api_main._sanitize_and_resolve("/etc/passwd", allowed)


def test_sanitize_and_resolve_rejects_parent_traversal(tmp_path):
    allowed = tmp_path / "allowed"
    allowed.mkdir()
    with pytest.raises(ValueError):
        api_main._sanitize_and_resolve("../secrets.txt", allowed)


def test_sanitize_and_resolve_outside(tmp_path):
    allowed = tmp_path / "allowed"
    allowed.mkdir()
    # Make candidate that attempts to escape via symlink or similar
    outside = tmp_path / "outside"
    outside.mkdir()
    # Attempt to point to sibling from inside allowed
    with pytest.raises(ValueError):
        api_main._sanitize_and_resolve("../outside/a.txt", allowed)
