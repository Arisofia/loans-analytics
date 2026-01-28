# Multi-Agent Scenario Library

**Version**: 1.0.0  
**Last Updated**: January 28, 2026

This document describes all pre-built multi-agent scenarios available in the orchestration system. Each scenario defines a multi-step workflow where agents collaborate to solve complex fintech problems.

---

## 📋 Scenario Index

| Scenario Name            | Agents Used                                    | Steps | Business Owner        | Use Case                                         |
| ------------------------ | ---------------------------------------------- | ----- | --------------------- | ------------------------------------------------ |
| `loan_risk_review`       | Risk Analyst, Compliance, Ops Optimizer        | 3     | Credit Risk Team      | Comprehensive loan portfolio risk assessment     |
| `growth_strategy`        | Growth Strategist, Risk Analyst, Ops Optimizer | 3     | Product/Strategy Team | Market expansion and growth opportunity analysis |
| `portfolio_optimization` | Ops Optimizer, Risk Analyst, Growth Strategist | 3     | Portfolio Management  | Portfolio performance review and recommendations |

---

## 📖 Scenario Definitions

### 1. Loan Risk Review

**Scenario Name**: `loan_risk_review`  
**Business Owner**: Credit Risk Team  
**Purpose**: Comprehensive risk assessment of loan applications or portfolios

#### Flow

```
Step 1: Risk Analyst
  ↓ Analyzes credit data and risk indicators

Step 2: Compliance Officer
  ↓ Validates regulatory compliance and policy adherence

Step 3: Ops Optimizer
  ↓ Recommends operational improvements and workflow optimizations
```

#### Inputs

| Key                 | Type   | Description                        | Example                                                                  |
| ------------------- | ------ | ---------------------------------- | ------------------------------------------------------------------------ |
| `loan_data`         | object | Loan application details           | `{"loan_id": "L123", "amount": 50000, "term": 36, "borrower_fico": 720}` |
| `portfolio_context` | object | Portfolio-level context (optional) | `{"total_exposure": 5000000, "avg_default_rate": 0.02}`                  |

#### Outputs

| Key                 | Type   | Description                                              |
| ------------------- | ------ | -------------------------------------------------------- |
| `risk_analysis`     | string | Detailed risk assessment with scores and recommendations |
| `compliance_check`  | string | Compliance review results with pass/fail status          |
| `optimization_plan` | string | Operational recommendations for efficiency               |

#### Usage Example

```python
from python.multi_agent.orchestrator import MultiAgentOrchestrator

orchestrator = MultiAgentOrchestrator()

results = orchestrator.run_scenario(
    scenario_name="loan_risk_review",
    initial_context={
        "loan_data": {
            "loan_id": "L12345",
            "amount": 50000,
            "term": 36,
            "borrower_fico": 720,
            "debt_to_income": 0.35,
            "employment_history": "5 years"
        },
        "portfolio_context": {
            "total_exposure": 5000000,
            "avg_default_rate": 0.02
        }
    }
)

print(results["risk_analysis"])
print(results["compliance_check"])
print(results["optimization_plan"])
```

#### Expected Execution Time

- Average: 5-10 seconds (depending on LLM provider)
- Tokens: ~2,000-5,000 tokens
- Cost: ~$0.01-$0.03 (OpenAI GPT-4o-mini)

---

### 2. Growth Strategy

**Scenario Name**: `growth_strategy`  
**Business Owner**: Product/Strategy Team  
**Purpose**: Identify market expansion opportunities and growth strategies

#### Flow

```
Step 1: Growth Strategist
  ↓ Analyzes market opportunities and expansion potential

Step 2: Risk Analyst
  ↓ Assesses risks associated with growth strategies

Step 3: Ops Optimizer
  ↓ Evaluates operational readiness and resource requirements
```

#### Inputs

| Key               | Type   | Description                  | Example                                                                            |
| ----------------- | ------ | ---------------------------- | ---------------------------------------------------------------------------------- |
| `market_data`     | object | Market analysis and trends   | `{"target_segment": "SME", "market_size": 1000000, "competition_level": "medium"}` |
| `current_metrics` | object | Current business performance | `{"monthly_origination": 5000000, "customer_acquisition_cost": 150}`               |

