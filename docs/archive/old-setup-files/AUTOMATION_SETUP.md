# Automation Setup Guide

## 🤖 Automated Workflows

This repository now has comprehensive automation for code quality, testing, security, and dependencies.

### Workflows Enabled

#### 1. **Auto Format & Lint** (`.github/workflows/auto-format-and-lint.yml`)

- **Triggers**: On PR and push to main
- **Features**:
  - Black formatting (Python)
  - isort (import sorting)
  - Ruff (linting and fixes)
  - ESLint (JavaScript/TypeScript)
  - Auto-commits formatting changes

**Usage**:

```bash
# Manual formatting
git checkout feat/my-feature
black python/ .github/scripts/
isort python/ .github/scripts/
git push
```

#### 2. **Auto Test** (`.github/workflows/auto-test.yml`)

- **Triggers**: On PR and push to main
- **Features**:
  - Pytest with coverage reports
  - Tests on Python 3.10, 3.11, 3.12
  - CodeCov integration
  - PR comments with results

**Usage**:

```bash
# Run tests locally
pytest tests/ -v --cov=python
```

#### 3. **Auto Security Scan** (`.github/workflows/auto-security-scan.yml`)

- **Triggers**: On PR, push, and weekly schedule
- **Features**:
  - Bandit security scanning
  - Safety dependency check
  - Snyk integration (if token available)
  - Artifact reports

**Usage**:

```bash
# Local security scan
bandit -r python/ .github/scripts/
safety check
pip-audit
```

#### 4. **Auto Dependencies** (`.github/workflows/auto-dependencies.yml`)

- **Triggers**: Weekly on Monday at 2 AM
- **Features**:
  - Python requirements updates
  - NPM package updates
  - Security fixes
  - Auto-commits and changelog

#### 5. **Pre-commit Hooks** (`.pre-commit-config.yaml`)

- **Triggers**: On `git commit`
- **Features**:
  - Code formatting
  - Linting
  - Security checks
  - Large file detection

## 🚀 Getting Started

### 1. Install Local Automation

Run the setup script:

```bash
chmod +x scripts/setup-automation.sh
./scripts/setup-automation.sh
```

This will:

- Install pre-commit framework
- Install all pre-commit hooks
- Configure git aliases
- Run initial compliance check

### 2. Available Git Aliases

After setup, you can use these shortcuts:

```bash
git check        # Run pre-commit checks on all files
git fmt          # Format all Python code
git test         # Run pytest suite
```

### 3. Manual Pre-commit Run

```bash
# Check specific file
pre-commit run --files path/to/file.py

# Check all files
pre-commit run --all-files

# Skip pre-commit on commit (not recommended)
git commit --no-verify
```

## 📋 CI/CD Flow

### On Pull Request:

1. **Auto Format & Lint** - Formats code, commits if changes
2. **Auto Test** - Runs pytest on 3 Python versions
3. **Auto Security Scan** - Runs security checks
4. All checks must pass before merge

### On Push to Main:

- Same as PR, but on the main branch

### Weekly (Monday 2 AM):

- **Auto Dependencies** - Updates dependencies
- Creates weekly changelog

## 🔧 Configuration Files

### `.pre-commit-config.yaml`

Define which checks run on every commit. Includes:

- Trailing whitespace removal
- Black formatter
- isort (import sorting)
- Ruff
- Flake8
- YAML linting
- Markdown formatting

### `.github/workflows/auto-*.yml`

CI/CD workflows for GitHub Actions. Each can be customized.

## 🎯 Best Practices

1. **Always use local pre-commit** - Catch issues before pushing
2. **Read pre-commit errors** - Fix manually if needed
3. **Test locally before PR** - `git test` runs full suite
4. **Review auto-commits** - GitHub bot may commit formatting changes
5. **Keep dependencies updated** - Weekly automation handles this

## 🚨 Troubleshooting

### Pre-commit not running on commit?

```bash
# Reinstall hooks
pre-commit install

# Verify installation
git config core.hooksPath
```

### Workflows failing?

- Check GitHub Actions logs
- Common causes:
  - Missing dependencies in `requirements*.txt`
  - Python version incompatibility
  - Network timeouts (usually transient)

### Want to skip a check temporarily?

```bash
# Skip specific hook
pre-commit run --hook-stage=commit --exclude black

# Skip all checks (use with caution)
git commit --no-verify
```

## 📊 Viewing Results

### GitHub Actions Dashboard

- Repository → Actions tab
- Click workflow to see detailed logs
- See artifacts and coverage reports

### Pre-commit Local

- Errors display in terminal on `git commit`
- Fix issues and try again

## 🔐 Security

Workflows include:

- ✅ Bandit (code security scanning)
- ✅ Safety (dependency vulnerability checking)
- ✅ Snyk (supply chain security)
- ✅ pip-audit (PyPI audit)

Run locally:

```bash
bandit -r python/
safety check
pip-audit
```

## 📝 Next Steps

1. Install local automation: `./scripts/setup-automation.sh`
2. Make a test commit to verify pre-commit works
3. Create a PR to test CI/CD workflows
4. Monitor weekly dependency updates
5. Review and merge automated changes

---

**Questions?** Check individual workflow files in `.github/workflows/`
