"""Comprehensive tests for the multi-agent system.

These tests are designed to be discovered and executed by pytest.
Run with: python3 -m pytest python/multi_agent/test_multi_agent_unittest.py -v
"""

import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

from backend.python.multi_agent.guardrails import Guardrails
from backend.python.multi_agent.orchestrator import MultiAgentOrchestrator
from backend.python.multi_agent.protocol import (
    AgentRequest,
    AgentResponse,
    AgentRole,
    Message,
    MessageRole,
    Scenario,
    ScenarioStep,
    Tool,
)
from backend.python.multi_agent.tracing import AgentTracer


class TestProtocol(unittest.TestCase):
    """Test protocol data models."""

    def test_agent_role_enum(self):
        """Test AgentRole enum values."""
        self.assertEqual(AgentRole.RISK_ANALYST.value, "risk_analyst")
        self.assertEqual(AgentRole.GROWTH_STRATEGIST.value, "growth_strategist")
        self.assertEqual(AgentRole.OPS_OPTIMIZER.value, "ops_optimizer")
        self.assertEqual(AgentRole.COMPLIANCE.value, "compliance")

    def test_message_creation(self):
        """Test Message model."""
        msg = Message(role=MessageRole.USER, content="Test message")
        self.assertEqual(msg.role, MessageRole.USER)
        self.assertEqual(msg.content, "Test message")
        self.assertIsInstance(msg.timestamp, datetime)
        self.assertIsInstance(msg.metadata, dict)

    def test_agent_request_validation(self):
        """Test AgentRequest model."""
        msg = Message(role=MessageRole.USER, content="Test")
        request = AgentRequest(
            trace_id="test_123",
            messages=[msg],
            context={"key": "value"},
            max_tokens=1000,
        )
        self.assertEqual(request.trace_id, "test_123")
        self.assertEqual(len(request.messages), 1)
        self.assertEqual(request.max_tokens, 1000)
        self.assertEqual(request.context["key"], "value")

    def test_agent_response_validation(self):
        """Test AgentResponse model."""
        msg = Message(role=MessageRole.ASSISTANT, content="Response")
        response = AgentResponse(
            trace_id="test_123",
            agent_role=AgentRole.RISK_ANALYST,
            message=msg,
            tokens_used=100,
            cost_usd=0.001,
            latency_ms=500.0,
        )
        self.assertEqual(response.trace_id, "test_123")
        self.assertEqual(response.agent_role, AgentRole.RISK_ANALYST)
        self.assertEqual(response.tokens_used, 100)
        self.assertEqual(response.cost_usd, 0.001)

    def test_scenario_validation(self):
        """Test Scenario model."""
        step = ScenarioStep(
            agent_role=AgentRole.RISK_ANALYST,
            prompt_template="Analyze {data}",
            context_keys=["data"],
            output_key="analysis",
        )
        scenario = Scenario(
            name="test_scenario",
            description="Test scenario",
            steps=[step],
        )
        self.assertEqual(scenario.name, "test_scenario")
        self.assertEqual(len(scenario.steps), 1)
        self.assertEqual(scenario.steps[0].agent_role, AgentRole.RISK_ANALYST)

    def test_tool_validation(self):
        """Test Tool model."""
        tool = Tool(
            name="calculate_risk",
            description="Calculate risk metrics",
            parameters={"portfolio": "object"},
            enabled=True,
        )
        self.assertEqual(tool.name, "calculate_risk")
        self.assertTrue(tool.enabled)


class TestGuardrails(unittest.TestCase):
    """Test guardrails functionality."""

    def test_email_redaction(self):
        """Test email PII redaction."""
        text = "Contact me at john.doe@example.com for more info."
        redacted = Guardrails.redact_pii(text)
        self.assertNotIn("john.doe@example.com", redacted)
        self.assertIn("[REDACTED]", redacted)

    def test_ssn_redaction(self):
        """Test SSN redaction."""
        text = "SSN: 123-45-6789"
        redacted = Guardrails.redact_pii(text)
        self.assertNotIn("123-45-6789", redacted)
        self.assertIn("[REDACTED]", redacted)

    def test_phone_redaction(self):
        """Test phone number redaction."""
        text = "Call me at 555-123-4567"
        redacted = Guardrails.redact_pii(text)
        self.assertNotIn("555-123-4567", redacted)
        self.assertIn("[REDACTED]", redacted)

    def test_credit_card_redaction(self):
        """Test credit card redaction."""
        text = "Card: 4532 1234 5678 9010"
        redacted = Guardrails.redact_pii(text)
        self.assertNotIn("4532 1234 5678 9010", redacted)
        self.assertIn("[REDACTED]", redacted)

    def test_multiple_pii_redaction(self):
        """Test multiple PII types in same text."""
        text = "John (SSN: 123-45-6789) email: john@test.com phone: 555-123-4567"
        redacted = Guardrails.redact_pii(text)
        self.assertNotIn("123-45-6789", redacted)
        self.assertNotIn("john@test.com", redacted)
        self.assertNotIn("555-123-4567", redacted)
        self.assertEqual(redacted.count("[REDACTED]"), 3)

    def test_validate_input(self):
        """Test input validation."""
        data = {"key1": "value1", "key2": "value2"}
        self.assertTrue(Guardrails.validate_input(data, ["key1", "key2"]))
        self.assertFalse(Guardrails.validate_input(data, ["key1", "key3"]))

    def test_sanitize_context(self):
        """Test context sanitization."""
        context = {
            "user_email": "john@example.com",
            "ssn": "123-45-6789",
            "nested": {"phone": "555-123-4567"},
            "numbers": [1, 2, 3],
        }
        sanitized = Guardrails.sanitize_context(context)
        self.assertNotIn("john@example.com", str(sanitized))
        self.assertNotIn("123-45-6789", str(sanitized))
        self.assertIn("[REDACTED]", sanitized["user_email"])