#### Outputs

| Key                     | Type   | Description                                      |
| ----------------------- | ------ | ------------------------------------------------ |
| `growth_opportunities`  | string | Identified growth strategies with prioritization |
| `risk_assessment`       | string | Risk analysis of proposed strategies             |
| `operational_readiness` | string | Resource needs and operational gap analysis      |

#### Usage Example

```python
orchestrator = MultiAgentOrchestrator()

results = orchestrator.run_scenario(
    scenario_name="growth_strategy",
    initial_context={
        "market_data": {
            "target_segment": "Small Business Loans",
            "market_size": 10000000,
            "competition_level": "high",
            "regulatory_environment": "moderate"
        },
        "current_metrics": {
            "monthly_origination": 5000000,
            "customer_acquisition_cost": 150,
            "avg_loan_size": 25000
        }
    }
)
```

#### Expected Execution Time

- Average: 8-15 seconds
- Tokens: ~3,000-7,000 tokens
- Cost: ~$0.02-$0.05

---

### 3. Portfolio Optimization

**Scenario Name**: `portfolio_optimization`  
**Business Owner**: Portfolio Management Team  
**Purpose**: Comprehensive portfolio performance review and optimization

#### Flow

```
Step 1: Ops Optimizer
  ↓ Analyzes portfolio efficiency and operational metrics

Step 2: Risk Analyst
  ↓ Reviews risk distribution and concentration

Step 3: Growth Strategist
  ↓ Identifies opportunities for portfolio growth and diversification
```

#### Inputs

| Key                   | Type   | Description                           | Example                                                                 |
| --------------------- | ------ | ------------------------------------- | ----------------------------------------------------------------------- |
| `portfolio_data`      | object | Portfolio composition and performance | `{"total_value": 10000000, "num_loans": 500, "avg_default_rate": 0.02}` |
| `performance_metrics` | object | Key performance indicators            | `{"roi": 0.12, "net_interest_margin": 0.045}`                           |

#### Outputs

| Key                      | Type   | Description                                     |
| ------------------------ | ------ | ----------------------------------------------- |
| `efficiency_analysis`    | string | Operational efficiency recommendations          |
| `risk_review`            | string | Risk concentration and diversification analysis |
| `growth_recommendations` | string | Portfolio growth and diversification strategies |

#### Usage Example

```python
orchestrator = MultiAgentOrchestrator()

results = orchestrator.run_scenario(
    scenario_name="portfolio_optimization",
    initial_context={
        "portfolio_data": {
            "total_value": 10000000,
            "num_loans": 500,
            "avg_loan_size": 20000,
            "avg_default_rate": 0.02,
            "segmentation": {
                "personal": 0.6,
                "business": 0.4
            }
        },
        "performance_metrics": {
            "roi": 0.12,
            "net_interest_margin": 0.045,
            "operating_efficiency_ratio": 0.65
        }
    }
)
```

#### Expected Execution Time

- Average: 10-18 seconds
- Tokens: ~4,000-8,000 tokens
- Cost: ~$0.03-$0.06

---

## 🎯 Creating Custom Scenarios

### Scenario Structure

```python
from python.multi_agent.protocol import Scenario, ScenarioStep, AgentRole

custom_scenario = Scenario(
    name="custom_scenario_name",
    description="Brief description of what this scenario does",
    steps=[
        ScenarioStep(
            agent_role=AgentRole.RISK_ANALYST,
            prompt_template="Analyze {input_data} and provide risk assessment",
            context_keys=["input_data"],  # Keys available from initial_context
            output_key="risk_analysis"    # Where to store this step's output
        ),
        ScenarioStep(
            agent_role=AgentRole.COMPLIANCE,
            prompt_template="Review {risk_analysis} for compliance issues",
            context_keys=["risk_analysis"],  # Can use outputs from previous steps
            output_key="compliance_review"
        )
    ]
)

# Register with orchestrator
orchestrator.add_scenario(custom_scenario)
```

### Best Practices for Custom Scenarios

