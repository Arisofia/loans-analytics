# Chaos Toolkit Experiments

This folder contains Chaos Toolkit experiments to validate resilience.

## How to run locally

1. Install Chaos Toolkit (`pip install chaostoolkit`).
2. Export target endpoint and baseline latency if needed:
   ```bash
   export CHAOS_TARGET_URL=https://example.com/health
   export CHAOS_BASELINE_MS=400
   ```
3. Run an experiment:
   ```bash
   chaostoolkit run experiments/latency-experiment.json
   ```
4. Review the `journal.json` output for steady-state and rollback results.

## Available experiments

- `latency-experiment.json`: Injects latency on the target dependency and validates the system still responds within the tolerated window or triggers alerting.
