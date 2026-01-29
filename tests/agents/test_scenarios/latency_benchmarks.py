"""Latency benchmarks for agent scenarios.

Tests p50, p95, p99 latency for various agent operations.
"""

import time

import pytest

import pytest

from src.agents.monitoring import PerformanceTracker


class TestLatencyBenchmarks:
    """Latency benchmark tests for agent scenarios."""

    def setup_method(self):
        """Set up performance tracker for each test."""
        self.tracker = PerformanceTracker()

    @pytest.mark.benchmark
    def test_loan_analysis_latency(self, benchmark):
        """Benchmark loan analysis scenario latency."""

        def loan_analysis():
            """Simulated loan analysis."""
            start = time.time()
            # Simulate agent work
            time.sleep(0.05)  # 50ms simulated work
            duration_ms = (time.time() - start) * 1000
            self.tracker.track_scenario_latency("loan_analysis", duration_ms)
            return duration_ms

        result = benchmark(loan_analysis)
        assert result < 200, f"Latency {result:.2f}ms exceeds 200ms threshold"

    @pytest.mark.benchmark
    def test_risk_assessment_latency(self, benchmark):
        """Benchmark risk assessment scenario latency."""

        def risk_assessment():
            """Simulated risk assessment."""
            start = time.time()
            time.sleep(0.03)  # 30ms simulated work
            duration_ms = (time.time() - start) * 1000
            self.tracker.track_scenario_latency("risk_assessment", duration_ms)
            return duration_ms

        result = benchmark(risk_assessment)
        assert result < 100, f"Latency {result:.2f}ms exceeds 100ms threshold"

    @pytest.mark.benchmark
    def test_portfolio_validation_latency(self, benchmark):
        """Benchmark portfolio validation scenario latency."""

        def portfolio_validation():
            """Simulated portfolio validation."""
            start = time.time()
            time.sleep(0.02)  # 20ms simulated work
            duration_ms = (time.time() - start) * 1000
            self.tracker.track_scenario_latency("portfolio_validation", duration_ms)
            return duration_ms

        result = benchmark(portfolio_validation)
        assert result < 50, f"Latency {result:.2f}ms exceeds 50ms threshold"

    @pytest.mark.benchmark
    @pytest.mark.timeout(5)
    def test_multi_agent_coordination_latency(self, benchmark):
        """Benchmark multi-agent coordination latency."""

        def multi_agent_coordination():
            """Simulated multi-agent coordination."""
            start = time.time()
            # Simulate multiple agents
            time.sleep(0.08)  # 80ms simulated work
            duration_ms = (time.time() - start) * 1000
            self.tracker.track_scenario_latency("multi_agent_coordination", duration_ms)
            return duration_ms

        result = benchmark(multi_agent_coordination)
        assert result < 200, f"Latency {result:.2f}ms exceeds 200ms threshold"

    def test_performance_percentiles(self):
        """Test performance percentile calculations."""
        # Simulate multiple executions
        for i in range(100):
            duration = 50 + (i % 10) * 5  # Varies from 50-100ms
            self.tracker.track_scenario_latency("test_scenario", duration)

        stats = self.tracker.get_scenario_performance("test_scenario")

        assert stats["total_executions"] == 100
        assert stats["latency"]["p50"] > 0
        assert stats["latency"]["p95"] > stats["latency"]["p50"]
        assert stats["latency"]["p99"] > stats["latency"]["p95"]
        assert stats["latency"]["p99"] < 200  # Within threshold

    @pytest.mark.timeout(10)
    def test_concurrent_agent_latency(self):
        """Test latency under concurrent agent execution."""
        import concurrent.futures

        def agent_task(agent_id):
            """Simulate agent task."""
            start = time.time()
            time.sleep(0.05)
            duration_ms = (time.time() - start) * 1000
            self.tracker.track_agent_latency(f"agent_{agent_id}", duration_ms)

        # Run 10 agents concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(agent_task, i) for i in range(10)]
            concurrent.futures.wait(futures)

        # Check that concurrent execution didn't cause excessive latency
        for i in range(10):
            stats = self.tracker.get_agent_performance(f"agent_{i}")
            avg_latency = stats["latency"]["avg"]
            assert (
                avg_latency < 200
            ), f"Agent {i} average latency {avg_latency:.2f}ms exceeds threshold"
