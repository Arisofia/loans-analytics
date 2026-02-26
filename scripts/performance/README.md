# Performance Scripts

## KPI cProfile

```bash
python3 scripts/performance/profile_kpi_engine.py --rows 1000000
```

Outputs:

- `logs/performance/kpi_engine_profile.stats`
- `logs/performance/kpi_engine_profile_summary.json`

## KPI Scale Benchmark

```bash
python3 scripts/performance/benchmark_kpi_engine_scale.py \
  --rows 100000,500000,1000000 \
  --mode both \
  --target-seconds 5
```

Output:

- `logs/performance/kpi_engine_scale_benchmark.json`

## API Load Test (Locust)

```bash
locust -f tests/load/locustfile.py --headless -u 30 -r 5 -t 5m --host http://localhost:8000
```

Optional auth:

```bash
export ABACO_BEARER_TOKEN="<jwt>"
```
