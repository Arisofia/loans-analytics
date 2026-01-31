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
infer: true
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
