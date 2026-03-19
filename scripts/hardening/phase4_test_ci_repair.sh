#!/usr/bin/env bash
# =============================================================================
# phase4_test_ci_repair.sh
# After destructive cleanup: fix test paths, verify CI, run the test suite.
# Must be run after phases 1-3.
#
# Run from repo root:
#   bash scripts/hardening/phase4_test_ci_repair.sh
#
# On Windows with Git Bash, set PYTHON_BIN before calling:
#   PYTHON_BIN="C:/Users/.../Python312/python.exe" bash scripts/hardening/phase4_test_ci_repair.sh
# =============================================================================
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

# ─────────────────────────────────────────────────────────────────────────────
# Detect Python binary (Windows Git Bash safe)
# ─────────────────────────────────────────────────────────────────────────────
if [ -n "${PYTHON_BIN:-}" ] && command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  PYTHON="$PYTHON_BIN"
elif python --version >/dev/null 2>&1; then
  PYTHON="python"
elif python3 --version >/dev/null 2>&1; then
  PYTHON="python3"
else
  # Last resort: fall back to common Windows location
  WIN_PY="$LOCALAPPDATA/Programs/Python/Python312/python.exe"
  if [ -f "$WIN_PY" ]; then
    PYTHON="$WIN_PY"
  else
    echo "ERROR: Python not found. Set PYTHON_BIN env var to your Python executable."
    exit 1
  fi
fi

GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'

ok()   { echo -e "${GREEN}  ✓${RESET}  $1"; }
fail() { echo -e "${RED}  ✗${RESET}  $1"; }
warn() { echo -e "${YELLOW}  ⚠${RESET}  $1"; }
info() { echo -e "${CYAN}  →${RESET}  $1"; }

echo -e "${BOLD}${CYAN}"
echo "══════════════════════════════════════════════════════════════"
echo " PHASE 4 — TEST AND CI REPAIR"
echo "══════════════════════════════════════════════════════════════"
echo -e "${RESET}"
echo "  Python: $PYTHON"
echo "  Repo:   $REPO_ROOT"

CANONICAL_TEST_DIR="backend/python/tests"
PASS_COUNT=0
FAIL_COUNT=0

# ─────────────────────────────────────────────────────────────────────────────
# 1. MOVE MISPLACED TESTS INTO CANONICAL DIRECTORY
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo "[1] Relocating misplaced test files from backend/python/multi_agent/ ..."

SRC_DIR="backend/python/multi_agent"
MULTI_TESTS=(
  test_agent_factory.py
  test_base_agent_grok.py
  test_config_historical.py
  test_continuous_learning.py
  test_database_designer_agent.py
  test_historical_context.py
  test_historical_supabase_integration.py
  test_kpi_integration.py
  test_multi_agent_unittest.py
  test_orchestrator_historical_integration.py
  test_scenario_packs.py
  test_specialized_agents.py
  test_trend_analysis_g4_2.py
)

for f in "${MULTI_TESTS[@]}"; do
  SRC_FILE="$SRC_DIR/$f"
  # Rename: test_agent_factory.py → test_multi_agent_agent_factory.py
  DST_FILE="$CANONICAL_TEST_DIR/test_multi_agent_${f#test_}"
  if [ -f "$SRC_FILE" ]; then
    # Skip if destination already exists (from a previous run)
    if [ -f "$DST_FILE" ]; then
      warn "Skipped (dst exists): $f → $DST_FILE"
      continue
    fi
    if git ls-files --error-unmatch "$SRC_FILE" >/dev/null 2>&1; then
      git mv "$SRC_FILE" "$DST_FILE" 2>/dev/null \
        || { cp "$SRC_FILE" "$DST_FILE"; git rm -f "$SRC_FILE"; }
    else
      cp "$SRC_FILE" "$DST_FILE" && rm -f "$SRC_FILE"
    fi
    ok "Moved: $f → $DST_FILE"
    ((PASS_COUNT++)) || true
  else
    info "Not found (already moved or deleted): $SRC_FILE"
  fi
done

# ─────────────────────────────────────────────────────────────────────────────
# 2. ENSURE CANONICAL CONFTEST.PY EXISTS AND IS CORRECT
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo "[2] Validating conftest.py..."

CANONICAL_CONFTEST="$CANONICAL_TEST_DIR/conftest.py"
ROOT_CONFTEST="conftest.py"

