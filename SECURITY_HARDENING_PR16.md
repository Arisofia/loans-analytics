# PR #16: Security Hardening & Path Refactoring

## Executive Summary

This PR addresses **critical security vulnerabilities** and **configuration
brittleness** identified in the codebase:

- **🔴 CRITICAL**: Exposed credentials in `.env` (Azure, OpenAI, Anthropic, HubSpot)
- **🟠 HIGH**: 40+ hard-coded paths across codebase causing deployment failures
- **🟡 MEDIUM**: Inconsistent secrets management (3 different patterns)
- **🟡 MEDIUM**: Missing path validation causing silent runtime failures

---

## CRITICAL ISSUE: Exposed Secrets

### Current State

`.env` file contains **active production credentials**:

- Azure Client Secret, Tenant ID, Subscription ID
- OpenAI API Key (billing exposure)
- Anthropic API Key (billing exposure)
- HubSpot API Key and Portal ID

### Remediation

#### Step 1: Remove from Git History

```bash
# Install BFG Repo Cleaner
brew install bfg

# Create file with patterns to remove
cat > /tmp/secrets.txt <<'SECRETS'
# Secrets must be set via environment variables or GitHub Secrets. See documentation for details.
HUBSPOT_TOKEN=*
SECRETS

# Remove all matches
bfg --replace-text /tmp/secrets.txt .

# Cleanup
git reflog expire --expire=now --all && git gc --prune=now

# Force push (WARNING: Rewrites history)
git push -f origin main
```

#### Step 2: Rotate Credentials Immediately

- [ ] Azure: Regenerate Client Secret in Azure Portal
- [ ] OpenAI: Deactivate exposed key, create new one
- [ ] Anthropic: Deactivate exposed key, create new one
- [ ] HubSpot: Deactivate API key, create new one

#### Step 3: Use GitHub Secrets

All secrets should be stored in GitHub Repository Settings → Secrets, NOT in `.env`

```yaml
# Example workflow usage:
- name: Run pipeline
  env:
    OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
    ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
  run: python scripts/run_data_pipeline.py
```

---

## Hard-Coded Paths: Comprehensive Refactoring

### Solution: Centralized Paths Module

New module: `src/config/paths.py` provides environment-aware path resolution:

```python
from src.config.paths import Paths

# Usage:
config_file = Paths.config_file()
metrics_dir = Paths.metrics_dir(create=True)
logs_dir = Paths.logs_dir(create=True)
environment = Paths.get_environment()
```

### Environment Variables Supported

| Variable                  | Default            | Purpose              |
| ------------------------- | ------------------ | -------------------- |
| `DATA_RAW_PATH`           | `./data/raw`       | Raw input data       |
| `DATA_METRICS_PATH`       | `./data/metrics`   | Calculated KPIs      |
| `CONFIG_PATH`             | `./config`         | Config files         |
| `LOGS_PATH`               | `./logs`           | Application logs     |
| `REPORTS_PATH`            | `./reports`        | Generated reports    |
| `PYTHON_ENV` or `APP_ENV` | `development`      | Current environment  |

### Migration Plan

#### Files to Refactor (Priority Order)

1. **`src/pipeline/orchestrator.py`** (Lines 36-37)

   ```python
   # BEFORE:
   DEFAULT_CONFIG_PATH = Path("config/pipeline.yml")
   ENVIRONMENTS_DIR = Path("config/environments")

   # AFTER:
   from src.config.paths import Paths
   config_path = Paths.config_file()
   environments_dir = Paths.config_file().parent.parent / "environments"
   ```

2. **`scripts/production_cutover.sh`** (Lines 13-18)

   ```bash
   # BEFORE:
   LOG_FILE="${PROD_DIR}/logs/cutover_$(date +%Y%m%d_%H%M%S).log"
   mkdir -p "$(dirname "$LOG_FILE")" "$ROLLBACK_DIR"

   # AFTER:
   LOG_DIR="${LOGS_PATH:-.logs}"
   mkdir -p "$LOG_DIR" "$ROLLBACK_DIR"
   LOG_FILE="$LOG_DIR/cutover_$(date +%Y%m%d_%H%M%S).log"
   ```

3. **`scripts/run_data_pipeline.py`** (Line 95)

   ```python
   # BEFORE:
   DEFAULT_INPUT = os.getenv("PIPELINE_INPUT_FILE", "data/abaco_portfolio_calculations.csv")

   # AFTER:
   from src.config.paths import Paths
   DEFAULT_INPUT = os.getenv("PIPELINE_INPUT_FILE", str(Paths.raw_data_dir() / "abaco_portfolio_calculations.csv"))
   ```

