# Phase F Quick Start Guide

## Getting Started with CI/Quality Gates

This guide helps you quickly set up and use the Phase F CI/Quality Gate automation system.

## Prerequisites

- GitHub repository access
- Python 3.11 or 3.12
- Required dependencies installed

## 1. Install Dependencies

```bash
# Install test dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt
pip install -r tests/agents/requirements-test.txt
```

## 2. Run Tests Locally

### All Multi-Agent Tests
```bash
pytest tests/agents/ -v
```

### Specific Test Categories
```bash
# Orchestrator tests
pytest tests/agents/test_orchestrator.py -v

# Integration tests
pytest tests/agents/test_integration/ -v

# Scenario tests (with timeout)
pytest tests/agents/test_scenarios/ -v --timeout=120

# Benchmarks
pytest tests/agents/test_scenarios/latency_benchmarks.py -v
```

## 3. Run Cost Analysis

### Benchmark Costs
```bash
python scripts/benchmark_costs.py --output cost_report.json
```

### Compare to Baseline
```bash
python scripts/compare_costs.py cost_report.json --threshold 0.10
```

### View Cost Report
```bash
cat cost_report.json | jq .
```

## 4. Run Performance Checks

### Health Check
```bash
# Check all systems
python scripts/health_check.py all

# Check specific systems
python scripts/health_check.py supabase n8n agents
```

### Generate Performance Dashboard
```bash
# After running benchmarks
python scripts/generate_performance_dashboard.py --metrics performance_metrics.json
```

## 5. Validate Agent Implementation

### Check Agent Code Quality
```bash
# Validate all agents
python scripts/validate_agent_checklist.py

# Validate specific file
python scripts/validate_agent_checklist.py src/agents/my_agent.py

# Strict mode (fail on warnings)
python scripts/validate_agent_checklist.py --strict
```

## 6. Configure Branch Protection

Follow the guide in `docs/BRANCH_PROTECTION.md` to set up required status checks:

1. Go to **Settings** → **Branches** → **Branch protection rules**
2. Add rule for `main` branch
3. Enable required status checks:
   - Multi-Agent Tests / test (3.11)
   - Multi-Agent Tests / test (3.12)
   - Cost Regression Detection / cost-benchmark
   - Agent Code Checklist / checklist
   - CodeQL Analysis / analyze (python)
   - SonarQube / sonarqube
   - CI / quality

## 7. Set Up Repository Secrets

Configure these secrets in **Settings** → **Secrets and variables** → **Actions**:

```
OPENAI_API_KEY          # OpenAI API key for LLM tests
SUPABASE_URL            # Supabase project URL
SUPABASE_KEY            # Supabase API key (anon/service)
N8N_WEBHOOK_URL         # n8n webhook endpoint (optional)
CODECOV_TOKEN           # Codecov upload token (optional)
```

## 8. Monitor Workflows

### View Workflow Status
- Go to **Actions** tab in GitHub
- Filter by workflow name
- Check recent runs

### Review Workflow Artifacts
- Performance metrics
- Cost reports
- Smoke test reports
- Coverage reports

## 9. Customize Thresholds

### Cost Thresholds
Edit `config/cost_baselines.yml`:
```yaml
scenarios:
  loan_analysis:
    baseline_cost: 0.0033  # Adjust based on actual costs
    threshold: 0.10         # 10% increase threshold
```

### Performance Thresholds
Edit `metrics/latency_baseline.yml`:
```yaml
scenarios:
  loan_analysis:
    baseline_p99_ms: 150   # Adjust based on benchmarks
    baseline_success_rate: 98
```

## 10. Troubleshooting

### Tests Failing Locally
```bash
# Check Python version
python --version  # Should be 3.11 or 3.12

# Reinstall dependencies
pip install --upgrade -r requirements.txt

# Clear pytest cache
pytest --cache-clear
```

### Cost Regression False Positives
```bash
# Update baselines after validation
python scripts/benchmark_costs.py --output cost_report.json
# Review the report, then update config/cost_baselines.yml
```

### Performance Regression False Positives
```bash
# Run benchmarks multiple times to get stable baseline
for i in {1..5}; do
  pytest tests/agents/test_scenarios/latency_benchmarks.py
done

# Update metrics/latency_baseline.yml with average values
```

### Health Check Failures
```bash
# Check individual components
python scripts/health_check.py agents     # Should always pass
python scripts/health_check.py supabase  # Requires SUPABASE_URL
python scripts/health_check.py llm       # Requires OPENAI_API_KEY
```

## Common Commands Cheat Sheet

```bash
# Full test suite
pytest tests/agents/ -v --cov=src/agents --cov-report=html

# Quick smoke test
pytest tests/agents/test_scenarios/test_happy_path.py -v

# Cost analysis
python scripts/benchmark_costs.py && python scripts/compare_costs.py cost_report.json

# Performance check
python scripts/health_check.py all

# Validate agent
python scripts/validate_agent_checklist.py src/agents/my_agent.py

# Generate reports
python scripts/generate_performance_dashboard.py --metrics performance_metrics.json
python scripts/post_cost_comment.py cost_report.json
```

## GitHub Workflow Triggers

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| multi-agent-tests.yml | PR to main, push | Run all agent tests |
| cost-regression-detection.yml | PR affecting agents | Detect cost increases |
| agent-checklist-validation.yml | PR affecting agents | Validate implementation |
| smoke-tests.yml | Every 30 min, manual | Health monitoring |
| performance-monitoring.yml | PR, push to main | Track latency |
| codeql.yml | PR, push, weekly | Security scanning |

## Getting Help

- **Documentation**: Check `docs/` directory
- **Examples**: Review existing tests in `tests/agents/`
- **Issues**: Create GitHub issue with `phase-f` label
- **Logs**: Check workflow run logs in Actions tab

## Best Practices

1. **Write tests first** - Add tests before implementing agent logic
2. **Run locally** - Test before pushing to avoid CI failures
3. **Monitor costs** - Review cost reports regularly
4. **Update baselines** - Keep baselines current as system evolves
5. **Review security findings** - Act on CodeQL and SonarQube issues
6. **Document changes** - Update docs when modifying workflows

---

**Quick Start Complete!** You're now ready to use Phase F CI/Quality Gates.

For detailed information, see:
- `docs/PHASE_F_IMPLEMENTATION.md` - Full implementation details
- `docs/BRANCH_PROTECTION.md` - Branch protection guide
- `tests/agents/conftest.py` - Available test fixtures
