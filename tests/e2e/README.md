# End-to-End (E2E) Testing

This directory contains E2E tests for both the backend (FastAPI) and frontend (Streamlit) components of the Abaco Loans Analytics platform.

## Purpose
- Ensure robust, high-coverage testing of mission-critical finance workflows
- Validate integration between backend and frontend
- Automate user flows and API interactions

## Structure
- `test_backend_api.py`: Backend integration tests using pytest and requests
- `test_frontend_playwright.py`: Frontend E2E tests using Playwright

## Setup
1. Install development dependencies:
   ```sh
   python3 -m pip install -r requirements-dev.txt --break-system-packages
   ```
2. Install Playwright browsers:
   ```sh
   python3 -m playwright install
   ```
3. Ensure backend (FastAPI) is running at http://localhost:8000
4. Ensure frontend (Streamlit) is running at http://localhost:8501

## Running Tests
To run all E2E tests:
```sh
pytest tests/e2e --cov=.
```

## Coverage
- Target: 95%+ code coverage
- Coverage reports generated with pytest-cov

## Notes
- Use fixtures and mocking to isolate tests from external dependencies
- Expand test cases to cover edge cases and critical user flows

## References
- [pytest](https://docs.pytest.org/)
- [pytest-playwright](https://github.com/microsoft/playwright-pytest)
- [pytest-cov](https://pytest-cov.readthedocs.io/)