class TestTracing(unittest.TestCase):
    """Test tracing functionality."""

    def test_generate_trace_id(self):
        """Test trace ID generation."""
        trace_id = AgentTracer.generate_trace_id()
        self.assertTrue(trace_id.startswith("trace_"))
        self.assertEqual(len(trace_id), 22)  # "trace_" + 16 hex chars

    def test_generate_unique_trace_ids(self):
        """Test trace IDs are unique."""
        id1 = AgentTracer.generate_trace_id()
        id2 = AgentTracer.generate_trace_id()
        self.assertNotEqual(id1, id2)

    def test_cost_tracking(self):
        """Test cost accumulation."""
        tracer = AgentTracer()
        msg = Message(role=MessageRole.ASSISTANT, content="Test")

        response1 = AgentResponse(
            trace_id="test_123",
            agent_role=AgentRole.RISK_ANALYST,
            message=msg,
            tokens_used=100,
            cost_usd=0.001,
            latency_ms=500.0,
        )
        response2 = AgentResponse(
            trace_id="test_123",
            agent_role=AgentRole.COMPLIANCE,
            message=msg,
            tokens_used=150,
            cost_usd=0.002,
            latency_ms=600.0,
        )

        tracer.log_response(response1)
        tracer.log_response(response2)

        self.assertEqual(tracer.get_trace_cost("test_123"), 0.003)
        self.assertEqual(tracer.get_trace_tokens("test_123"), 250)

    def test_reset_trace(self):
        """Test trace reset."""
        tracer = AgentTracer()
        msg = Message(role=MessageRole.ASSISTANT, content="Test")

        response = AgentResponse(
            trace_id="test_123",
            agent_role=AgentRole.RISK_ANALYST,
            message=msg,
            tokens_used=100,
            cost_usd=0.001,
            latency_ms=500.0,
        )

        tracer.log_response(response)
        self.assertEqual(tracer.get_trace_cost("test_123"), 0.001)

        tracer.reset_trace("test_123")
        self.assertEqual(tracer.get_trace_cost("test_123"), 0.0)
        self.assertEqual(tracer.get_trace_tokens("test_123"), 0)


class TestOrchestrator(unittest.TestCase):
    """Test orchestrator functionality."""

    def setUp(self):
        """Set up test fixtures."""
        # Mock environment and OpenAI to avoid actual API calls
        self.env_patcher = patch.dict("os.environ", {"OPENAI_API_KEY": "test_key"})
        self.env_patcher.start()

        self.openai_patcher = patch("backend.python.multi_agent.base_agent.OpenAI")
        self.mock_openai = self.openai_patcher.start()
        self.mock_openai.return_value = MagicMock()

    def tearDown(self):
        """Tear down test fixtures."""
        self.env_patcher.stop()
        self.openai_patcher.stop()

    def test_orchestrator_initialization(self):
        """Test orchestrator initializes with all agents."""
        orchestrator = MultiAgentOrchestrator()
        self.assertIn(AgentRole.RISK_ANALYST, orchestrator.agents)
        self.assertIn(AgentRole.GROWTH_STRATEGIST, orchestrator.agents)
        self.assertIn(AgentRole.OPS_OPTIMIZER, orchestrator.agents)
        self.assertIn(AgentRole.COMPLIANCE, orchestrator.agents)

    def test_list_scenarios(self):
        """Test listing available scenarios."""
        orchestrator = MultiAgentOrchestrator()
        scenarios = orchestrator.list_scenarios()
        self.assertIn("loan_risk_review", scenarios)
        self.assertIn("growth_strategy", scenarios)
        self.assertIn("portfolio_optimization", scenarios)

    def test_get_scenario(self):
        """Test getting scenario by name."""
        orchestrator = MultiAgentOrchestrator()
        scenario = orchestrator.get_scenario("loan_risk_review")
        self.assertIsNotNone(scenario)
        self.assertEqual(scenario.name, "loan_risk_review")
        self.assertGreater(len(scenario.steps), 0)

    def test_add_custom_scenario(self):
        """Test adding custom scenario."""
        orchestrator = MultiAgentOrchestrator()

        custom_scenario = Scenario(
            name="custom_test",
            description="Test scenario",
            steps=[
                ScenarioStep(
                    agent_role=AgentRole.RISK_ANALYST,
                    prompt_template="Test {data}",
                    context_keys=["data"],
                    output_key="result",
                )
            ],
        )

        orchestrator.add_scenario(custom_scenario)
        self.assertIn("custom_test", orchestrator.list_scenarios())
        retrieved = orchestrator.get_scenario("custom_test")
        self.assertEqual(retrieved.name, "custom_test")