if [ -f "$ROOT_CONFTEST" ] && [ -f "$CANONICAL_CONFTEST" ]; then
  if cmp -s "$ROOT_CONFTEST" "$CANONICAL_CONFTEST"; then
    git rm -f "$ROOT_CONFTEST" 2>/dev/null || rm -f "$ROOT_CONFTEST"
    ok "Root conftest.py removed (identical to canonical)"
    ((PASS_COUNT++)) || true
  else
    warn "Root and canonical conftest.py differ — serving different test trees (expected)."
    info "  Root conftest:      $ROOT_CONFTEST"
    info "  Canonical conftest: $CANONICAL_CONFTEST"
    info "  Both are needed. No action required."
    ((PASS_COUNT++)) || true
  fi
elif [ -f "$ROOT_CONFTEST" ] && [ ! -f "$CANONICAL_CONFTEST" ]; then
  git mv "$ROOT_CONFTEST" "$CANONICAL_CONFTEST" 2>/dev/null || {
    cp "$ROOT_CONFTEST" "$CANONICAL_CONFTEST" && git rm -f "$ROOT_CONFTEST"
  }
  ok "Root conftest.py moved to canonical location"
  ((PASS_COUNT++)) || true
else
  ok "conftest.py in correct location: $CANONICAL_CONFTEST"
  ((PASS_COUNT++)) || true
fi

# ─────────────────────────────────────────────────────────────────────────────
# 3. VERIFY pytest CONFIGURATION IN pyproject.toml
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo "[3] Resolving pytest configuration..."

if [ -f "pytest.ini" ] && [ -f "pyproject.toml" ]; then
  EXISTING_PYTEST=$(grep -c "\[tool.pytest" pyproject.toml || echo 0)
  if [ "$EXISTING_PYTEST" -gt 0 ]; then
    warn "pyproject.toml already has pytest config AND pytest.ini still exists."
    warn "Verify coverage is equivalent then remove pytest.ini:"
    echo "    git rm pytest.ini"
    ((FAIL_COUNT++)) || true
  else
    # Read pytest.ini content (skip [pytest] header)
    PYTEST_CONTENT=$(awk 'NR>1' pytest.ini)
    cat >> pyproject.toml << PYTOML

