"""
Supabase load testing script.

Tests connection pool performance at 3× current volume to identify bottlenecks
before production scaling from $7.4M to $16.3M AUM.
"""

import asyncio
import os
import statistics
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from python.supabase_pool import SupabaseConnectionPool


@dataclass
class LoadTestResult:
    """Results from a single load test run."""

    test_name: str
    total_queries: int
    successful_queries: int
    failed_queries: int
    duration_seconds: float
    queries_per_second: float
    avg_latency_ms: float
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    pool_metrics: dict


async def execute_query_batch(
    pool: SupabaseConnectionPool, query: str, batch_size: int, latencies: List[float]
) -> tuple[int, int]:
    """
    Execute a batch of queries concurrently.

    Args:
        pool: Connection pool
        query: SQL query to execute
        batch_size: Number of concurrent queries
        latencies: List to append latencies to

    Returns:
        (successful_count, failed_count)
    """

    async def _execute_single():
        start = time.perf_counter()
        try:
            await pool.fetchrow(query)
            latencies.append((time.perf_counter() - start) * 1000)  # ms
            return True
        except Exception as e:
            print(f"Query failed: {e}")
            return False

    results = await asyncio.gather(*[_execute_single() for _ in range(batch_size)])
    successful = sum(1 for r in results if r)
    failed = len(results) - successful
    return successful, failed


async def run_load_test(
    database_url: str,
    test_name: str,
    query: str,
    total_queries: int,
    concurrent_queries: int,
    pool_config: dict,
) -> LoadTestResult:
    """
    Run a load test scenario.

    Args:
        database_url: Supabase connection string
        test_name: Test scenario name
        query: SQL query to test
        total_queries: Total number of queries to execute
        concurrent_queries: Number of concurrent queries per batch
        pool_config: Pool configuration overrides

    Returns:
        Load test results
    """
    print(f"\n{'='*80}")
    print(f"🚀 Load Test: {test_name}")
    print(f"{'='*80}")
    print(f"Total queries: {total_queries:,}")
    print(f"Concurrent: {concurrent_queries}")
    print(f"Pool config: {pool_config}")
    print(f"Query: {query[:100]}...")

    # Initialize pool
    pool = SupabaseConnectionPool(database_url, **pool_config)
    await pool.initialize()

    latencies: List[float] = []
    successful = 0
    failed = 0

    start_time = time.perf_counter()

    # Execute queries in batches
    num_batches = total_queries // concurrent_queries
    for batch_num in range(num_batches):
        batch_success, batch_failed = await execute_query_batch(
            pool, query, concurrent_queries, latencies
        )
        successful += batch_success
        failed += batch_failed

        if (batch_num + 1) % 10 == 0:
            elapsed = time.perf_counter() - start_time
            qps = successful / elapsed
            print(
                f"  Batch {batch_num + 1}/{num_batches}: "
                f"{successful:,} queries ({qps:.1f} qps, "
                f"{failed} failures)"
            )

    duration = time.perf_counter() - start_time

    # Calculate statistics
    qps = successful / duration if duration > 0 else 0
    avg_latency = statistics.mean(latencies) if latencies else 0
    sorted_latencies = sorted(latencies)

    def percentile(data: List[float], p: float) -> float:
        if not data:
            return 0.0
        k = (len(data) - 1) * p
        f = int(k)
        c = f + 1
        if c >= len(data):
            return data[-1]
        return data[f] + (k - f) * (data[c] - data[f])

    p50 = percentile(sorted_latencies, 0.50)
    p95 = percentile(sorted_latencies, 0.95)
    p99 = percentile(sorted_latencies, 0.99)

    pool_metrics = pool.get_metrics()

    # Cleanup
    await pool.close()

    result = LoadTestResult(
        test_name=test_name,
        total_queries=total_queries,
        successful_queries=successful,
        failed_queries=failed,
        duration_seconds=duration,
        queries_per_second=qps,
        avg_latency_ms=avg_latency,
        p50_latency_ms=p50,
        p95_latency_ms=p95,
        p99_latency_ms=p99,
        pool_metrics=pool_metrics,
    )

    print("\n📊 Results:")
    print(f"  Duration: {duration:.2f}s")
    print(f"  Successful: {successful:,}/{total_queries:,} ({successful/total_queries*100:.1f}%)")
    print(f"  Failed: {failed:,}")
    print(f"  QPS: {qps:.1f}")
    print(f"  Latency (avg): {avg_latency:.2f}ms")
    print(f"  Latency (p50): {p50:.2f}ms")
    print(f"  Latency (p95): {p95:.2f}ms")
    print(f"  Latency (p99): {p99:.2f}ms")
    print(f"  Pool metrics: {pool_metrics}")

    return result


