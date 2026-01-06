import base64
import json
import subprocess
from pathlib import Path
import importlib.util


def test_update_playwright_invokes_gh_api_and_writes_fixed_file(monkeypatch, tmp_path):
    # Prepare a sample workflow content that contains the quoted "on" key
    workflow_yaml = """name: Playwright Example
"on": push
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - run: echo hello
"""

    payload = {"content": base64.b64encode(workflow_yaml.encode("utf-8")).decode("ascii"), "sha": "deadbeef"}

    # Write the expected input file that the script reads
    input_path = Path("/tmp/ari_playwright.json")
    input_path.write_text(json.dumps(payload), encoding="utf-8")

    # Prepare a fake subprocess.run to capture the command invoked
    called = {}

    def fake_run(cmd, check, capture_output, text):
        # Record the command and return a dummy successful CompletedProcess
        called["cmd"] = cmd
        return subprocess.CompletedProcess(cmd, 0, stdout="{\"ok\":true}", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)

    # Import the updated script and run main() with explicit args (use --input and --output)
    spec = importlib.util.spec_from_file_location("update_playwright", "scripts/update_playwright.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # Execute main (should read /tmp/ari_playwright.json and call gh api)
    # Use args to avoid depending on hard-coded paths inside the script
    ret = module.main(["--input", str(input_path), "--output", "/tmp/playwright_fixed.yml", "--dry-run"])
    # In dry-run we expect exit code 0
    assert ret == 0

    # Run again without dry-run to exercise the gh API call path
    ret2 = module.main(["--input", str(input_path), "--output", "/tmp/playwright_fixed.yml", "--retries", "1", "--backoff", "0.01"])  # fast retry settings
    assert ret2 == 0

    # Verify that the output file was written and contains the unquoted key
    out_path = Path("/tmp/playwright_fixed.yml")
    assert out_path.exists(), "Fixed workflow file was not written"
    out_content = out_path.read_text(encoding="utf-8")
    assert 'on:' in out_content
    assert '"on":' not in out_content

    # Verify subprocess.run (gh api) was invoked and includes expected args
    assert "cmd" in called
    cmd = called["cmd"]
    # basic sanity checks
    assert isinstance(cmd, list)
    assert "gh" in cmd[0] or cmd[0].endswith("gh")
    assert "-X" in cmd and "PUT" in cmd
    assert any("branch=chore/ci-pipeline-integrity" in s for s in cmd)
    # Cleanup
    try:
        input_path.unlink()
    except Exception:
        pass
    try:
        out_path.unlink()
    except Exception:
        pass
