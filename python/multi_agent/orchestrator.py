"""Multi-agent orchestrator with scenario support."""

import logging
from typing import Any, Dict, List, Optional

from .agents import ComplianceAgent, GrowthStrategistAgent, OpsOptimizerAgent, RiskAnalystAgent
from .base_agent import BaseAgent
from .protocol import (
    AgentRequest,
    AgentResponse,
    AgentRole,
    LLMProvider,
    Message,
    MessageRole,
    Scenario,
    ScenarioStep,
)
from .tracing import AgentTracer

logger = logging.getLogger(__name__)


class MultiAgentOrchestrator:
    """Orchestrates multi-agent workflows with scenario support."""

    def __init__(
        self,
        provider: LLMProvider = LLMProvider.OPENAI,
        enable_tracing: bool = False,
    ):
        """Initialize orchestrator.

        Args:
            provider: Default LLM provider for all agents
            enable_tracing: Enable OpenTelemetry tracing
        """
        self.provider = provider
        self.tracer = AgentTracer(enable_otel=enable_tracing)
        self.agents = self._init_agents()
        self.scenarios = self._init_scenarios()

    def _init_agents(self) -> Dict[AgentRole, BaseAgent]:
        """Initialize all role-specific agents."""
        return {
            AgentRole.RISK_ANALYST: RiskAnalystAgent(provider=self.provider, tracer=self.tracer),
            AgentRole.GROWTH_STRATEGIST: GrowthStrategistAgent(
                provider=self.provider, tracer=self.tracer
            ),
            AgentRole.OPS_OPTIMIZER: OpsOptimizerAgent(provider=self.provider, tracer=self.tracer),
            AgentRole.COMPLIANCE: ComplianceAgent(provider=self.provider, tracer=self.tracer),
        }

    def _init_scenarios(self) -> Dict[str, Scenario]:
        """Define standard scenarios."""
        return {
            "loan_risk_review": Scenario(
                name="loan_risk_review",
                description="Comprehensive loan portfolio risk assessment",
                steps=[
                    ScenarioStep(
                        agent_role=AgentRole.RISK_ANALYST,
                        prompt_template="Analyze the loan portfolio: {portfolio_data}. Identify key risk metrics, concentrations, and trends.",
                        context_keys=["portfolio_data"],
                        output_key="risk_analysis",
                    ),
                    ScenarioStep(
                        agent_role=AgentRole.COMPLIANCE,
                        prompt_template="Review risk findings for regulatory compliance: {risk_analysis}. Flag any violations.",
                        context_keys=["risk_analysis"],
                        output_key="compliance_review",
                    ),
                    ScenarioStep(
                        agent_role=AgentRole.OPS_OPTIMIZER,
                        prompt_template="Recommend operational improvements based on risk findings: {risk_analysis} and compliance review: {compliance_review}.",
                        context_keys=["risk_analysis", "compliance_review"],
                        output_key="ops_recommendations",
                    ),
                ],
            ),
            "growth_strategy": Scenario(
                name="growth_strategy",
                description="Growth opportunity analysis and strategy",
                steps=[
                    ScenarioStep(
                        agent_role=AgentRole.GROWTH_STRATEGIST,
                        prompt_template="Analyze market data: {market_data}. Identify growth opportunities.",
                        context_keys=["market_data"],
                        output_key="growth_analysis",
                    ),
                    ScenarioStep(
                        agent_role=AgentRole.RISK_ANALYST,
                        prompt_template="Assess risk implications of growth strategy: {growth_analysis}.",
                        context_keys=["growth_analysis"],
                        output_key="risk_assessment",
                    ),
                    ScenarioStep(
                        agent_role=AgentRole.COMPLIANCE,
                        prompt_template="Ensure growth strategy complies with regulations: {growth_analysis} with risk context: {risk_assessment}.",
                        context_keys=["growth_analysis", "risk_assessment"],
                        output_key="compliance_check",
                    ),
                ],
            ),
            "portfolio_optimization": Scenario(
                name="portfolio_optimization",
                description="End-to-end portfolio optimization workflow",
                steps=[
                    ScenarioStep(
                        agent_role=AgentRole.RISK_ANALYST,
                        prompt_template="Analyze current portfolio: {portfolio_data}. Calculate risk metrics.",
                        context_keys=["portfolio_data"],
                        output_key="risk_metrics",
                    ),
                    ScenarioStep(
                        agent_role=AgentRole.OPS_OPTIMIZER,
                        prompt_template="Optimize portfolio allocation based on: {risk_metrics}. Maximize efficiency.",
                        context_keys=["risk_metrics"],
                        output_key="optimization_plan",
                    ),
                    ScenarioStep(
                        agent_role=AgentRole.GROWTH_STRATEGIST,
                        prompt_template="Identify revenue opportunities in optimized portfolio: {optimization_plan}.",
                        context_keys=["optimization_plan"],
                        output_key="growth_plan",
                    ),
                    ScenarioStep(
                        agent_role=AgentRole.COMPLIANCE,
                        prompt_template="Final compliance review of plan: {optimization_plan} and {growth_plan}.",
                        context_keys=["optimization_plan", "growth_plan"],
                        output_key="compliance_approval",
                    ),
                ],
            ),
        }

    def run_agent(
        self,
        role: AgentRole,
        messages: List[Message],
        context: Optional[Dict[str, Any]] = None,
        trace_id: Optional[str] = None,
        **kwargs,
    ) -> AgentResponse:
        """Run a single agent.

        Args:
            role: Agent role to execute
            messages: Conversation messages
            context: Additional context data
            trace_id: Optional trace ID (auto-generated if not provided)
            **kwargs: Additional request parameters (max_tokens, temperature, etc.)

        Returns:
            AgentResponse with result
        """
        agent = self.agents.get(role)
        if not agent:
            raise ValueError(f"Agent not found for role: {role}")

        request = AgentRequest(
            trace_id=trace_id or self.tracer.generate_trace_id(),
            messages=messages,
            context=context or {},
            **kwargs,
        )

        return agent.process(request)

    def run_scenario(
        self,
        scenario_name: str,
        initial_context: Dict[str, Any],
        trace_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Run a predefined scenario with context propagation.

        Args:
            scenario_name: Name of scenario to run
            initial_context: Initial context data
            trace_id: Optional trace ID (auto-generated if not provided)

        Returns:
            Dict with all step outputs and aggregated metrics
        """
        scenario = self.scenarios.get(scenario_name)
        if not scenario:
            raise ValueError(f"Scenario not found: {scenario_name}")

        trace_id = trace_id or self.tracer.generate_trace_id()
        context = {**scenario.initial_context, **initial_context}
        results = {}

        logger.info(f"Starting scenario: {scenario_name} with trace_id: {trace_id}")

        for step in scenario.steps:
            # Build prompt from template and context
            prompt = step.prompt_template.format(
                **{k: context.get(k, "") for k in step.context_keys}
            )

            # Run agent
            try:
                response = self.run_agent(
                    role=step.agent_role,
                    messages=[Message(role=MessageRole.USER, content=prompt)],
                    context=context,
                    trace_id=trace_id,
                )

                # Store output in context for next step
                context[step.output_key] = response.message.content
                results[step.output_key] = response.message.content

                logger.info(f"Step completed: {step.agent_role.value} -> {step.output_key}")

            except Exception as e:
                if step.optional:
                    logger.warning(f"Optional step failed: {step.agent_role.value}: {e}")
                    results[step.output_key] = None
                else:
                    logger.error(f"Required step failed: {step.agent_role.value}: {e}")
                    raise

        # Add aggregated metrics
        results["_metadata"] = {
            "scenario_name": scenario_name,
            "trace_id": trace_id,
            "total_cost_usd": self.tracer.get_trace_cost(trace_id),
            "total_tokens": self.tracer.get_trace_tokens(trace_id),
            "steps_completed": len([k for k in results if not k.startswith("_")]),
        }

        logger.info(
            f"Scenario completed: {scenario_name} | "
            f"Cost: ${results['_metadata']['total_cost_usd']:.4f} | "
            f"Tokens: {results['_metadata']['total_tokens']}"
        )

        return results

    def add_scenario(self, scenario: Scenario):
        """Add a custom scenario."""
        self.scenarios[scenario.name] = scenario
        logger.info(f"Added scenario: {scenario.name}")

    def list_scenarios(self) -> List[str]:
        """List available scenario names."""
        return list(self.scenarios.keys())

    def get_scenario(self, name: str) -> Optional[Scenario]:
        """Get scenario definition by name."""
        return self.scenarios.get(name)
