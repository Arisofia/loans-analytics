"""Run pipeline and save output to file."""
import sys
import os
import io

sys.path.insert(0, ".")
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

# Capture both stdout and stderr
import contextlib

output = io.StringIO()

try:
    with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
        from backend.src.pipeline.orchestrator import UnifiedPipeline
        pipeline = UnifiedPipeline()
        results = pipeline.execute(mode="full")
except Exception as e:
    output.write(f"\nEXCEPTION: {e}\n")
    results = {"status": "error", "error": str(e), "phases": {}}

# Write results to file 
with open("_pipeline_result.txt", "w") as f:
    f.write(f"Status: {results.get('status', 'unknown')}\n")
    f.write(f"Run ID: {results.get('run_id', 'N/A')}\n")
    f.write(f"Duration: {results.get('duration_seconds', 0):.2f}s\n")
    f.write(f"Error: {results.get('error', 'None')}\n")
    f.write("\nPhase Results:\n")
    for name, phase in results.get("phases", {}).items():
        f.write(f"  {name}: {phase.get('status', 'unknown')}\n")
    
    # KPI count
    kpi_results = results.get("phases", {}).get("calculation", {}).get("kpi_results", {})
    f.write(f"\nKPI Results count: {len(kpi_results)}\n")
    
    if kpi_results:
        f.write("\nKPI Values:\n")
        for kpi_name, kpi_data in sorted(kpi_results.items()):
            if isinstance(kpi_data, dict):
                val = kpi_data.get("value", kpi_data.get("kpi_value", "?"))
            else:
                val = kpi_data
            f.write(f"  {kpi_name}: {val}\n")
    
    f.write("\n--- Captured Output ---\n")
    f.write(output.getvalue()[-2000:] if len(output.getvalue()) > 2000 else output.getvalue())

print(f"Status: {results.get('status')}")
print(f"Run ID: {results.get('run_id', 'N/A')}")
print(f"Output saved to _pipeline_result.txt")
