# Multi-Agent Orchestration System

**Production-grade, typed, observable multi-agent orchestration for fintech lending analytics.**

[![Tests](https://img.shields.io/badge/tests-21%20passed-success)]() [![Python](https://img.shields.io/badge/python-3.9%2B-blue)]() [![License](https://img.shields.io/badge/license-MIT-green)]()

## 🌟 Features

- ✅ **Typed Protocol**: Full type safety with Pydantic models
- ✅ **PII Guardrails**: Automatic redaction of sensitive data (SSN, email, phone, credit cards)
- ✅ **Multi-Provider**: OpenAI, Anthropic, Gemini support with easy switching
- ✅ **Tracing & Cost Tracking**: OpenTelemetry compatible, tracks tokens and costs per trace
- ✅ **4 Role-Specific Agents**: Risk Analyst, Growth Strategist, Ops Optimizer, Compliance
- ✅ **Scenario Orchestration**: Pre-built workflows for common fintech use cases
- ✅ **Observable**: Centralized logging, trace IDs, latency metrics
- ✅ **Tested**: 21 unit tests covering protocol, guardrails, tracing, orchestration

## 📋 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Client Layer                            │
│  (Python scripts, web apps, notebooks, APIs)                │
└─────────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────┐
│                 Orchestration Layer                          │
│  ┌───────────────────────────────────────────────────┐      │
│  │  MultiAgentOrchestrator                           │      │
│  │  - run_agent()      - run_scenario()              │      │
│  │  - add_scenario()   - list_scenarios()            │      │
│  └───────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────┐
│                     Agent Layer                              │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐        │
│  │ RiskAnalyst  │ │ GrowthStrat  │ │ OpsOptimizer │        │
│  └──────────────┘ └──────────────┘ └──────────────┘        │
│  ┌──────────────┐                                           │
│  │ Compliance   │                                           │
│  └──────────────┘                                           │
│  All extend BaseAgent with:                                 │
│  - get_system_prompt() - process()                          │
└─────────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────┐
│                 Core Services Layer                          │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐            │
│  │ Guardrails │  │  Tracing   │  │  Protocol  │            │
│  │ PII Redact │  │ Cost Track │  │  Typed API │            │
│  └────────────┘  └────────────┘  └────────────┘            │
└─────────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────┐
│                 LLM Providers Layer                          │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐            │
│  │   OpenAI   │  │ Anthropic  │  │   Gemini   │            │
│  │ gpt-4o-mini│  │ Claude 3.5 │  │ 2.0-flash  │            │
│  └────────────┘  └────────────┘  └────────────┘            │
└─────────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────┐
│            Storage & Monitoring Layer                        │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐            │
│  │   Logs     │  │   Traces   │  │  Metrics   │            │
│  │ Structured │  │OpenTelemetry│ │ Cost/Token │            │
│  └────────────┘  └────────────┘  └────────────┘            │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Installation

```bash
# Required
pip install pydantic openai

# Optional providers
pip install anthropic google-generativeai

# Optional observability
pip install opentelemetry-api opentelemetry-sdk
```

### Environment Setup

```bash
export OPENAI_API_KEY="your_openai_key"
export ANTHROPIC_API_KEY="your_anthropic_key"  # Optional
export GEMINI_API_KEY="your_gemini_key"        # Optional
```

### Basic Usage

```python
from python.multi_agent.orchestrator import MultiAgentOrchestrator
from python.multi_agent.protocol import AgentRole, Message, MessageRole

# Initialize orchestrator
orchestrator = MultiAgentOrchestrator()

# Query a single agent
messages = [Message(
    role=MessageRole.USER,
    content="Analyze a loan portfolio with $10M outstanding, 5% delinquency rate."
)]

response = orchestrator.run_agent(
    role=AgentRole.RISK_ANALYST,
    messages=messages,
    context={"portfolio_size": 10_000_000}
)

print(f"Response: {response.message.content}")
print(f"Cost: ${response.cost_usd:.4f}")
print(f"Tokens: {response.tokens_used}")
```

## 🔍 Validation Report

✅ **All files compile without syntax errors**  
✅ **All imports successful**  
✅ **21/21 tests passing**  
✅ **Protocol classes: OK**  
✅ **Guardrails: OK**  
✅ **Tracing: OK**  
✅ **Agents: OK**  
✅ **Orchestrator: OK**

## 📚 Documentation

See full documentation for:

- Pre-built scenarios (loan_risk_review, growth_strategy, portfolio_optimization)
- PII redaction and security
- Cost tracking and observability
- OpenTelemetry integration
- Custom scenario creation
- Provider switching (OpenAI, Anthropic, Gemini)
- Usage examples

## 🧪 Testing

```bash
# Run all 21 tests
python3 -m pytest python/multi_agent/tests.py -v

# Expected output: ✅ 21 passed in 0.10s
```

## 📖 Examples

```bash
# Run interactive examples
python3 -m python.multi_agent.examples
```

---

**Built for fintech lending analytics by Arisofia/abaco-loans-analytics**

- **Trace ID**: unique identifier for tracing requests through the system.
- **Tokens**: used for authorization and tracking.
- **Cost**: monitors operational costs.
- **Latency**: measures the time taken for operations.
- **Logs**: provides visibility into system operations and potential issues.
- **OpenTelemetry**: supports distributed tracing and metrics collection.

## Guardrails

- **PII Redaction**: implements mechanisms to redact personally identifiable information.

## Migration from Legacy Code Pattern

Guidelines and best practices for migrating from legacy code patterns to the new architecture.

## Examples Directory Reference

A reference to the directory containing examples for using the Multi-Agent Orchestration System.
