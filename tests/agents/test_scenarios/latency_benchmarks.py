import concurrent.futures
import time
import pytest
from backend.src.agents.monitoring import PerformanceTracker

class TestLatencyBenchmarks:

    def setup_method(self):
        self.tracker = PerformanceTracker()

    @pytest.mark.benchmark
    def test_loan_analysis_latency(self):
        start = time.time()
        time.sleep(0.05)
        duration_ms = (time.time() - start) * 1000
        self.tracker.track_scenario_latency('loan_analysis', duration_ms)
        assert duration_ms < 200, f'Latency {duration_ms:.2f}ms exceeds 200ms threshold'

    @pytest.mark.benchmark
    def test_risk_assessment_latency(self):
        start = time.time()
        time.sleep(0.03)
        duration_ms = (time.time() - start) * 1000
        self.tracker.track_scenario_latency('risk_assessment', duration_ms)
        assert duration_ms < 100, f'Latency {duration_ms:.2f}ms exceeds 100ms threshold'

    @pytest.mark.benchmark
    def test_portfolio_validation_latency(self):
        start = time.time()
        time.sleep(0.02)
        duration_ms = (time.time() - start) * 1000
        self.tracker.track_scenario_latency('portfolio_validation', duration_ms)
        assert duration_ms < 50, f'Latency {duration_ms:.2f}ms exceeds 50ms threshold'

    @pytest.mark.benchmark
    @pytest.mark.timeout(5)
    def test_multi_agent_coordination_latency(self):
        start = time.time()
        time.sleep(0.08)
        duration_ms = (time.time() - start) * 1000
        self.tracker.track_scenario_latency('multi_agent_coordination', duration_ms)
        assert duration_ms < 200, f'Latency {duration_ms:.2f}ms exceeds 200ms threshold'

    def test_performance_percentiles(self):
        for i in range(100):
            duration = 50 + i % 10 * 5
            self.tracker.track_scenario_latency('test_scenario', duration)
        stats = self.tracker.get_scenario_performance('test_scenario')
        assert stats['total_executions'] == 100
        assert stats['latency']['p50'] > 0
        assert stats['latency']['p95'] >= stats['latency']['p50']
        assert stats['latency']['p99'] >= stats['latency']['p95']
        assert stats['latency']['p99'] < 200

    @pytest.mark.timeout(10)
    def test_concurrent_agent_latency(self):

        def agent_task(agent_id):
            start = time.time()
            time.sleep(0.05)
            duration_ms = (time.time() - start) * 1000
            self.tracker.track_agent_latency(f'agent_{agent_id}', duration_ms)
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(agent_task, i) for i in range(10)]
            concurrent.futures.wait(futures)
        for i in range(10):
            stats = self.tracker.get_agent_performance(f'agent_{i}')
            avg_latency = stats['latency']['avg']
            assert avg_latency < 200, f'Agent {i} average latency {avg_latency:.2f}ms exceeds threshold'
