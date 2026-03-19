import pytest

from backend.src.utils.config_loader import load_config


def test_load_config_empty_yaml_fails_fast(tmp_path):
    config_path = tmp_path / "config.yml"
    config_path.write_text("", encoding="utf-8")

    with pytest.raises(ValueError, match="empty"):
        load_config(str(config_path))


def test_load_config_non_mapping_yaml_fails_fast(tmp_path):
    config_path = tmp_path / "config.yml"
    config_path.write_text("- item1\n- item2\n", encoding="utf-8")

    with pytest.raises(ValueError, match="must be a mapping"):
        load_config(str(config_path))


def test_load_config_malformed_yaml_fails_fast(tmp_path):
    config_path = tmp_path / "config.yml"
    config_path.write_text("supabase: [unclosed\n", encoding="utf-8")

    with pytest.raises(ValueError, match="malformed"):
        load_config(str(config_path))


def test_load_config_valid_mapping_without_optional_sections(tmp_path):
    config_path = tmp_path / "config.yml"
    config_path.write_text("feature_flags:\n  enabled: true\n", encoding="utf-8")

    loaded = load_config(str(config_path))

    assert loaded["feature_flags"]["enabled"] is True