async def main():
    """Run comprehensive load tests."""
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                   SUPABASE LOAD TEST - 3× VOLUME SIMULATION                  ║
║                                                                              ║
║  Simulating growth from $7.4M → $16.3M AUM (2.2× growth)                   ║
║  Testing connection pool performance under 3× current query volume          ║
╚══════════════════════════════════════════════════════════════════════════════╝
""")

    # Load database URL from environment
    database_url = os.getenv("SUPABASE_DATABASE_URL")
    if not database_url:
        database_url = os.getenv("DATABASE_URL")

    if not database_url:
        print("❌ ERROR: SUPABASE_DATABASE_URL or DATABASE_URL environment variable required")
        print("\nExample:")
        print('  export SUPABASE_DATABASE_URL="postgresql://user:pass@host:5432/dbname"')
        return

    # Test scenarios
    scenarios = [
        {
            "name": "Baseline - Current Volume",
            "query": "SELECT COUNT(*) FROM fact_loans",
            "total_queries": 300,
            "concurrent": 5,
            "pool_config": {"min_size": 2, "max_size": 5},
        },
        {
            "name": "3× Volume - Small Pool",
            "query": "SELECT COUNT(*) FROM fact_loans",
            "total_queries": 900,
            "concurrent": 15,
            "pool_config": {"min_size": 2, "max_size": 5},
        },
        {
            "name": "3× Volume - Medium Pool",
            "query": "SELECT COUNT(*) FROM fact_loans",
            "total_queries": 900,
            "concurrent": 15,
            "pool_config": {"min_size": 5, "max_size": 10},
        },
        {
            "name": "3× Volume - Large Pool",
            "query": "SELECT COUNT(*) FROM fact_loans",
            "total_queries": 900,
            "concurrent": 15,
            "pool_config": {"min_size": 10, "max_size": 20},
        },
        {
            "name": "Complex Query - 3× Volume",
            "query": """
                SELECT
                    loan_status,
                    COUNT(*) as count,
                    SUM(principal_balance) as total_balance
                FROM fact_loans
                GROUP BY loan_status
            """,
            "total_queries": 900,
            "concurrent": 15,
            "pool_config": {"min_size": 5, "max_size": 10},
        },
        {
            "name": "Peak Load - 5× Volume",
            "query": "SELECT COUNT(*) FROM fact_loans",
            "total_queries": 1500,
            "concurrent": 25,
            "pool_config": {"min_size": 10, "max_size": 20},
        },
    ]

    results: List[LoadTestResult] = []

    for scenario in scenarios:
        try:
            result = await run_load_test(
                database_url=database_url,
                test_name=scenario["name"],
                query=scenario["query"],
                total_queries=scenario["total_queries"],
                concurrent_queries=scenario["concurrent"],
                pool_config=scenario["pool_config"],
            )
            results.append(result)

            # Cool-down period between tests
            print("\n⏳ Cooling down for 5 seconds...")
            await asyncio.sleep(5)

        except Exception as e:
            print(f"\n❌ Test failed: {e}")
            import traceback

            traceback.print_exc()

    # Summary report
    print(f"\n\n{'='*80}")
    print("📈 LOAD TEST SUMMARY")
    print(f"{'='*80}\n")

    print(f"{'Test Name':<40} {'QPS':>10} {'P95 (ms)':>12} {'Success %':>12}")
    print("-" * 80)

    for result in results:
        success_pct = (
            (result.successful_queries / result.total_queries * 100)
            if result.total_queries > 0
            else 0
        )
        print(
            f"{result.test_name:<40} {result.queries_per_second:>10.1f} {result.p95_latency_ms:>12.2f} {success_pct:>11.1f}%"
        )

    # Recommendations
    print(f"\n{'='*80}")
    print("💡 RECOMMENDATIONS")
    print(f"{'='*80}\n")

    baseline = results[0] if results else None
    peak_3x = [r for r in results if "3× Volume" in r.test_name and "Medium Pool" in r.test_name]
    peak_3x = peak_3x[0] if peak_3x else None

    if baseline and peak_3x:
        latency_increase = (peak_3x.p95_latency_ms / baseline.p95_latency_ms - 1) * 100

        print("1. Pool Size:")
        if latency_increase < 50:
            print("   ✅ Medium pool (5-10 connections) handles 3× load well")
            print(f"      P95 latency increase: {latency_increase:.1f}%")
        else:
            print("   ⚠️  Consider larger pool for production")
            print(f"      P95 latency increase: {latency_increase:.1f}%")

        print("\n2. Performance Targets:")
        print(f"   Current QPS: {baseline.queries_per_second:.1f}")
        print(f"   3× Volume QPS: {peak_3x.queries_per_second:.1f}")
        print("   Recommended pool: min_size=5, max_size=15")

        print("\n3. Monitoring:")
        print("   Track P95 latency < 100ms")
        print("   Alert on query failure rate > 1%")
        print("   Monitor pool utilization > 80%")

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"data/metrics/load_test_{timestamp}.json"

    import json
    # Path already imported at module level (line 15)

    Path("data/metrics").mkdir(parents=True, exist_ok=True)

    with open(output_file, "w") as f:
        json.dump(
            [
                {
                    "test_name": r.test_name,
                    "total_queries": r.total_queries,
                    "successful_queries": r.successful_queries,
                    "failed_queries": r.failed_queries,
                    "duration_seconds": r.duration_seconds,
                    "queries_per_second": r.queries_per_second,
                    "avg_latency_ms": r.avg_latency_ms,
                    "p50_latency_ms": r.p50_latency_ms,
                    "p95_latency_ms": r.p95_latency_ms,
                    "p99_latency_ms": r.p99_latency_ms,
                    "pool_metrics": r.pool_metrics,
                }
                for r in results
            ],
            f,
            indent=2,
        )

    print(f"\n💾 Results saved to: {output_file}")


if __name__ == "__main__":
    asyncio.run(main())
