#!/usr/bin/env python
"""
24-Hour Monitoring Checkpoint Tracker
Executes validation and records metrics for each checkpoint
"""

import sys
import os
import json
import subprocess
import time
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, '/Users/jenineferderas/Documents/abaco-loans-analytics')


class MonitoringCheckpoint:
    """Track and record checkpoint metrics"""
    
    def __init__(self, checkpoint_hour: int = None):
        self.checkpoint_hour = checkpoint_hour or self._current_hour()
        self.start_time = datetime.now()
        self.metrics = {
            "checkpoint_hour": self.checkpoint_hour,
            "timestamp": self.start_time.isoformat(),
            "validation": None,
            "system_metrics": None,
            "status": "PENDING"
        }
    
    def _current_hour(self) -> int:
        """Calculate hours since cutover (01:58:46 UTC)"""
        cutover_time = datetime(2025, 12, 26, 1, 58, 46)
        now = datetime.utcnow()
        hours = int((now - cutover_time).total_seconds() / 3600)
        return max(0, hours)
    
    def _get_system_metrics(self) -> dict:
        """Gather system resource metrics"""
        try:
            import psutil
            
            process = psutil.Process()
            memory_info = process.memory_info()
            
            return {
                "memory_rss_mb": memory_info.rss / (1024 * 1024),
                "memory_vms_mb": memory_info.vms / (1024 * 1024),
                "cpu_percent": process.cpu_percent(interval=0.1),
                "num_threads": process.num_threads(),
            }
        except Exception as e:
            return {"error": str(e)}
    
    def run_validation(self) -> dict:
        """Execute production validation script"""
        try:
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/production_validation.py"
                ],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            validation_report_path = Path("production_validation_report.json")
            if validation_report_path.exists():
                with open(validation_report_path) as f:
                    return json.load(f)
            else:
                return {"status": "FAIL", "error": "No validation report generated"}
                
        except subprocess.TimeoutExpired:
            return {"status": "FAIL", "error": "Validation script timeout"}
        except Exception as e:
            return {"status": "FAIL", "error": str(e)}
    
    def execute(self) -> dict:
        """Execute checkpoint validation and collect metrics"""
        print(f"\n{'='*80}")
        print(f"CHECKPOINT: Hour {self.checkpoint_hour}")
        print(f"Timestamp: {self.start_time.isoformat()}")
        print(f"{'='*80}\n")
        
        print("Running validation suite...")
        self.metrics["validation"] = self.run_validation()
        validation_status = self.metrics["validation"].get("status", "UNKNOWN")
        print(f"Validation Status: {validation_status}")
        
        print("\nCollecting system metrics...")
        self.metrics["system_metrics"] = self._get_system_metrics()
        if "error" not in self.metrics["system_metrics"]:
            print(f"  Memory: {self.metrics['system_metrics']['memory_rss_mb']:.1f} MB")
            print(f"  CPU: {self.metrics['system_metrics']['cpu_percent']:.1f}%")
        
        self.metrics["status"] = validation_status
        self.metrics["duration_seconds"] = (datetime.now() - self.start_time).total_seconds()
        
        return self.metrics
    
    def save_checkpoint(self, output_dir: str = "logs/monitoring") -> str:
        """Save checkpoint results to file"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        checkpoint_file = output_path / f"checkpoint_hour_{self.checkpoint_hour:02d}.json"
        with open(checkpoint_file, 'w') as f:
            json.dump(self.metrics, f, indent=2)
        
        return str(checkpoint_file)
    
    def print_summary(self):
        """Print checkpoint summary"""
        print(f"\n{'─'*80}")
        print(f"CHECKPOINT SUMMARY - Hour {self.checkpoint_hour}")
        print(f"{'─'*80}")
        
        print(f"\nValidation Status: {self.metrics['validation'].get('status', 'UNKNOWN')}")
        
        if self.metrics['validation'].get('checks'):
            print("\nValidation Checks:")
            for check_name, check_result in self.metrics['validation']['checks'].items():
                status = check_result.get('status', 'UNKNOWN')
                print(f"  ✓ {check_name}: {status}")
        
        if self.metrics['system_metrics'] and 'error' not in self.metrics['system_metrics']:
            print("\nSystem Metrics:")
            metrics = self.metrics['system_metrics']
            print(f"  Memory: {metrics['memory_rss_mb']:.1f} MB (threshold: 200 MB)")
            print(f"  CPU: {metrics['cpu_percent']:.1f}% (threshold: 80%)")
            print(f"  Threads: {metrics['num_threads']}")
        
        if self.metrics['validation'].get('checks', {}).get('performance'):
            perf = self.metrics['validation']['checks']['performance'].get('metrics', {})
            print(f"\nPerformance:")
            print(f"  Latency: {perf.get('latency_ms', 'N/A')} ms (threshold: 100 ms)")
            print(f"  Throughput: {perf.get('throughput_rows_per_sec', 'N/A')} rows/sec")
        
        print(f"\nDuration: {self.metrics['duration_seconds']:.2f} seconds")
        print(f"{'─'*80}\n")


def main():
    checkpoint = MonitoringCheckpoint()
    results = checkpoint.execute()
    checkpoint_file = checkpoint.save_checkpoint()
    checkpoint.print_summary()
    
    print(f"Checkpoint saved: {checkpoint_file}")
    
    return 0 if results['status'] == 'PASS' else 1


if __name__ == '__main__':
    sys.exit(main())
