"""Tests for historical context integration in the multi-agent orchestrator."""

import unittest
from unittest.mock import MagicMock, patch

from python.multi_agent.orchestrator import MultiAgentOrchestrator
from python.multi_agent.protocol import AgentResponse, AgentRole, Message, MessageRole


class TestOrchestratorHistoricalIntegration(unittest.TestCase):
    """Validate G5 historical context integration behavior."""

    @staticmethod
    def _response(role: AgentRole, trace_id: str, content: str) -> AgentResponse:
        """Create a synthetic agent response."""
        return AgentResponse(
            trace_id=trace_id,
            agent_role=role,
            message=Message(role=MessageRole.ASSISTANT, content=content),
            tokens_used=90,
            cost_usd=0.0015,
            latency_ms=25.0,
        )

    @patch("python.multi_agent.base_agent.BaseAgent._init_client")
    def test_auto_enriches_and_injects_historical_context(self, mock_init_client):
        """Orchestrator should derive historical context from KPI IDs automatically."""
        mock_init_client.return_value = MagicMock()
        provider = MagicMock()
        provider.agent_summary.return_value = {
            "kpi_id": "par_30",
            "trend": {"direction": "decreasing", "strength": "moderate"},
            "moving_average_30d": 2.4,
            "recent_change_point": None,
        }

        orchestrator = MultiAgentOrchestrator(historical_context_provider=provider)

        captured: dict = {}

        def make_process(role: AgentRole):
            def _process(request):
                if role == AgentRole.RISK_ANALYST:
                    captured["prompt"] = request.messages[0].content
                    captured["context"] = request.context
                return self._response(
                    role=role,
                    trace_id=request.trace_id,
                    content=f"{role.value} response",
                )

            return _process

        for role, agent in orchestrator.agents.items():
            agent.process = MagicMock(side_effect=make_process(role))

        orchestrator.run_scenario(
            scenario_name="loan_risk_review",
            initial_context={"portfolio_data": "sample portfolio", "kpi_id": "par_30"},
            trace_id="trace_hist_auto",
        )

        provider.agent_summary.assert_called_once_with("par_30", periods=12)
        self.assertIn("Historical context (auto-injected):", captured["prompt"])
        self.assertIn("historical_context", captured["context"])
        self.assertIn("historical_trends", captured["context"])

    @patch("python.multi_agent.base_agent.BaseAgent._init_client")
    def test_preserves_explicit_historical_context(self, mock_init_client):
        """Explicit historical context should not be overridden by provider lookups."""
        mock_init_client.return_value = MagicMock()
        provider = MagicMock()

        orchestrator = MultiAgentOrchestrator(historical_context_provider=provider)

        explicit_historical_context = {
            "kpi_id": "par_30",
            "trend": {"direction": "stable", "strength": "weak"},
        }
        explicit_historical_trends = {"direction": "stable", "strength": "weak"}

        captured: dict = {}

        def make_process(role: AgentRole):
            def _process(request):
                if role == AgentRole.RISK_ANALYST:
                    captured["prompt"] = request.messages[0].content
                return self._response(
                    role=role,
                    trace_id=request.trace_id,
                    content=f"{role.value} response",
                )

            return _process

        for role, agent in orchestrator.agents.items():
            agent.process = MagicMock(side_effect=make_process(role))

        orchestrator.run_scenario(
            scenario_name="loan_risk_review",
            initial_context={
                "portfolio_data": "sample portfolio",
                "historical_context": explicit_historical_context,
                "historical_trends": explicit_historical_trends,
            },
            trace_id="trace_hist_explicit",
        )

        provider.agent_summary.assert_not_called()
        self.assertIn("Historical context (auto-injected):", captured["prompt"])
        self.assertIn("stable", captured["prompt"])


if __name__ == "__main__":
    unittest.main()
