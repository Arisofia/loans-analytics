import stat

from pipeline.ingestion import UnifiedIngestion


def test_archive_failure_records_error(tmp_path):
    ui = UnifiedIngestion({"pipeline": {"phases": {"ingestion": {}}}})
    src = tmp_path / "data.csv"
    src.write_text("loan_id,total_receivable_usd\n1,100\n")
    archive_dir = tmp_path / "arch"
    archive_dir.mkdir()
    # make archive dir read-only to cause copy failure
    archive_dir.chmod(stat.S_IREAD)

    archived = ui._archive_raw(src, archive_dir)
    assert archived is None
    # errors recorded
    assert any(e.get("stage") == "archive" for e in ui.errors)

    # restore permissions for cleanup
    archive_dir.chmod(stat.S_IWRITE | stat.S_IREAD)