1. **Context Propagation**: Each step's `output_key` becomes available to subsequent steps via `context_keys`
2. **Prompt Templates**: Use `{key}` syntax to inject context values into prompts
3. **Agent Order**: Sequence agents logically (e.g., Risk before Compliance, Analysis before Strategy)
4. **Error Handling**: Orchestrator handles agent failures and includes them in trace logs
5. **Cost Awareness**: Estimate token usage - complex scenarios with long contexts will be more expensive

### Scenario Naming Conventions

- Use snake_case: `loan_risk_review`, `portfolio_optimization`
- Be descriptive but concise
- Indicate business domain when ambiguous: `retail_loan_approval`, `sme_growth_strategy`

---

## 📊 Scenario Performance Metrics

Track these metrics for each scenario execution:

| Metric            | Description                    | How to Access                       |
| ----------------- | ------------------------------ | ----------------------------------- |
| **Total Latency** | End-to-end execution time      | Trace logs                          |
| **Total Tokens**  | Sum of tokens across all steps | `tracer.get_trace_tokens(trace_id)` |
| **Total Cost**    | Sum of costs across all steps  | `tracer.get_trace_cost(trace_id)`   |
| **Success Rate**  | % of successful executions     | Application logs                    |
| **Step Failures** | Which steps fail most often    | Trace error logs                    |

---

## 🔒 Security & Compliance

All scenarios automatically apply:

✅ **PII Redaction**: Email, SSN, phone, credit card, EIN  
✅ **Trace Logging**: Full audit trail with trace IDs  
✅ **Cost Tracking**: Per-scenario cost and token usage  
✅ **Input Validation**: Context key validation before execution

---

## 🚀 Integration with Services

### From Python Backend

```python
from python.multi_agent.orchestrator import MultiAgentOrchestrator

orchestrator = MultiAgentOrchestrator()

# In your API endpoint
@app.post("/api/analyze-loan")
def analyze_loan(loan_data: dict):
    results = orchestrator.run_scenario(
        scenario_name="loan_risk_review",
        initial_context={"loan_data": loan_data}
    )
    return results
```

### From CLI

```bash
# List scenarios
python -m python.multi_agent.cli list-scenarios

# Run scenario
python -m python.multi_agent.cli run-scenario loan_risk_review \
    --context '{"loan_data": {"loan_id": "L123", "amount": 50000}}'
```

### From Notebooks

```python
# Jupyter/IPython
from python.multi_agent.orchestrator import MultiAgentOrchestrator

orchestrator = MultiAgentOrchestrator()

# Interactive scenario execution
results = orchestrator.run_scenario("loan_risk_review", {
    "loan_data": {...}
})
```

---

## 📈 Scenario Roadmap

**Planned Scenarios** (Future Releases):

- `collections_strategy` - Delinquency management and recovery workflows
- `fraud_detection` - Multi-agent fraud analysis pipeline
- `customer_retention` - Churn analysis and retention recommendations
- `regulatory_reporting` - Automated compliance report generation
- `pricing_optimization` - Dynamic pricing strategy recommendations

**Regional Variants**:

- Add region-specific compliance rules
- Multi-language support for prompts
- Localized regulatory frameworks

---

## 🛠️ Troubleshooting

### Common Issues

**Scenario Not Found**

```python
# List available scenarios
print(orchestrator.list_scenarios())
```

**Context Key Missing**

- Ensure all `context_keys` in scenario steps are provided in `initial_context`
- Check spelling and case sensitivity

**High Costs**

- Monitor token usage with `tracer.get_trace_tokens()`
- Simplify prompts or reduce context size
- Consider switching to cheaper LLM models for non-critical scenarios

**Slow Execution**

- Check LLM provider latency
- Consider parallel execution for independent steps (future enhancement)
- Cache common scenario results when appropriate

---

## 📞 Support & Feedback

- **Documentation**: See [INTEGRATION_STATUS.md](../INTEGRATION_STATUS.md)
- **Tests**: Run `pytest python/multi_agent/tests.py -v`
- **Examples**: See [examples.py](../python/multi_agent/examples.py)

For questions about specific scenarios or custom scenario development, consult your team's technical lead or the multi-agent system maintainer.