4. **`scripts/monitoring_checkpoint.py`** (Line 77)

   ```python
   # BEFORE:
   def save_checkpoint(self, output_dir: str = "logs/monitoring") -> str:

   # AFTER:
   from src.config.paths import Paths
   def save_checkpoint(self, output_dir: Optional[str] = None) -> str:
       if output_dir is None:
           output_dir = str(Paths.monitoring_logs_dir(create=True))
   ```

5. **`scripts/load_secrets.py`** (Line 9)

   ```python
   # BEFORE:
   vault_name = os.getenv("AZURE_KEY_VAULT_NAME", "abaco-capital-kv")

   # AFTER:
   vault_name = os.getenv("AZURE_KEY_VAULT_NAME")
   if not vault_name:
       raise ValueError("AZURE_KEY_VAULT_NAME env var is required")
   ```

---

## Secrets Management: Unified Pattern

### Current: 3 Different Patterns ❌

1. Azure Key Vault (`load_secrets.py`)
2. Environment Variables (`.env`)
3. GitHub Secrets (workflows)

### Proposed: Single Pattern ✅

All secrets via **environment variables** (from GitHub Secrets → workflow → container):

```bash
# .env.example (for documentation only)

# Actual deployment: GitHub Secrets or K8s/container secrets
```

### New Module: `src/config/secrets.py`

```python
import os
from typing import Optional

class SecretsManager:
    """Unified secrets access with validation."""

    REQUIRED = [
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
    ]

    OPTIONAL = [
        "GEMINI_API_KEY",
        "PERPLEXITY_API_KEY",
        "HUBSPOT_API_KEY",
    ]

    @classmethod
    def validate_all(cls, fail_on_missing_optional: bool = False) -> dict:
        """Validate all secrets are available."""
        missing = []

        for key in cls.REQUIRED:
            if not os.getenv(key):
                missing.append(key)

        if fail_on_missing_optional:
            for key in cls.OPTIONAL:
                if not os.getenv(key):
                    missing.append(key)

        if missing:
            raise ValueError(f"Missing secrets: {', '.join(missing)}")

        return {"status": "ok", "validated": len(cls.REQUIRED) + len(cls.OPTIONAL)}

    @classmethod
    def get(cls, key: str, required: bool = False) -> Optional[str]:
        """Get a secret with optional validation."""
        value = os.getenv(key)
        if required and not value:
            raise ValueError(f"Required secret {key} not found")
        return value
```

---

## Testing & Validation

### Unit Tests to Add

```python
# tests/test_paths.py
from src.config.paths import Paths, resolve_path

def test_resolve_path_absolute():
    """Absolute paths remain unchanged."""
    assert resolve_path("/tmp/test").name == "test"

def test_resolve_path_with_env_var():
    """Environment variables take precedence."""
    os.environ["TEST_PATH"] = "/custom/path"
    assert resolve_path("./default", env_var="TEST_PATH") == Path("/custom/path")

def test_paths_create_missing_dirs(tmp_path):
    """Directories are created when create=True."""
    test_dir = tmp_path / "new_dir"
    result = resolve_path(str(test_dir), create=True)
    assert result.exists()

def test_metrics_dir_environment_override():
    """METRICS_DIR env var overrides default."""
    os.environ["METRICS_DIR"] = "/var/metrics"
    assert Paths.metrics_dir() == Path("/var/metrics")
```

### Integration Tests

```bash
# Test with custom paths
export LOGS_PATH=/tmp/test_logs
export METRICS_PATH=/tmp/test_metrics
python -m pytest tests/test_pipeline_orchestrator.py -v
```

---

## Deployment Checklist

- [ ] Remove credentials from git history (`bfg` or `git filter-branch`)
- [ ] Rotate all exposed API keys
- [ ] Create GitHub Secrets for all credentials
- [ ] Merge `src/config/paths.py` and `src/config/secrets.py`
- [ ] Refactor 10+ scripts to use `Paths` module
- [ ] Add unit tests for path resolution
- [ ] Update `.env.example` (credentials only)
- [ ] Test locally with custom `*_PATH` env vars
- [ ] Test in staging with GitHub Secrets
- [ ] Document in CONTRIBUTING.md

---

## Security Benefits

✅ **No secrets in git** - All credentials in GitHub Secrets or K8s
✅ **Environment-agnostic paths** - Same code runs locally, staging, prod
✅ **Automatic directory creation** - No silent failures on missing directories
✅ **Centralized configuration** - Single source of truth for all paths
✅ **Easy environment switching** - Set env vars once, code adapts
✅ **Audit trail** - GitHub Actions logs secrets access (masked)

---

## References

- OWASP: Secret Management Best Practices
- GitHub: Using Secrets in Actions
- Twelve-Factor App: Configuration as Environment Variables
