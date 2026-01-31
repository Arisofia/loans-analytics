"""Example usage of multi-agent orchestrator."""

import os

try:
    # Preferred: run as package module (python -m python.multi_agent.examples)
    from .guardrails import Guardrails
    from .orchestrator import MultiAgentOrchestrator
    from .protocol import (
        AgentRole,
        LLMProvider,
        Message,
        MessageRole,
        Scenario,
        ScenarioStep,
    )
except ImportError:
    # Fallback: direct script execution (python python/multi_agent/examples.py)
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from python.multi_agent.guardrails import Guardrails
    from python.multi_agent.orchestrator import MultiAgentOrchestrator
    from python.multi_agent.protocol import (
        AgentRole,
        LLMProvider,
        Message,
        MessageRole,
        Scenario,
        ScenarioStep,
    )


def example_single_agent():
    """Example: Query a single agent directly."""
    print("\n" + "=" * 80)
    print("EXAMPLE 1: Single Agent Query")
    print("=" * 80)

    # Initialize orchestrator (OpenAI default)
    orchestrator = MultiAgentOrchestrator(provider=LLMProvider.OPENAI)

    # Create user message
    messages = [
        Message(
            role=MessageRole.USER,
            content=(
                "Analyze a loan portfolio with $10M outstanding, "
                "5% delinquency rate, and 2% charge-off rate. "
                "What are the key risks?"
            ),
        )
    ]

    # Run risk analyst
    try:
        response = orchestrator.run_agent(
            role=AgentRole.RISK_ANALYST,
            messages=messages,
            context={"portfolio_size": 10_000_000, "delinquency_rate": 0.05},
        )

        print(f"\n✅ Response from {response.agent_role.value}:")
        print(f"📝 {response.message.content}")
        print("\n📊 Metrics:")
        print(f"   - Tokens: {response.tokens_used}")
        print(f"   - Cost: ${response.cost_usd:.4f}")
        print(f"   - Latency: {response.latency_ms:.0f}ms")
        print(f"   - Provider: {response.provider.value}")
        print(f"   - Model: {response.model}")

        return response

    except (ValueError, RuntimeError, ConnectionError) as e:
        print(f"❌ Error: {e}")
        return None


def example_scenario_execution():
    """Example: Run a predefined multi-agent scenario."""
    print("\n" + "=" * 80)
    print("EXAMPLE 2: Multi-Agent Scenario Execution")
    print("=" * 80)

    orchestrator = MultiAgentOrchestrator(provider=LLMProvider.OPENAI)

    # List available scenarios
    print("\n📋 Available scenarios:")
    for scenario_name in orchestrator.list_scenarios():
        scenario = orchestrator.get_scenario(scenario_name)
        print(f"   - {scenario_name}: {scenario.description}")

    # Run loan risk review scenario
    print("\n🚀 Running 'loan_risk_review' scenario...")

    initial_context = {
        "portfolio_data": """
        Portfolio Summary:
        - Total Outstanding: $50M
        - Number of Loans: 1,250
        - Average Loan Size: $40K
        - Delinquency Rate (30+ days): 6.2%
        - Charge-off Rate: 2.8%
        - Geographic Concentration: 60% California, 20% Texas, 20% Other
        - Product Mix: 70% Personal Loans, 30% Small Business Loans
        """,
    }

    try:
        results = orchestrator.run_scenario(
            scenario_name="loan_risk_review",
            initial_context=initial_context,
        )

        print("\n✅ Scenario completed successfully!\n")

        # Display step outputs
        for key, value in results.items():
            if key.startswith("_"):
                continue
            print(f"📌 {key.upper().replace('_', ' ')}:")
            print(f"{value}\n")

        # Display metadata
        metadata = results["_metadata"]
        print("=" * 80)
        print("📊 SCENARIO METRICS:")
        print(f"   - Trace ID: {metadata['trace_id']}")
        print(f"   - Steps Completed: {metadata['steps_completed']}")
        print(f"   - Total Cost: ${metadata['total_cost_usd']:.4f}")
        print(f"   - Total Tokens: {metadata['total_tokens']}")
        print("=" * 80)

        return results

    except (ValueError, RuntimeError, KeyError) as e:
        print(f"❌ Scenario failed: {e}")
        return None


