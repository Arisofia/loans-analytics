# GitHub Copilot Agents

This directory contains custom GitHub Copilot agent configurations for the Abaco Loans Analytics platform.

## Available Agents

### Code Optimizer (`code_optimizer.md`)

**Purpose:** Specialized agent for optimizing Python code in fintech lending analytics with focus on performance, security, and financial accuracy.

**Key Features:**

- Performance optimization for large-scale data processing
- Financial calculation accuracy (Decimal vs float)
- PII protection and security best practices
- Compliance with fintech regulatory requirements
- Integration with existing tooling (black, ruff, mypy, pylint)

**When to Use:**

- Optimizing slow data pipeline operations
- Improving KPI calculation performance
- Ensuring financial calculations use proper precision
- Reviewing code for security vulnerabilities
- Optimizing database queries
- Reducing LLM API costs in multi-agent system

**Invocation:**
In GitHub Copilot Chat (VS Code):

```
@code_optimizer Review this function for performance issues
@code_optimizer Optimize this KPI calculation for large datasets
@code_optimizer Check if this financial calculation is using Decimal properly
@code_optimizer Find N+1 query problems in this code
```

**Core Principles:**

1. **Correctness > Performance** - Never sacrifice accuracy for speed in fintech
2. **Security First** - PII protection and financial data safety
3. **Type Safety** - Required type hints for all functions
4. **Structured Logging** - No print() statements, use structured loggers
5. **Test Coverage** - >95% coverage maintained

### Microservice Designer (`microservice_designer.md`)

**Purpose:** Specialized agent for designing distributed microservice architectures using Domain-Driven Design principles.

**Key Features:**

- Domain-Driven Design (DDD) for service boundary definition
- Communication pattern design (sync/async, event-driven)
- Data management strategies (database per service, sagas, CQRS)
- Resilience patterns (circuit breakers, retries, timeouts)
- Deployment and operational strategies
- Technology recommendations based on scale
- Context-aware designs for fintech, e-commerce, SaaS

**When to Use:**

- Designing new microservice architectures from scratch
- Breaking down a monolith into microservices
- Defining service boundaries and responsibilities
- Choosing communication patterns between services
- Planning data consistency strategies
- Designing for resilience and fault tolerance
- Planning deployment and operational approach
- Evaluating microservices vs monolith trade-offs

**Invocation:**
In GitHub Copilot Chat (VS Code):

```
@microservice_designer Design a microservice architecture for an e-commerce platform
@microservice_designer How should I decompose this monolith into services?
@microservice_designer What communication pattern should I use between order and payment services?
@microservice_designer Design a saga pattern for distributed transaction handling
@microservice_designer What resilience patterns should I implement?
```

**Core Principles:**

1. **Domain-Driven Design** - Service boundaries aligned with business capabilities
2. **Pragmatism Over Idealism** - Balance theory with practical constraints
3. **Resilience by Design** - Assume failures and design for them
4. **Observability First** - Metrics, logs, and traces from day one
5. **Team Topology** - Architecture follows organizational structure (Conway's Law)

### QA Engineer / TestCraftPro (`qa_engineer.md`)

**Purpose:** Specialized QA Engineer agent for generating comprehensive test plans and test cases for fintech features.

**Key Features:**

- Structured test planning with clarifying questions
- Comprehensive test case generation (functional, security, performance, integration)
- Fintech-specific testing requirements (PII protection, financial accuracy, compliance)
- Integration with pytest and CI/CD infrastructure
- Risk-based testing approach (prioritize high-impact areas)
- Test templates and documentation

**When to Use:**

- Generating test plans for new features
- Creating detailed test cases for user stories
- Planning security and compliance testing
- Designing performance test scenarios
- Validating financial calculation accuracy
- Setting up integration test strategies
- Reviewing test coverage and quality

**Invocation:**
In GitHub Copilot Chat (VS Code):

```
@qa_engineer Generate a test plan for the new KPI calculation feature
@qa_engineer Create test cases for the loan approval API endpoint
@qa_engineer What security tests should I include for this payment processing feature?
@qa_engineer Help me test this data pipeline for performance with large datasets
@qa_engineer Review this test plan and suggest improvements
@qa_engineer What edge cases should I test for this validation logic?
```

**Core Principles:**

1. **Ask Before Assuming** - Start with clarifying questions about requirements
2. **Risk-Based Testing** - Prioritize high-impact, high-likelihood risks (top 3-5)
3. **Security & Compliance First** - PII protection and regulatory requirements
4. **Financial Accuracy** - Use Decimal for monetary values, verify against baselines
5. **Automation-Friendly** - Design tests that can be automated with pytest
6. **Balanced Coverage** - Test happy path, edge cases, and error scenarios

**Test Artifacts Generated:**

- Test Plans: `docs/testing/test_plans/[feature]_test_plan.md`
- Test Cases: `docs/testing/test_cases/[feature]_test_cases.md`
- Test Scripts: `tests/` or `python/tests/` (pytest format)

## Agent Configuration Format

Agents are defined using YAML frontmatter at the top of Markdown files:

```yaml
---
name: agent_name
description: Brief description of agent capabilities
target: vscode
tools:
  - read
  - edit
  - search
  - grep
  - bash
user-invokable: true
metadata:
  team: Engineering
  version: 1.0.0
---
# Agent Instructions

Detailed instructions for the agent...
```

## Adding New Agents

1. Create a new `.md` file in this directory
2. Add YAML frontmatter with agent configuration
3. Write comprehensive instructions below the frontmatter
4. Test the agent with common use cases
5. Update this README with agent details

## References

- [GitHub Copilot Custom Agents Documentation](https://docs.github.com/en/copilot/reference/custom-agents-configuration)
- [How to Write Great Agents](https://github.blog/ai-and-ml/github-copilot/how-to-write-a-great-agents-md-lessons-from-over-2500-repositories/)
- Project Copilot Instructions: `.github/copilot-instructions.md`

## Notes

- Agents are automatically available in VS Code when using GitHub Copilot
- Use `@agent_name` in chat to invoke specific agents
- Agents have access to repository context and specified tools
- Agent configurations are version-controlled with the repository
