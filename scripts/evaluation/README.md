# Evaluation Scripts

Automated testing and evaluation utilities for ML models and system components.

## Scripts

### `check_thresholds.py`

Validates evaluation metrics against configured quality thresholds.

**Usage:**

```bash
python scripts/evaluation/check_thresholds.py \
  --metrics-file reports/evaluation-metrics.json \
  --config config/evaluation-thresholds.yml \
  --output threshold-results.json
```

**Purpose:**

- Ensures test pass rates meet fintech compliance standards (>95%)
- Validates ML model performance metrics (accuracy, precision, recall, F1)
- Fails CI pipeline if hard thresholds not met
- Issues warnings for soft target misses

**Configuration:**
See `config/evaluation-thresholds.yml` for threshold definitions.

### `generate_visualizations.py`

Creates charts and visualizations from evaluation metrics.

**Usage:**

```bash
python scripts/evaluation/generate_visualizations.py \
  --metrics-file reports/evaluation-metrics.json \
  --output-dir reports/visualizations/
```

**Generates:**

- Test pass/fail summary bar chart (`test_summary.png`)
- Test duration distribution chart (`test_durations.png`)
- Coverage reports (planned)

**Requirements:**

- `matplotlib` (optional, gracefully degrades if not installed)

## Integration with CI/CD

These scripts are called by `.github/workflows/model_evaluation.yml`:

1. **Pytest runs** → generates `reports/evaluation-metrics.json`
2. **Visualizations** → `generate_visualizations.py` creates charts
3. **Threshold check** → `check_thresholds.py` validates quality gates
4. **Artifacts uploaded** → reports available in GitHub Actions

## Development

### Adding New Metrics

To add custom metrics to threshold checking:

1. Update `config/evaluation-thresholds.yml` with new metric thresholds
2. Ensure your test generates metrics in pytest JSON report format
3. Metrics will be automatically validated by `check_thresholds.py`

### Adding New Visualizations

To add new charts:

1. Add a function in `generate_visualizations.py` (e.g., `generate_custom_chart()`)
2. Call it from `main()` function
3. Follow matplotlib best practices (use `Agg` backend for CI)

## Error Handling

All scripts:

- Use structured logging via `python.logging_config.get_logger()`
- Exit with code 0 on success, 1 on failure
- Degrade gracefully when optional dependencies missing (matplotlib)
- Validate input files before processing

## Fintech Compliance

Threshold configurations enforce:

- **95% minimum test coverage** (regulatory requirement)
- **High model accuracy** (>95% for production deployment)
- **Balanced precision/recall** (risk management)
- **Performance transparency** (all metrics tracked and visualized)

Adjust thresholds in `config/evaluation-thresholds.yml` based on:

- Regulatory requirements
- Business impact of false positives/negatives
- Model maturity and dataset quality
