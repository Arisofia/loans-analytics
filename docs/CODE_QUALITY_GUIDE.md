# Code Quality Guide
**Version**: 1.0  
**Last Updated**: 2026-01-21  
**Status**: Active
---
## Overview
This guide provides comprehensive documentation for all code quality tools configured in the ABACO Loans Analytics repository. It covers setup, usage, and best practices for maintaining high code quality standards across Python and TypeScript/JavaScript codebases.
---
## Table of Contents
1. [Code Quality Tools Overview](#code-quality-tools-overview)
2. [ESLint (JavaScript/TypeScript)](#eslint-javascripttypescript)
3. [Pylint (Python)](#pylint-python)
4. [SonarQube](#sonarqube)
5. [Code Climate](#code-climate)
6. [Pre-commit Hooks](#pre-commit-hooks)
7. [Code Review Process](#code-review-process)
8. [Quick Reference Commands](#quick-reference-commands)
9. [Troubleshooting](#troubleshooting)
---
## Code Quality Tools Overview
Our repository uses multiple complementary tools for code quality analysis:
| Tool             | Language              | Purpose                                  | When It Runs                                            |
| ---------------- | --------------------- | ---------------------------------------- | ------------------------------------------------------- |
| **ESLint**       | TypeScript/JavaScript | Linting, code style, best practices      | Pre-commit, CI, Local                                   |
| **Pylint**       | Python                | Linting, code style, complexity          | Pre-commit, CI, Local                                   |
| **SonarQube**    | All                   | Security, bugs, code smells, tech debt   | CI (main branch, see `.github/workflows/sonarqube.yml`) |
| **Code Climate** | All                   | Maintainability, complexity, duplication | On-demand, CI                                           |
| **Black**        | Python                | Code formatting                          | Pre-commit, CI                                          |
| **isort**        | Python                | Import sorting                           | Pre-commit, CI                                          |
| **Bandit**       | Python                | Security vulnerabilities                 | Code Climate                                            |
| **Gitleaks**     | All                   | Secret scanning                          | Pre-commit                                              |
---
## ESLint (JavaScript/TypeScript)
### Overview
ESLint is configured for the Next.js web application with TypeScript, React, and accessibility rules.
### Configuration Files
- **Primary**: `apps/web/eslint.config.mjs` (ESLint flat config)
- **Legacy**: `apps/web/.eslintrc.json` (for backward compatibility)
### Running ESLint Locally
```bash
# From repository root
npm run lint --prefix apps/web
# From apps/web directory
cd apps/web
npm run lint
# Auto-fix issues
npm run lint:fix --prefix apps/web
# Run all quality checks
npm run check-all --prefix apps/web
```
### ESLint Rules Enforced
```javascript
// Key rules configured:
- @typescript-eslint/no-unused-vars: error (ignore _prefixed)
- @typescript-eslint/no-explicit-any: warn
- @typescript-eslint/no-floating-promises: error
- no-console: warn (allow warn/error)
- react-hooks/rules-of-hooks: error
- react-hooks/exhaustive-deps: warn
```
### Common ESLint Issues and Solutions
#### Issue: `@typescript-eslint/no-explicit-any`
```typescript
// ❌ Bad
function process(data: any) {}
// ✅ Good
function process(data: unknown) {}
function process<T>(data: T) {}
```
#### Issue: `@typescript-eslint/no-floating-promises`
```typescript
// ❌ Bad
fetchData()
// ✅ Good
await fetchData()
void fetchData()
fetchData().catch(console.error)
```
#### Issue: `@typescript-eslint/no-unused-vars`
```typescript
// ❌ Bad
function handler(event, context) {
  /* only uses event */
}
// ✅ Good
function handler(event, _context) {
  /* context ignored */
}
```
### ESLint in CI
ESLint runs automatically in the CI pipeline:
- `.github/workflows/ci.yml` - On PR and push to main
- `apps/web/.github/workflows/ci.yml` - Web-specific checks
---
## Pylint (Python)
### Overview
Pylint analyzes Python code for errors, enforces coding standards, and detects code smells.
### Configuration Files
- **Primary**: `.pylintrc` (Pylint configuration)
- **Alternative**: `pyproject.toml` (can also contain Pylint settings)
- **Pre-commit**: `.pre-commit-config.yaml`
### Running Pylint Locally
```bash
# Run Pylint on specific directories
pylint python apps/analytics/src
# Run Pylint with coverage report
make lint
# Run Pylint on specific file
pylint python/kpi_engine.py
# Run Pylint with custom config
pylint --rcfile=.pylintrc python/
# Generate JSON report
pylint --output-format=json python/ > pylint_report.json
# Check specific error codes
pylint --disable=all --enable=E python/
```
### Pylint Score Target
- **Target**: 9.0/10 or higher
- **Current**: 9.56/10 (Excellent)
- **Threshold**: Fail CI if score < 8.5
### Common Pylint Issues and Solutions
#### Issue: `too-many-arguments` (R0913)
```python
# ❌ Bad
def calculate(a, b, c, d, e, f, g, h):
    pass
# ✅ Good - Use dataclass or config object
from dataclasses import dataclass
@dataclass
class CalculationConfig:
    a: float
    b: float
    c: float
def calculate(config: CalculationConfig):
    pass
```
#### Issue: `unused-variable` (W0612)
```python
# ❌ Bad
def process():
    result = expensive_calculation()
    return True
# ✅ Good
def process():
    _ = expensive_calculation()  # Explicitly ignored
    return True
```
#### Issue: `line-too-long` (C0301)
```python
# ❌ Bad (> 88 characters)
def calculate_portfolio_metrics(total_receivable, eligible_amount, delinquent_bucket, current_date):
    pass
# ✅ Good - Use multi-line formatting
def calculate_portfolio_metrics(
    total_receivable: float,
    eligible_amount: float,
    delinquent_bucket: Dict[str, float],
    current_date: datetime
) -> Dict[str, float]:
    pass
```
### Pylint in CI
Pylint runs in:
- Pre-commit hooks (`.pre-commit-config.yaml`)
- CI pipeline (`.github/workflows/archived/ci-main.yml`)
- Makefile (`make lint`)
---
## SonarQube
### Overview
SonarQube provides comprehensive code quality analysis including security vulnerabilities, bugs, code smells, and technical debt.
### Configuration Files
- **Configuration**: `sonar-project.properties`
- **CI Workflow**: `.github/workflows/archived/ci-main.yml`
### Running SonarQube Analysis
SonarQube analysis runs automatically in CI on the main branch:
```yaml
# From .github/workflows/archived/ci-main.yml
sonar:
  runs-on: ubuntu-latest
  steps:
    - uses: SonarSource/sonarcloud-github-action@v5.0.0
      env:
        SONAR_TOKEN: ${{ secrets.SONAR_TOKEN }}
```
### SonarQube Configuration
```properties
# sonar-project.properties
sonar.organization=abaco-fintech
sonar.projectName=ABACO Loans Analytics
# Source directories
sonar.sources=apps,packages,python,src
# Test directories
sonar.tests=tests
# Coverage reports
sonar.python.coverage.reportPaths=coverage-python.xml
sonar.javascript.lcov.reportPaths=apps/web/coverage/lcov.info
```
### Accessing SonarQube Reports
1. **SonarCloud Dashboard**: Visit https://sonarcloud.io/
2. **Navigate**: Organizations → abaco-fintech → ABACO Loans Analytics
3. **View Metrics**:
   - Bugs
   - Vulnerabilities
   - Code Smells
   - Coverage
   - Duplications
   - Technical Debt
### SonarQube Quality Gates
Default quality gate requirements:
- Coverage ≥ 80%
- Duplicated Lines < 3%
- Maintainability Rating ≥ A
- Reliability Rating ≥ A
- Security Rating ≥ A
---
## Code Climate
### Overview
Code Climate provides automated code review for maintainability, complexity, and duplication detection.
### Configuration Files
- **Configuration**: `.codeclimate.yml`
### Setting Up Code Climate
#### Step 1: Sign Up and Connect Repository
1. Visit https://codeclimate.com/
2. Click "Sign up" and authenticate with GitHub
3. Click "Add a repository"
4. Select `Arisofia/abaco-loans-analytics`
5. Code Climate will automatically:
   - Detect `.codeclimate.yml` configuration
   - Start analyzing the codebase
   - Generate initial report
#### Step 2: Configure Quality Thresholds
In the Code Climate dashboard:
1. Navigate to **Repo Settings** → **Quality**
2. Set thresholds:
   - Complexity: Medium (default)
   - Duplication: 50 similar lines
   - Method length: 50 lines
   - Argument count: 5 parameters
#### Step 3: Enable GitHub Integration
1. Navigate to **Repo Settings** → **GitHub**
2. Enable:
   - Pull Request comments
   - Pull Request status checks
   - Inline issue comments
### Code Climate Plugins Enabled
```yaml
plugins:
  pylint: # Python linting
    enabled: true
  bandit: # Python security
    enabled: true
  eslint: # JavaScript/TypeScript
    enabled: true
  sonar-javascript: # JS code smells
    enabled: true
  duplication: # Code duplication
    enabled: true
```
### Accessing Code Climate Reports
1. **Dashboard**: https://codeclimate.com/github/Arisofia/abaco-loans-analytics
2. **Pull Requests**: Automatic comments on PRs with issues
3. **CLI Analysis** (local):
   ```bash
   # Install Code Climate CLI
   brew install codeclimate/formulae/codeclimate
   # Run analysis locally
   codeclimate analyze
   # Validate configuration
   codeclimate validate-config
   ```
### Understanding Code Climate Ratings
| Rating | Maintainability | Technical Debt |
| ------ | --------------- | -------------- |
| **A**  | Excellent       | < 5%           |
| **B**  | Good            | 5-10%          |
| **C**  | Satisfactory    | 10-20%         |
| **D**  | Poor            | 20-50%         |
| **F**  | Critical        | > 50%          |
### Common Code Climate Issues
#### High Complexity
```python
# ❌ Bad - Cyclomatic Complexity: 15
def process_loan(loan, status, type, risk, amount):
    if status == "active":
        if type == "personal":
            if risk == "high":
                if amount > 10000:
                    return calculate_high_risk()
                else:
                    return calculate_normal()
            else:
                return calculate_low_risk()
        else:
            return calculate_business()
    else:
        return None
# ✅ Good - Refactored into smaller functions
def process_loan(loan):
    if not loan.is_active():
        return None
    calculator = get_loan_calculator(loan)
    return calculator.calculate()
def get_loan_calculator(loan):
    if loan.is_personal():
        return PersonalLoanCalculator(loan)
    return BusinessLoanCalculator(loan)
```
#### Code Duplication
```python
# ❌ Bad - Duplicated logic
def calculate_par_30(data):
    delinquent = data[data['days_past_due'] > 30]['balance'].sum()
    total = data['balance'].sum()
    return delinquent / total if total > 0 else 0
def calculate_par_90(data):
    delinquent = data[data['days_past_due'] > 90]['balance'].sum()
    total = data['balance'].sum()
    return delinquent / total if total > 0 else 0
# ✅ Good - DRY principle
def calculate_par(data, threshold):
    delinquent = data[data['days_past_due'] > threshold]['balance'].sum()
    total = data['balance'].sum()
    return delinquent / total if total > 0 else 0
def calculate_par_30(data):
    return calculate_par(data, 30)
def calculate_par_90(data):
    return calculate_par(data, 90)
```
---
## Pre-commit Hooks
### Overview
Pre-commit hooks automatically check code quality before commits, preventing issues from reaching CI.
### Configuration File
- `.pre-commit-config.yaml`
### Installing Pre-commit Hooks
```bash
# Install pre-commit package
pip install pre-commit
# Install hooks for this repository
pre-commit install
# Run hooks on all files (first time or after config changes)
pre-commit run --all-files
```
### Hooks Configured
1. **trailing-whitespace**: Remove trailing whitespace
2. **end-of-file-fixer**: Ensure files end with newline
3. **check-yaml**: Validate YAML syntax
4. **check-added-large-files**: Prevent large files (>1MB)
5. **black**: Format Python code (Python 3.11)
6. **isort**: Sort Python imports
7. **yamllint**: Lint YAML files
8. **gitleaks**: Scan for secrets/credentials
### Temporarily Bypassing Hooks
```bash
# Skip all hooks for a commit (use sparingly!)
git commit --no-verify -m "Emergency fix"
# Skip specific hook
SKIP=black git commit -m "Skip black formatting"
```
### Updating Hooks
```bash
# Update to latest versions
pre-commit autoupdate
# Clean and reinstall
pre-commit clean
pre-commit install
```
---
## Code Review Process
### Overview
Code reviews ensure quality, knowledge sharing, and maintain coding standards.
### CODEOWNERS File
- **Location**: `.github/CODEOWNERS`
- **Configuration**:
  ```
  .github/workflows/* @Arisofia
  ```
### Pull Request Checklist
Before requesting a review:
- [ ] Code passes all linters (ESLint, Pylint)
- [ ] All tests pass locally
- [ ] Pre-commit hooks pass
- [ ] Code coverage maintained/improved
- [ ] Documentation updated (if needed)
- [ ] No secrets or sensitive data committed
- [ ] Self-review completed
### Setting Up Code Review Automation
#### GitHub Branch Protection Rules
1. Navigate to: **Repository Settings** → **Branches**
2. Add rule for `main`:
   - ✅ Require pull request reviews (1 reviewer)
   - ✅ Require status checks (CI, linting, tests)
   - ✅ Require branches up to date
   - ✅ Require conversation resolution
   - ✅ Enforce for administrators
#### Pull Request Templates
Create `.github/pull_request_template.md`:
```markdown
## Description
<!-- Brief description of changes -->
## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update
## Testing
- [ ] Tests pass locally
- [ ] New tests added
- [ ] Manual testing completed
## Code Quality
- [ ] ESLint passes
- [ ] Pylint passes
- [ ] Pre-commit hooks pass
- [ ] Code Climate checks pass
## Checklist
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No breaking changes (or documented)
```
---
## Quick Reference Commands
### TypeScript/JavaScript (Web App)
```bash
# Lint
npm run lint --prefix apps/web
# Lint with auto-fix
npm run lint:fix --prefix apps/web
# Type check
npm run type-check --prefix apps/web
# Format check
npm run format:check --prefix apps/web
# Auto-format
npm run format --prefix apps/web
# All checks
npm run check-all --prefix apps/web
```
### Python
```bash
# Lint with Pylint
make lint
pylint python apps/analytics/src
# Format with Black
black python/ tests/
# Sort imports
isort python/ tests/
# Run tests with coverage
pytest --cov=python --cov-report=term-missing
# Run all quality checks
make quality
```
### Pre-commit
```bash
# Install hooks
pre-commit install
# Run on all files
pre-commit run --all-files
# Run specific hook
pre-commit run black --all-files
# Update hooks
pre-commit autoupdate
```
### Code Climate
```bash
# Install CLI (macOS)
brew install codeclimate/formulae/codeclimate
# Run analysis locally
codeclimate analyze
# Validate config
codeclimate validate-config
```
---
## Troubleshooting
### ESLint Issues
#### Issue: "Cannot find module '@next/eslint-plugin-next'"
```bash
# Solution: Reinstall dependencies
cd apps/web
rm -rf node_modules
npm install
```
#### Issue: "Parsing error: Cannot read file 'tsconfig.json'"
```bash
# Solution: Ensure tsconfig.json exists and is valid
cd apps/web
npx tsc --noEmit  # Validate TypeScript config
```
### Pylint Issues
#### Issue: "ImportError: No module named 'pytest'"
```bash
# Solution: Install dev dependencies
pip install -r requirements-dev.txt
```
#### Issue: "Pylint score suddenly drops"
```bash
# Solution: Check for new files not formatted
black python/ tests/
isort python/ tests/
pylint python/ --exit-zero  # Don't fail, just report
```
### Pre-commit Issues
#### Issue: "Hook failed: black"
```bash
# Solution: Run black manually to see full error
black python/ tests/ --check --diff
# Auto-fix
black python/ tests/
```
#### Issue: "Hook failed: gitleaks"
```bash
# Solution: Check what was detected
git diff  # Review staged changes
# If false positive, add to .gitleaksignore
echo "path/to/file:sha" >> .gitleaksignore
```
### SonarQube Issues
#### Issue: "SonarQube analysis not appearing"
1. Check if running on main branch (skips PRs)
2. Verify SONAR_TOKEN secret is set in repository
3. Check CI logs for errors
#### Issue: "Coverage report not found"
```bash
# Solution: Ensure coverage is generated
pytest --cov=python --cov-report=xml:coverage-python.xml
```
### Code Climate Issues
#### Issue: "Config validation failed"
```bash
# Solution: Validate locally
codeclimate validate-config
# Check YAML syntax
yamllint .codeclimate.yml
```
#### Issue: "Plugin not running"
Check exclusion patterns in `.codeclimate.yml`:
```yaml
exclude_patterns:
  - 'path/to/exclude/**'
```
---
## Additional Resources
### Documentation Links
- **ESLint**: https://eslint.org/docs/latest/
- **Pylint**: https://pylint.pycqa.org/en/latest/
- **SonarQube**: https://docs.sonarqube.org/latest/
- **Code Climate**: https://docs.codeclimate.com/
- **Pre-commit**: https://pre-commit.com/
- **Black**: https://black.readthedocs.io/
- **isort**: https://pycqa.github.io/isort/
### Internal Documentation
- `docs/ENGINEERING_STANDARDS.md` - Engineering standards and best practices
- `docs/LINTING_STANDARDS.md` - Detailed linting standards (if exists)
- `CLAUDE.md` - Quick reference for CI/CD and quality checks
### Support
For questions or issues:
1. Check this guide and troubleshooting section
2. Review CI logs for specific errors
3. Consult code owners: @Arisofia
---
## Changelog
### Version 1.0 (2026-01-21)
- Initial comprehensive code quality guide
- Added Code Climate configuration
- Added Pylint configuration
- Documented all tools and workflows
- Added troubleshooting section
- Added quick reference commands
