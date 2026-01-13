Supported Python versions

- Recommended: Python 3.11, 3.12
- Not recommended for running tests: Python 3.14 (known typing/pytest compatibility issues)

Testing

- Use `requirements-dev.txt` to install test dependencies: `pip install -r requirements-dev.txt`
- CI runs tests on Python 3.11 and 3.12 via `.github/workflows/ci.yml`.