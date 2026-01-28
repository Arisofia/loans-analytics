"""Multi-agent orchestrator with scenario support."""

import logging
from typing import Any, Dict, List, Optional

from .agents import ComplianceAgent, GrowthStrategistAgent, OpsOptimizerAgent, RiskAnalystAgent
from .specialized_agents import CollectionsAgent, FraudDetectionAgent, PricingAgent, CustomerRetentionAgent
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
            AgentRole.RISK_ANALYST: RiskAnalystAgent(
                provider=self.provider, tracer=self.tracer
            ),
            AgentRole.GROWTH_STRATEGIST: GrowthStrategistAgent(
                provider=self.provider, tracer=self.tracer
            ),
            AgentRole.OPS_OPTIMIZER: OpsOptimizerAgent(
                provider=self.provider, tracer=self.tracer
            ),
            AgentRole.COMPLIANCE: ComplianceAgent(
                provider=self.provider, tracer=self.tracer
            ),
            AgentRole.COLLECTIONS: CollectionsAgent(
                provider=self.provider, tracer=self.tracer
            ),
            AgentRole.FRAUD_DETECTION: FraudDetectionAgent(
                provider=self.provider, tracer=self.tracer
            ),
            AgentRole.PRICING: PricingAgent(
                provider=self.provider, tracer=self.tracer
            ),
            AgentRole.CUSTOMER_RETENTION: CustomerRetentionAgent(
                provider=self.provider, tracer=self.tracer
            ),
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
            "kpi_anomaly_detection": Scenario(
                name="kpi_anomaly_detection",
                description="Multi-agent KPI anomaly detection and root cause analysis",
                steps=[
                    ScenarioStep(
                        agent_role=AgentRole.RISK_ANALYST,
                        prompt_template="Analyze the following KPI anomalies: {kpi_anomalies}. Assess risk implications and potential causes. Consider historical trends: {historical_context}.",
                        context_keys=["kpi_anomalies", "historical_context"],
                        output_key="risk_assessment",
                    ),
                    ScenarioStep(
                        agent_role=AgentRole.COMPLIANCE,
                        prompt_template="Review KPI breach implications: {risk_assessment}. Check if any anomalies indicate regulatory compliance issues or reporting violations.",
                        context_keys=["risk_assessment"],
                        output_key="compliance_check",
                    ),
                    ScenarioStep(
                        agent_role=AgentRole.OPS_OPTIMIZER,
                        prompt_template="Based on risk assessment: {risk_assessment} and compliance findings: {compliance_check}, recommend corrective actions and process improvements to prevent future KPI breaches.",
                        context_keys=["risk_assessment", "compliance_check"],
                        output_key="action_plan",
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
            "delinquency_workout": Scenario(
                name="delinquency_workout",
                description="Delinquent account analysis and workout strategy",
                steps=[
                    ScenarioStep(
                        agent_role=AgentRole.COLLECTIONS,
                        prompt_template="Analyze delinquent account: {account_data}. Segment by risk and recommend collection strategy.",
                        context_keys=["account_data"],
                        output_key="collections_strategy",
                    ),
                    ScenarioStep(
                        agent_role=AgentRole.RISK_ANALYST,
                        prompt_template="Assess recovery likelihood and expected loss for: {collections_strategy}.",
                        context_keys=["collections_strategy"],
                        output_key="recovery_assessment",
                    ),
                    ScenarioStep(
                        agent_role=AgentRole.CUSTOMER_RETENTION,
                        prompt_template="Evaluate retention opportunity and recommend workout plan based on: {collections_strategy} and {recovery_assessment}.",
                        context_keys=["collections_strategy", "recovery_assessment"],
                        output_key="workout_plan",
                    ),
                ],
            ),
            "fraud_investigation": Scenario(
                name="fraud_investigation",
                description="Suspicious application fraud detection workflow",
                steps=[
                    ScenarioStep(
                        agent_role=AgentRole.FRAUD_DETECTION,
                        prompt_template="Analyze application for fraud indicators: {application_data}. Provide fraud risk score and evidence.",
                        context_keys=["application_data"],
                        output_key="fraud_analysis",
                    ),
                    ScenarioStep(
                        agent_role=AgentRole.RISK_ANALYST,
                        prompt_template="Assess portfolio risk impact if this application is fraudulent: {fraud_analysis}.",
                        context_keys=["fraud_analysis"],
                        output_key="risk_impact",
                    ),
                    ScenarioStep(
                        agent_role=AgentRole.COMPLIANCE,
                        prompt_template="Review fraud case for regulatory reporting requirements: {fraud_analysis} with risk context: {risk_impact}.",
                        context_keys=["fraud_analysis", "risk_impact"],
                        output_key="regulatory_actions",
                    ),
                ],
            ),
            "pricing_optimization": Scenario(
                name="pricing_optimization",
                description="Risk-based pricing and rate optimization",
                steps=[
                    ScenarioStep(
                        agent_role=AgentRole.RISK_ANALYST,
                        prompt_template="Analyze borrower risk profile: {borrower_data}. Calculate risk-adjusted metrics.",
                        context_keys=["borrower_data"],
                        output_key="risk_profile",
                    ),
                    ScenarioStep(
                        agent_role=AgentRole.PRICING,
                        prompt_template="Recommend optimal pricing based on risk: {risk_profile} and market conditions: {market_data}.",
                        context_keys=["risk_profile", "market_data"],
                        output_key="pricing_recommendation",
                    ),
                    ScenarioStep(
                        agent_role=AgentRole.COMPLIANCE,
                        prompt_template="Verify pricing complies with regulations: {pricing_recommendation}.",
                        context_keys=["pricing_recommendation"],
                        output_key="pricing_approval",
                    ),
                ],
            ),
            "churn_prevention": Scenario(
                name="churn_prevention",
                description="Customer churn risk analysis and retention strategy",
                steps=[
                    ScenarioStep(
                        agent_role=AgentRole.CUSTOMER_RETENTION,
                        prompt_template="Analyze customer for churn risk: {customer_data}. Identify churn signals and lifetime value.",
                        context_keys=["customer_data"],
                        output_key="churn_analysis",
                    ),
                    ScenarioStep(
                        agent_role=AgentRole.PRICING,
                        prompt_template="Recommend retention offer based on: {churn_analysis}. Balance profitability and retention.",
                        context_keys=["churn_analysis"],
                        output_key="retention_offer",
                    ),
                    ScenarioStep(
                        agent_role=AgentRole.OPS_OPTIMIZER,
                        prompt_template="Design retention campaign execution plan: {retention_offer}. Optimize timing and channel.",
                        context_keys=["retention_offer"],
                        output_key="campaign_plan",
                    ),
                ],
            ),
            # ========================================
            # Product-Specific Scenarios: Retail Loans
            # ========================================
            "retail_origination": Scenario(
                name="retail_origination",
                description="End-to-end retail loan origination workflow",
                steps=[
                    ScenarioStep(
                        agent_role=AgentRole.FRAUD_DETECTION,
                        prompt_template="Screen application for fraud: {application_data}. Flag suspicious indicators.",
                        context_keys=["application_data"],
                        output_key="fraud_screen",
                    ),
                    ScenarioStep(
                        agent_role=AgentRole.RISK_ANALYST,
                        prompt_template="Underwrite application considering fraud screen: {fraud_screen} and credit data: {credit_data}.",
                        context_keys=["fraud_screen", "credit_data"],
                        output_key="underwriting_decision",
                    ),
                    ScenarioStep(
                        agent_role=AgentRole.PRICING,
                        prompt_template="Set optimal rate for approved application: {underwriting_decision} with market rates: {market_rates}.",
                        context_keys=["underwriting_decision", "market_rates"],
                        output_key="rate_quote",
                    ),
                    ScenarioStep(
                        agent_role=AgentRole.COMPLIANCE,
                        prompt_template="Final compliance check for origination: {underwriting_decision} and {rate_quote}. Approve or flag issues.",
                        context_keys=["underwriting_decision", "rate_quote"],
                        output_key="compliance_approval",
                    ),
                ],
            ),
            "retail_portfolio_review": Scenario(
                name="retail_portfolio_review",
                description="Quarterly retail loan portfolio health assessment",
                steps=[
                    ScenarioStep(
                        agent_role=AgentRole.RISK_ANALYST,
                        prompt_template="Assess retail portfolio health: {portfolio_metrics}. Identify delinquency trends and risk concentrations.",
                        context_keys=["portfolio_metrics"],
                        output_key="risk_assessment",
                    ),
                    ScenarioStep(
                        agent_role=AgentRole.COLLECTIONS,
                        prompt_template="Analyze delinquency patterns from risk assessment: {risk_assessment}. Recommend collection strategies.",
                        context_keys=["risk_assessment"],
                        output_key="collection_strategy",
                    ),
                    ScenarioStep(
                        agent_role=AgentRole.CUSTOMER_RETENTION,
                        prompt_template="Identify at-risk customers from portfolio: {risk_assessment}. Design retention campaigns.",
                        context_keys=["risk_assessment"],
                        output_key="retention_plan",
                    ),
                    ScenarioStep(
                        agent_role=AgentRole.OPS_OPTIMIZER,
                        prompt_template="Consolidate action plan from: {collection_strategy} and {retention_plan}. Prioritize by ROI.",
                        context_keys=["collection_strategy", "retention_plan"],
                        output_key="action_plan",
                    ),
                ],
            ),
            "retail_rate_adjustment": Scenario(
                name="retail_rate_adjustment",
                description="Portfolio-wide rate adjustment and repricing",
                steps=[
                    ScenarioStep(
                        agent_role=AgentRole.RISK_ANALYST,
                        prompt_template="Segment retail portfolio by risk profile: {portfolio_data}. Identify repricing candidates.",
                        context_keys=["portfolio_data"],
                        output_key="risk_segmentation",
                    ),
                    ScenarioStep(
                        agent_role=AgentRole.PRICING,
                        prompt_template="Design rate adjustment strategy for segments: {risk_segmentation} considering market: {market_conditions}.",
                        context_keys=["risk_segmentation", "market_conditions"],
                        output_key="repricing_strategy",
                    ),
                    ScenarioStep(
                        agent_role=AgentRole.CUSTOMER_RETENTION,
                        prompt_template="Assess churn risk from repricing: {repricing_strategy}. Suggest mitigation tactics.",
                        context_keys=["repricing_strategy"],
                        output_key="churn_mitigation",
                    ),
                    ScenarioStep(
                        agent_role=AgentRole.COMPLIANCE,
                        prompt_template="Review repricing plan for regulatory compliance: {repricing_strategy} and {churn_mitigation}.",
                        context_keys=["repricing_strategy", "churn_mitigation"],
                        output_key="compliance_review",
                    ),
                ],
            ),
            # ========================================
            # Product-Specific Scenarios: SME Loans
            # ========================================
            "sme_underwriting": Scenario(
                name="sme_underwriting",
                description="SME loan underwriting with fraud and pricing analysis",
                steps=[
                    ScenarioStep(
                        agent_role=AgentRole.RISK_ANALYST,
                        prompt_template="Assess SME credit risk: {business_data}. Analyze financials, cash flow, industry risk.",
                        context_keys=["business_data"],
                        output_key="credit_assessment",
                    ),
                    ScenarioStep(
                        agent_role=AgentRole.FRAUD_DETECTION,
                        prompt_template="Screen for business fraud: {credit_assessment}. Check beneficial ownership, tax compliance, trade references.",
                        context_keys=["credit_assessment"],
                        output_key="fraud_check",
                    ),
                    ScenarioStep(
                        agent_role=AgentRole.PRICING,
                        prompt_template="Price SME loan based on: {credit_assessment} and {fraud_check}. Consider collateral and guarantees.",
                        context_keys=["credit_assessment", "fraud_check"],
                        output_key="pricing_terms",
                    ),
                    ScenarioStep(
                        agent_role=AgentRole.COMPLIANCE,
                        prompt_template="Verify SME lending compliance: {pricing_terms}. Check regulatory limits and documentation.",
                        context_keys=["pricing_terms"],
                        output_key="compliance_clearance",
                    ),
                ],
            ),
            "sme_portfolio_stress_test": Scenario(
                name="sme_portfolio_stress_test",
                description="SME portfolio stress testing and scenario analysis",
                steps=[
                    ScenarioStep(
                        agent_role=AgentRole.RISK_ANALYST,
                        prompt_template="Run stress scenarios on SME portfolio: {portfolio_data} with assumptions: {stress_scenarios}.",
                        context_keys=["portfolio_data", "stress_scenarios"],
                        output_key="stress_results",
                    ),
                    ScenarioStep(
                        agent_role=AgentRole.OPS_OPTIMIZER,
                        prompt_template="Identify operational responses to stress results: {stress_results}. Optimize reserves and liquidity.",
                        context_keys=["stress_results"],
                        output_key="operational_response",
                    ),
                    ScenarioStep(
                        agent_role=AgentRole.GROWTH_STRATEGIST,
                        prompt_template="Adjust growth strategy based on: {stress_results} and {operational_response}. Balance risk and opportunity.",
                        context_keys=["stress_results", "operational_response"],
                        output_key="strategic_adjustments",
                    ),
                ],
            ),
            "sme_default_management": Scenario(
                name="sme_default_management",
                description="SME default workout and recovery strategy",
                steps=[
                    ScenarioStep(
                        agent_role=AgentRole.COLLECTIONS,
                        prompt_template="Assess defaulted SME loan: {loan_data}. Evaluate collateral, guarantees, business viability.",
                        context_keys=["loan_data"],
                        output_key="default_assessment",
                    ),
                    ScenarioStep(
                        agent_role=AgentRole.RISK_ANALYST,
                        prompt_template="Calculate expected recovery and loss: {default_assessment}. Consider liquidation vs. restructuring.",
                        context_keys=["default_assessment"],
                        output_key="recovery_analysis",
                    ),
                    ScenarioStep(
                        agent_role=AgentRole.COMPLIANCE,
                        prompt_template="Review legal options and regulatory requirements: {recovery_analysis}. Document next steps.",
                        context_keys=["recovery_analysis"],
                        output_key="legal_strategy",
                    ),
                ],
            ),
            # ========================================
            # Product-Specific Scenarios: Auto Loans
            # ========================================
            "auto_origination": Scenario(
                name="auto_origination",
                description="Auto loan origination with fraud screening and pricing",
                steps=[
                    ScenarioStep(
                        agent_role=AgentRole.FRAUD_DETECTION,
                        prompt_template="Screen auto loan application: {application_data}. Verify VIN, title, income documentation.",
                        context_keys=["application_data"],
                        output_key="fraud_screen",
                    ),
                    ScenarioStep(
                        agent_role=AgentRole.PRICING,
                        prompt_template="Price auto loan: {fraud_screen} with vehicle data: {vehicle_data}. Calculate LTV and rate.",
                        context_keys=["fraud_screen", "vehicle_data"],
                        output_key="loan_terms",
                    ),
                    ScenarioStep(
                        agent_role=AgentRole.RISK_ANALYST,
                        prompt_template="Underwrite based on: {loan_terms}. Assess borrower capacity and collateral value.",
                        context_keys=["loan_terms"],
                        output_key="underwriting_decision",
                    ),
                    ScenarioStep(
                        agent_role=AgentRole.OPS_OPTIMIZER,
                        prompt_template="Optimize funding and documentation: {underwriting_decision}. Streamline closing process.",
                        context_keys=["underwriting_decision"],
                        output_key="operational_plan",
                    ),
                ],
            ),
            "auto_delinquency_workout": Scenario(
                name="auto_delinquency_workout",
                description="Auto loan delinquency management and recovery",
                steps=[
                    ScenarioStep(
                        agent_role=AgentRole.COLLECTIONS,
                        prompt_template="Manage delinquent auto loan: {account_data}. Assess vehicle location, value, payment capacity.",
                        context_keys=["account_data"],
                        output_key="collection_plan",
                    ),
                    ScenarioStep(
                        agent_role=AgentRole.CUSTOMER_RETENTION,
                        prompt_template="Evaluate retention vs. repossession: {collection_plan}. Consider customer relationship value.",
                        context_keys=["collection_plan"],
                        output_key="retention_assessment",
                    ),
                    ScenarioStep(
                        agent_role=AgentRole.RISK_ANALYST,
                        prompt_template="Calculate recovery options: {retention_assessment}. Compare workout vs. repo scenarios.",
                        context_keys=["retention_assessment"],
                        output_key="recovery_recommendation",
                    ),
                ],
            ),
            "auto_residual_value_analysis": Scenario(
                name="auto_residual_value_analysis",
                description="Auto loan portfolio residual value assessment",
                steps=[
                    ScenarioStep(
                        agent_role=AgentRole.RISK_ANALYST,
                        prompt_template="Analyze auto portfolio residual values: {portfolio_data} with market trends: {market_data}.",
                        context_keys=["portfolio_data", "market_data"],
                        output_key="residual_analysis",
                    ),
                    ScenarioStep(
                        agent_role=AgentRole.PRICING,
                        prompt_template="Adjust LTV and pricing strategy: {residual_analysis}. Optimize for changing collateral values.",
                        context_keys=["residual_analysis"],
                        output_key="pricing_adjustments",
                    ),
                    ScenarioStep(
                        agent_role=AgentRole.OPS_OPTIMIZER,
                        prompt_template="Implement portfolio actions: {pricing_adjustments}. Plan reserve adjustments and hedging.",
                        context_keys=["pricing_adjustments"],
                        output_key="implementation_plan",
                    ),
                ],
            ),
            # ========================================
            # Portfolio-Level Scenarios
            # ========================================
            "portfolio_health_check": Scenario(
                name="portfolio_health_check",
                description="Comprehensive portfolio health assessment with KPIs",
                steps=[
                    ScenarioStep(
                        agent_role=AgentRole.RISK_ANALYST,
                        prompt_template="Assess overall portfolio health: {portfolio_metrics}. Identify key risk indicators and trends.",
                        context_keys=["portfolio_metrics"],
                        output_key="health_assessment",
                    ),
                    ScenarioStep(
                        agent_role=AgentRole.COMPLIANCE,
                        prompt_template="Review regulatory compliance status: {health_assessment}. Flag any breaches or concerns.",
                        context_keys=["health_assessment"],
                        output_key="compliance_status",
                    ),
                    ScenarioStep(
                        agent_role=AgentRole.OPS_OPTIMIZER,
                        prompt_template="Recommend operational improvements: {health_assessment} and {compliance_status}.",
                        context_keys=["health_assessment", "compliance_status"],
                        output_key="improvement_plan",
                    ),
                ],
            ),
            "strategic_planning": Scenario(
                name="strategic_planning",
                description="Annual strategic planning for lending business",
                steps=[
                    ScenarioStep(
                        agent_role=AgentRole.GROWTH_STRATEGIST,
                        prompt_template="Develop growth strategy: {market_analysis} and {performance_data}. Identify expansion opportunities.",
                        context_keys=["market_analysis", "performance_data"],
                        output_key="growth_strategy",
                    ),
                    ScenarioStep(
                        agent_role=AgentRole.RISK_ANALYST,
                        prompt_template="Assess risk appetite and constraints: {growth_strategy}. Define risk tolerance levels.",
                        context_keys=["growth_strategy"],
                        output_key="risk_framework",
                    ),
                    ScenarioStep(
                        agent_role=AgentRole.PRICING,
                        prompt_template="Design pricing strategy to support: {growth_strategy} within {risk_framework}.",
                        context_keys=["growth_strategy", "risk_framework"],
                        output_key="pricing_strategy",
                    ),
                    ScenarioStep(
                        agent_role=AgentRole.OPS_OPTIMIZER,
                        prompt_template="Build operational roadmap for: {growth_strategy}, {risk_framework}, and {pricing_strategy}.",
                        context_keys=["growth_strategy", "risk_framework", "pricing_strategy"],
                        output_key="execution_roadmap",
                    ),
                ],
            ),
            "regulatory_review": Scenario(
                name="regulatory_review",
                description="Comprehensive regulatory compliance review",
                steps=[
                    ScenarioStep(
                        agent_role=AgentRole.COMPLIANCE,
                        prompt_template="Conduct regulatory compliance audit: {audit_scope}. Identify gaps and violations.",
                        context_keys=["audit_scope"],
                        output_key="compliance_findings",
                    ),
                    ScenarioStep(
                        agent_role=AgentRole.RISK_ANALYST,
                        prompt_template="Assess risk exposure from compliance findings: {compliance_findings}.",
                        context_keys=["compliance_findings"],
                        output_key="risk_exposure",
                    ),
                    ScenarioStep(
                        agent_role=AgentRole.OPS_OPTIMIZER,
                        prompt_template="Design remediation plan: {compliance_findings} and {risk_exposure}. Prioritize by severity.",
                        context_keys=["compliance_findings", "risk_exposure"],
                        output_key="remediation_plan",
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

        logger.info(
            f"Starting scenario: {scenario_name} with trace_id: {trace_id}"
        )

        for step in scenario.steps:
            # Build prompt from template and context
            prompt = step.prompt_template.format(**{k: context.get(k, "") for k in step.context_keys})

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

                logger.info(
                    f"Step completed: {step.agent_role.value} -> {step.output_key}"
                )

            except Exception as e:
                if step.optional:
                    logger.warning(
                        f"Optional step failed: {step.agent_role.value}: {e}"
                    )
                    results[step.output_key] = None
                else:
                    logger.error(
                        f"Required step failed: {step.agent_role.value}: {e}"
                    )
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
