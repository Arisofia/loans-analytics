import base64
import json
import re
import subprocess
import importlib.util


def _load_module():
    spec = importlib.util.spec_from_file_location("update_playwright", "scripts/update_playwright.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_integration_replaces_only_top_level_key_and_invokes_gh(monkeypatch, tmp_path):
    module = _load_module()

    workflow_yaml = """name: Playwright Example
"on": push
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - run: |
          echo 'this string contains "on": value and should remain quoted'
      - run: echo hello
"""

    payload = {"content": base64.b64encode(workflow_yaml.encode("utf-8")).decode("ascii"), "sha": "deadbeef"}

    input_path = tmp_path / "ari_playwright.json"
    input_path.write_text(json.dumps(payload), encoding="utf-8")

    out_path = tmp_path / "playwright_fixed.yml"

    called = {}

    def fake_run(cmd, check, capture_output, text):
        called["cmd"] = cmd
        return subprocess.CompletedProcess(cmd, 0, stdout='{"ok":true}', stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)

    ret = module.main(["--input", str(input_path), "--output", str(out_path), "--retries", "1", "--backoff", "0.01"])
    assert ret == 0

    assert out_path.exists()
    out_content = out_path.read_text(encoding="utf-8")

    # Ensure top-level quoted key was unquoted exactly once
    assert len(re.findall(r'(?m)^[ \t]*on\s*:', out_content)) == 1

    # Ensure quoted appearances inside run blocks were preserved
    assert '"on": value' in out_content

    # Ensure gh API was invoked
    assert "cmd" in called
    cmd = called["cmd"]
    assert isinstance(cmd, list)


def test_integration_no_top_level_change_does_not_call_gh(monkeypatch, tmp_path):
    module = _load_module()

    # Only contains quoted "on" inside a run string (no top-level key)
    workflow_yaml = """name: Playwright Example
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - run: echo 'this contains "on": in a string and should not trigger an update'
"""

    payload = {"content": base64.b64encode(workflow_yaml.encode("utf-8")).decode("ascii"), "sha": "deadbeef"}

    input_path = tmp_path / "ari_playwright.json"
    input_path.write_text(json.dumps(payload), encoding="utf-8")

    out_path = tmp_path / "playwright_fixed.yml"

    def fail_if_called(*args, **kwargs):
        raise AssertionError("gh api should not be called when there are no top-level replacements")

    monkeypatch.setattr(subprocess, "run", fail_if_called)

    ret = module.main(["--input", str(input_path), "--output", str(out_path)])
    assert ret == 0

    # Output file should be written and should still contain the quoted occurrence
    assert out_path.exists()
    out_content = out_path.read_text(encoding="utf-8")
    assert '"on":' in out_content
