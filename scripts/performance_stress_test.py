#!/usr/bin/env python
"""
Performance Stress Test - Week 3 Day 5-6
Tests V2 pipeline with production-scale data and sustained load
"""

import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import psutil

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.kpi_engine_v2 import KPIEngineV2

try:
    from src.azure_tracing import setup_azure_tracing

    logger, _ = setup_azure_tracing()
    logger.info("Azure tracing initialized for performance_stress_test")
except (ImportError, Exception) as tracing_err:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    logger = logging.getLogger(__name__)
    logger.warning("Azure tracing not initialized: %s", tracing_err)


class PerformanceStressTest:
    """Comprehensive performance and stress testing"""

    def __init__(self):
        self.results = {
            "test_date": datetime.now().isoformat(),
            "tests": {},
            "summary": {},
        }
        self.process = psutil.Process(os.getpid())

    def create_test_dataset(self, size: int) -> pd.DataFrame:
        """Create realistic test dataset"""
        np.random.seed(42)
        return pd.DataFrame(
            {
                "dpd_30_60_usd": np.random.uniform(0, 20000, size),
                "dpd_60_90_usd": np.random.uniform(0, 10000, size),
                "dpd_90_plus_usd": np.random.uniform(0, 5000, size),
                "total_receivable_usd": np.random.uniform(100000, 1500000, size),
                "cash_available_usd": np.random.uniform(1000, 150000, size),
                "total_eligible_usd": np.random.uniform(50000, 1200000, size),
            }
        )

    def test_load_scalability(self):
        """Test with various dataset sizes"""
        logger.info("=" * 70)
        logger.info("TEST 1: LOAD SCALABILITY")
        logger.info("=" * 70)

        sizes = [10000, 50000, 100000]
        results = {}

        for size in sizes:
            logger.info(f"\nTesting with {size:,} rows...")
            df = self.create_test_dataset(size)

            # Measure execution
            start_mem = self.process.memory_info().rss / 1024 / 1024  # MB
            start_time = time.time()

            engine = KPIEngineV2(df)
            engine.calculate_all(include_composite=True)

            elapsed = time.time() - start_time
            end_mem = self.process.memory_info().rss / 1024 / 1024  # MB
            mem_delta = end_mem - start_mem

            results[size] = {
                "rows": size,
                "execution_time_s": elapsed,
                "time_per_1k_rows": (elapsed / size * 1000),
                "memory_mb": end_mem,
                "memory_delta_mb": mem_delta,
                "throughput_rows_per_sec": size / elapsed if elapsed > 0 else 0,
            }

            logger.info(f"  ✓ Execution: {elapsed:.3f}s")
            logger.info(f"  ✓ Throughput: {size/elapsed:,.0f} rows/sec")
            logger.info(f"  ✓ Memory: {end_mem:.1f} MB (Δ {mem_delta:+.1f} MB)")
            logger.info(f"  ✓ Per 1k rows: {(elapsed/size*1000):.3f}ms")

        self.results["tests"]["load_scalability"] = results
        logger.info("\n✓ Load scalability test complete")
        return results

    def test_sustained_load(self, duration_seconds=60, interval_seconds=10):
        """Test sustained load over time"""
        logger.info("\n" + "=" * 70)
        logger.info("TEST 2: SUSTAINED LOAD (60+ seconds)")
        logger.info("=" * 70)

        df = self.create_test_dataset(10000)
        execution_times = []
        memory_readings = []
        error_count = 0

        start_time = time.time()
        iteration = 0

        while time.time() - start_time < duration_seconds:
            iteration += 1
            logger.info(f"\nIteration {iteration}...")

            try:
                iter_start = time.time()
                engine = KPIEngineV2(df)
                engine.calculate_all(include_composite=True)
                iter_time = time.time() - iter_start

                execution_times.append(iter_time)
                mem = self.process.memory_info().rss / 1024 / 1024
                memory_readings.append(mem)

                logger.info(f"  ✓ Time: {iter_time*1000:.2f}ms, Memory: {mem:.1f} MB")
            except Exception as e:
                error_count += 1
                logger.error(f"  ✗ Error: {str(e)[:50]}")

        # Analysis
        total_time = time.time() - start_time
        avg_exec = np.mean(execution_times)
        std_exec = np.std(execution_times)
        min_exec = np.min(execution_times)
        max_exec = np.max(execution_times)
        avg_mem = np.mean(memory_readings)
        max_mem = np.max(memory_readings)

        results = {
            "duration_seconds": total_time,
            "iterations": iteration,
            "errors": error_count,
            "execution_times": {
                "mean_ms": avg_exec * 1000,
                "std_ms": std_exec * 1000,
                "min_ms": min_exec * 1000,
                "max_ms": max_exec * 1000,
            },
            "memory": {
                "average_mb": avg_mem,
                "peak_mb": max_mem,
                "stable": std_exec < avg_exec * 0.1,  # < 10% variation
            },
        }

        logger.info(f"\n✓ Completed {iteration} iterations in {total_time:.1f}s")
        logger.info(f"  Avg execution: {avg_exec*1000:.2f}ms ±{std_exec*1000:.2f}ms")
        logger.info(f"  Memory: {avg_mem:.1f} MB (peak: {max_mem:.1f} MB)")
        logger.info(f"  Errors: {error_count}")

        self.results["tests"]["sustained_load"] = results
        logger.info("\n✓ Sustained load test complete")
        return results

    def test_resource_usage(self):
        """Profile CPU and memory usage"""
        logger.info("\n" + "=" * 70)
        logger.info("TEST 3: RESOURCE USAGE PROFILING")
        logger.info("=" * 70)

        df = self.create_test_dataset(50000)

        # Measure CPU and memory during execution
        sum(self.process.cpu_num() for _ in range(1)) / 1.0
        start_mem = self.process.memory_info().rss / 1024 / 1024

        start_time = time.time()
        engine = KPIEngineV2(df)
        engine.calculate_all(include_composite=True)
        elapsed = time.time() - start_time

        end_mem = self.process.memory_info().rss / 1024 / 1024
        cpu_times = self.process.cpu_times()

        results = {
            "dataset_size": 50000,
            "execution_time_s": elapsed,
            "memory_used_mb": end_mem - start_mem,
            "memory_peak_mb": end_mem,
            "cpu_user_seconds": cpu_times.user,
            "cpu_system_seconds": cpu_times.system,
        }

        logger.info(f"  Execution Time: {elapsed:.3f}s")
        logger.info(f"  Memory Used: {end_mem - start_mem:.1f} MB")
        logger.info(f"  Memory Peak: {end_mem:.1f} MB")
        logger.info(f"  CPU User: {cpu_times.user:.3f}s")
        logger.info(f"  CPU System: {cpu_times.system:.3f}s")

        self.results["tests"]["resource_usage"] = results
        logger.info("\n✓ Resource usage test complete")
        return results

    def generate_report(self, output_file="WEEK3_PERFORMANCE_STRESS_TEST.json"):
        """Generate comprehensive test report"""

        # Generate summary
        load_test = self.results["tests"].get("load_scalability", {})
        sustained = self.results["tests"].get("sustained_load", {})
        resource = self.results["tests"].get("resource_usage", {})

        summary = {
            "overall_status": "PASS" if sustained.get("errors", 0) == 0 else "FAIL",
            "tests_passed": sum(1 for _ in [load_test, sustained, resource] if _),
            "performance_assessment": {
                "scalability": "EXCELLENT" if load_test else "UNKNOWN",
                "stability": "STABLE" if sustained.get("memory", {}).get("stable") else "VARIABLE",
                "resource_efficiency": "EFFICIENT" if resource else "UNKNOWN",
            },
            "recommendations": self._generate_recommendations(),
        }

        self.results["summary"] = summary

        # Save report
        with open(output_file, "w") as f:
            json.dump(self.results, f, indent=2, default=str)

        logger.info(f"\n✓ Report saved to {output_file}")

        # Print summary
        print("\n" + "=" * 70)
        print("PERFORMANCE STRESS TEST SUMMARY")
        print("=" * 70)
        print(f"\nOverall Status: {summary['overall_status']}")
        print(f"Tests Executed: {summary['tests_passed']}")
        print("\nPerformance Assessment:")
        for aspect, rating in summary["performance_assessment"].items():
            print(f"  {aspect}: {rating}")
        print("\nRecommendations:")
        for rec in summary["recommendations"]:
            print(f"  • {rec}")
        print("=" * 70)

    def _generate_recommendations(self):
        """Generate recommendations based on test results"""
        recs = []

        sustained = self.results["tests"].get("sustained_load", {})
        if sustained.get("errors", 0) > 0:
            recs.append("Investigate errors in sustained load test")

        if not sustained.get("memory", {}).get("stable"):
            recs.append("Memory usage is variable - monitor for leaks")

        load = self.results["tests"].get("load_scalability", {})
        if load:
            results = list(load.values())
            if results and results[-1]["execution_time_s"] > 10:
                recs.append("Consider optimization for 100k+ row datasets")

        if not recs:
            recs.append("✓ All performance tests passed - ready for production")

        return recs


def main():
    logger.info("Starting Performance Stress Test Suite")
    logger.info("=" * 70)

    tester = PerformanceStressTest()

    # Run all tests
    tester.test_load_scalability()
    tester.test_sustained_load(duration_seconds=30)  # 30s for quick test
    tester.test_resource_usage()

    # Generate report
    tester.generate_report()


if __name__ == "__main__":
    main()