def example_custom_scenario():
    """Example: Create and run a custom scenario."""
    print("\n" + "=" * 80)
    print("EXAMPLE 3: Custom Scenario")
    print("=" * 80)

    orchestrator = MultiAgentOrchestrator(provider=LLMProvider.OPENAI)

    # Define custom scenario
    custom_scenario = Scenario(
        name="customer_acquisition_review",
        description="Review customer acquisition strategy for compliance and risk",
        steps=[
            ScenarioStep(
                agent_role=AgentRole.GROWTH_STRATEGIST,
                prompt_template=(
                    "Propose a customer acquisition strategy for: "
                    "{target_market}. Focus on CAC and LTV."
                ),
                context_keys=["target_market"],
                output_key="acquisition_strategy",
            ),
            ScenarioStep(
                agent_role=AgentRole.COMPLIANCE,
                prompt_template=(
                    "Review this acquisition strategy for fair "
                    "lending compliance: {acquisition_strategy}."
                ),
                context_keys=["acquisition_strategy"],
                output_key="compliance_review",
            ),
            ScenarioStep(
                agent_role=AgentRole.RISK_ANALYST,
                prompt_template=(
                    "Assess credit risk of target market: {target_market} "
                    "with strategy: {acquisition_strategy}."
                ),
                context_keys=["target_market", "acquisition_strategy"],
                output_key="risk_assessment",
            ),
        ],
    )

    # Add custom scenario
    orchestrator.add_scenario(custom_scenario)

    print(f"\n✅ Added custom scenario: {custom_scenario.name}")
    print(f"📋 Description: {custom_scenario.description}")
    print(f"🔄 Steps: {len(custom_scenario.steps)}")

    # Run custom scenario
    initial_context = {
        "target_market": (
            "Millennials (25-40) with income $50K-$100K, credit score "
            "650-720, seeking personal loans $5K-$25K for debt "
            "consolidation."
        ),
    }

    try:
        results = orchestrator.run_scenario(
            scenario_name="customer_acquisition_review",
            initial_context=initial_context,
        )

        print("\n✅ Custom scenario completed!\n")

        for key, value in results.items():
            if not key.startswith("_"):
                print(f"📌 {key.upper().replace('_', ' ')}:")
                print(f"{value}\n")

        metadata = results["_metadata"]
        print(f"💰 Total Cost: ${metadata['total_cost_usd']:.4f}")

        return results

    except (ValueError, RuntimeError, KeyError) as e:
        print(f"❌ Error: {e}")
        return None


def example_pii_redaction():
    """Example: PII redaction in action."""
    print("\n" + "=" * 80)
    print("EXAMPLE 4: PII Redaction")
    print("=" * 80)

    sensitive_text = """
    Borrower John Doe (SSN: 123-45-6789) applied for a loan.
    Contact: john.doe@example.com, phone 555-123-4567.
    Credit card on file: 4532 1234 5678 9010.
    Business EIN: 12-3456789.
    """

    print("\n🔒 Original text (with PII):")
    print(sensitive_text)

    redacted = Guardrails.redact_pii(sensitive_text)

    print("\n✅ Redacted text (PII removed):")
    print(redacted)

    # Show what was detected
    print("\n📊 PII patterns detected:")
    for pattern_name, pattern in Guardrails.PII_PATTERNS.items():
        matches = pattern.findall(sensitive_text)
        if matches:
            print(f"   - {pattern_name}: {len(matches)} instance(s)")


def example_provider_switching():
    """Example: Switch LLM providers."""
    print("\n" + "=" * 80)
    print("EXAMPLE 5: Provider Switching")
    print("=" * 80)

    providers_to_test = []
    if os.getenv("OPENAI_API_KEY"):
        providers_to_test.append(LLMProvider.OPENAI)
    if os.getenv("ANTHROPIC_API_KEY"):
        providers_to_test.append(LLMProvider.ANTHROPIC)
    if os.getenv("GEMINI_API_KEY"):
        providers_to_test.append(LLMProvider.GEMINI)

    print(f"\nTesting {len(providers_to_test)} provider(s)...")

    for provider in providers_to_test:
        try:
            orchestrator = MultiAgentOrchestrator(provider=provider)
            response = orchestrator.run_agent(
                role=AgentRole.RISK_ANALYST,
                messages=[
                    Message(
                        role=MessageRole.USER,
                        content="In one sentence, what is credit risk?",
                    )
                ],
            )
            print(
                f"  Success! Response: {response.message.content[:100]}... "
                f"Cost: ${response.cost_usd:.6f}"
            )
        except (ValueError, RuntimeError, ConnectionError) as e:
            print(f"  Failed: {e}")


def run_all_examples():
    """Run all examples."""
    print("\n" + "=" * 80)
    print("🚀 MULTI-AGENT ORCHESTRATOR EXAMPLES")
    print("=" * 80)

    # Check API keys
    if not os.getenv("OPENAI_API_KEY"):
        print("\n⚠️  WARNING: OPENAI_API_KEY not set. Examples will fail.")
        print("   Set it with: export OPENAI_API_KEY=your_key_here")
        return

    print("\n✅ Environment check passed")
    print(f"   - OpenAI: {'✓' if os.getenv('OPENAI_API_KEY') else '✗'}")
    print(f"   - Anthropic: {'✓' if os.getenv('ANTHROPIC_API_KEY') else '✗'}")
    print(f"   - Gemini: {'✓' if os.getenv('GEMINI_API_KEY') else '✗'}")

    # Run examples
    try:
        example_single_agent()
        example_pii_redaction()
        example_provider_switching()

        print("\n" + "=" * 80)
        print("✅ All examples completed successfully!")
        print("=" * 80 + "\n")

    except KeyboardInterrupt:
        print("\n\n⚠️  Examples interrupted by user")
    except (ValueError, RuntimeError, ConnectionError, ImportError) as e:
        print(f"\n\n❌ Examples failed: {e}")


if __name__ == "__main__":
    run_all_examples()
