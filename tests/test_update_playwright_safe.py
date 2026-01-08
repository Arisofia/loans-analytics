import importlib.util


def _load_module():
    spec = importlib.util.spec_from_file_location("update_playwright", "scripts/update_playwright.py")
    if spec is None or spec.loader is None:
        raise ImportError("Could not load spec for update_playwright")
    module = importlib.util.module_from_spec(spec)
    # spec.loader is checked above; type check ignore for dynamically loaded module
    spec.loader.exec_module(module)  # type: ignore[attr-defined]
    return module


def test_safe_replace_on_key_replaces_top_level_key():
    module = _load_module()
    content = 'name: Example\n  "on": push\njobs:\n  - name: t\n'

    new, n = module.safe_replace_on_key(content)

    assert n == 1
    assert 'on:' in new
    assert '"on":' not in new


def test_safe_replace_on_key_ignores_values_and_strings():
    module = _load_module()
    # appearance inside a value or an inline string should NOT be replaced
    content = 'jobs:\n  test:\n    steps:\n      - run: echo "test \"on\": value"\n'

    new, n = module.safe_replace_on_key(content)

    assert n == 0
    assert '"on":' in content
    assert '"on":' in new
