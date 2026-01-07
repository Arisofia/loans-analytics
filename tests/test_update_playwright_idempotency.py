import importlib.util


def _load_module():
    spec = importlib.util.spec_from_file_location("update_playwright", "scripts/update_playwright.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_safe_replace_on_key_is_idempotent():
    module = _load_module()
    content = 'name: Example\n"on": push\njobs:\n  - name: t\n'

    new1, n1 = module.safe_replace_on_key(content)
    new2, n2 = module.safe_replace_on_key(new1)

    # first run should perform the replacement, second should not
    assert n1 == 1
    assert n2 == 0
    assert new1 == new2


def test_fix_content_returns_replacements_count():
    module = _load_module()
    content_b64 = module.base64.b64encode('name: Example\n"on": push\n'.encode('utf-8')).decode('ascii')

    new, n = module.fix_content(content_b64)
    assert n == 1
    assert 'on:' in new