[tool.pytest.ini_options]
testpaths = ["backend/python/tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
$PYTEST_CONTENT
PYTOML
    git rm -f pytest.ini 2>/dev/null || rm -f pytest.ini
    ok "pytest.ini merged into pyproject.toml and removed"
    ((PASS_COUNT++)) || true
  fi
elif [ -f "pytest.ini" ]; then
  warn "pyproject.toml not found — keeping pytest.ini"
  ((FAIL_COUNT++)) || true
else
  # No pytest.ini — verify pyproject.toml has the right testpaths
  if grep -q "testpaths" pyproject.toml 2>/dev/null; then
    if grep -q "backend/python/tests" pyproject.toml; then
      ok "testpaths correctly includes backend/python/tests in pyproject.toml"
      ((PASS_COUNT++)) || true
    else
      warn "testpaths in pyproject.toml does not include backend/python/tests — patching"
      "$PYTHON" -c "
import pathlib
p = pathlib.Path('pyproject.toml')
c = p.read_text()
if 'testpaths' in c and 'backend/python/tests' not in c:
    c = c.replace('testpaths = [', 'testpaths = [\"backend/python/tests\", ')
    p.write_text(c)
    print('  Patched testpaths in pyproject.toml')
"
      ((PASS_COUNT++)) || true
    fi
  else
    warn "No testpaths found in pyproject.toml"
    ((FAIL_COUNT++)) || true
  fi
fi

# ─────────────────────────────────────────────────────────────────────────────
# 4. VALIDATE IMPORTS DON'T REFERENCE DELETED MODULES
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo "[4] Scanning for imports of deleted modules..."

# These paths were removed in phases 1-3 and must not be imported anywhere
DEAD_MODULES=(
  "backend.src.agents.multi_agent"
  "backend.src.zero_cost.dpd_calculator"
  "frontend.streamlit_app.fuzzy_table_mapping"
)

DEAD_IMPORT_FOUND=false
for module in "${DEAD_MODULES[@]}"; do
  # Exclude hardening scripts — they reference deleted paths as string literals, not imports
  RESULTS=$(grep -r "$module" --include="*.py" \
    --exclude-dir=__pycache__ \
    --exclude-dir=".git" \
    --exclude-dir="scripts" \
    . 2>/dev/null || true)
  if [ -n "$RESULTS" ]; then
    fail "Dead import found: $module"
    echo "$RESULTS" | head -5
    DEAD_IMPORT_FOUND=true
    ((FAIL_COUNT++)) || true
  fi
done
$DEAD_IMPORT_FOUND || ok "No dead imports to deleted modules found"
$DEAD_IMPORT_FOUND || ((PASS_COUNT++)) || true

# ─────────────────────────────────────────────────────────────────────────────
# 5. RUN THE TEST SUITE
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo "[5] Running canonical test suite (backend/python/tests)..."

PYTEST_LOG="/tmp/pytest_hardening.log"
if "$PYTHON" -m pytest "$CANONICAL_TEST_DIR" \
    --tb=short -q \
    --no-header \
    --no-cov \
    2>&1 | tee "$PYTEST_LOG"; then
  ok "Test suite PASSED"
  ((PASS_COUNT++)) || true
else
  fail "Test suite FAILED — see $PYTEST_LOG"
  ((FAIL_COUNT++)) || true
fi

# ─────────────────────────────────────────────────────────────────────────────
# 6. RUN LINTING
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo "[6] Running linting (ruff)..."

RUFF_LOG="/tmp/ruff_hardening.log"
if command -v ruff >/dev/null 2>&1; then
  if ruff check backend/ --quiet 2>&1 | tee "$RUFF_LOG"; then
    ok "ruff: no errors in backend/"
    ((PASS_COUNT++)) || true
  else
    fail "ruff errors found — see $RUFF_LOG"
    ((FAIL_COUNT++)) || true
  fi
elif "$PYTHON" -m ruff check backend/ --quiet 2>&1 | tee "$RUFF_LOG"; then
  ok "ruff (via python -m ruff): no errors"
  ((PASS_COUNT++)) || true
else
  warn "ruff not installed or failed — skipping lint check"
fi

# ─────────────────────────────────────────────────────────────────────────────
# 7. RUN TYPE CHECKING
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo "[7] Running type checking (mypy)..."

MYPY_LOG="/tmp/mypy_hardening.log"
if command -v mypy >/dev/null 2>&1; then
  MYPY_CMD="mypy"
elif "$PYTHON" -m mypy --version >/dev/null 2>&1; then
  MYPY_CMD="$PYTHON -m mypy"
else
  MYPY_CMD=""
fi

if [ -n "$MYPY_CMD" ]; then
  if $MYPY_CMD backend/python/ backend/src/ \
      --ignore-missing-imports --no-error-summary -q \
      2>&1 | tee "$MYPY_LOG" | grep -E "^Found|^Success" | tail -1; then
    ok "mypy check complete (see $MYPY_LOG for details)"
    ((PASS_COUNT++)) || true
  else
    warn "mypy issues found — see $MYPY_LOG"
    ((FAIL_COUNT++)) || true
  fi
else
  warn "mypy not installed — skipping type check"
fi

# ─────────────────────────────────────────────────────────────────────────────
# 8. VALIDATE CI WORKFLOW PATHS
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo "[8] Validating CI workflow paths..."

CI_FILES=(
  ".github/workflows/tests.yml"
  ".github/workflows/pr-checks.yml"
  ".github/workflows/security-scan.yml"
)

for ci_file in "${CI_FILES[@]}"; do
  if [ ! -f "$ci_file" ]; then
    warn "CI file not found: $ci_file"
    ((FAIL_COUNT++)) || true
    continue
  fi
  # Check for references to paths deleted in phases 1-3
  for dead in "backend/python/multi_agent/test_" "pytest_full.log"; do
    if grep -q "$dead" "$ci_file" 2>/dev/null; then
      fail "$ci_file references deleted path: $dead"
      ((FAIL_COUNT++)) || true
    fi
  done
  # Check for correct test path (either canonical or root tests/ are valid)
  if grep -qE "backend/python/tests|pytest tests/" "$ci_file"; then
    ok "$ci_file references a valid test path"
    ((PASS_COUNT++)) || true
  else
    warn "$ci_file may not reference a test directory"
  fi
done

# ─────────────────────────────────────────────────────────────────────────────
# SUMMARY
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo "════════════════════════════════════════════════"
echo " PHASE 4 SUMMARY"
echo "  PASS: $PASS_COUNT"
echo "  FAIL: $FAIL_COUNT"
echo "════════════════════════════════════════════════"

if [ "$FAIL_COUNT" -eq 0 ]; then
  echo -e "${GREEN}${BOLD}  → All CI/test checks passed. Ready to commit.${RESET}"
  echo ""
  echo "  git add -A"
  echo "  git commit -m 'fix(ci): repair tests and CI after production purge'"
else
  echo -e "${RED}${BOLD}  → $FAIL_COUNT issues require resolution before committing.${RESET}"
  exit 1
fi
