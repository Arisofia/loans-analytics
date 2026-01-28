# Multi-Agent System Change Checklist

**Version**: 1.0.0  
**Purpose**: Protect system integrity during modifications to the multi-agent orchestration system  
**Applies To**: Changes affecting `python/multi_agent/`, agent configurations, or LLM integrations

---

## ⚠️ When to Use This Checklist

Use this checklist for **ANY** change involving:

- ✅ Protocol definitions (`protocol.py`)
- ✅ Guardrails and PII redaction (`guardrails.py`)
- ✅ Orchestrator logic (`orchestrator.py`)
- ✅ Agent implementations (`agents.py`, `base_agent.py`)
- ✅ Tracing and observability (`tracing.py`)
- ✅ Scenario definitions (new or modified scenarios)
- ✅ LLM provider configurations or API keys
- ✅ Test coverage (`tests.py`)

---

## 📋 Pre-Change Checklist

Before making any changes, verify:

- [ ] **Baseline State Confirmed**
  - Current branch is up-to-date with `main`
  - All existing tests pass: `python3 -m pytest python/multi_agent/tests.py -v`
  - No uncommitted changes in multi-agent module

- [ ] **Change Scope Defined**
  - Clear description of what's being changed and why
  - Identified which components are affected (protocol, orchestrator, agents, etc.)
  - Estimated impact on existing scenarios

- [ ] **Security Review Started**
  - Change involves no new PII handling (or PII redaction updated)
  - No hardcoded credentials or API keys
  - No new logging of sensitive data

---

## 🔨 During Implementation

### Code Changes

- [ ] **Protocol Changes** (if applicable)
  - Updated `protocol.py` with new/modified data models
  - Ensured backward compatibility OR documented breaking changes
  - Updated type hints and Pydantic validation

- [ ] **Guardrails Changes** (if applicable)
  - PII redaction patterns updated/tested
  - Input validation logic reviewed
  - Context sanitization working correctly

- [ ] **Orchestrator Changes** (if applicable)
  - Agent routing logic tested
  - Scenario execution flow validated
  - Error handling covers new edge cases

- [ ] **Agent Changes** (if applicable)
  - System prompts reviewed for clarity and security
  - Provider-specific logic (OpenAI/Anthropic/Gemini) tested
  - Token usage and cost implications considered

- [ ] **Tracing Changes** (if applicable)
  - Trace ID generation consistent
  - Cost/token tracking accurate
  - OpenTelemetry compatibility maintained

### Testing

- [ ] **Unit Tests Updated**
  - New tests added for new functionality
  - Modified tests reflect changed behavior
  - All tests pass: `python3 -m pytest python/multi_agent/tests.py -v`
  - Test coverage maintained or improved

- [ ] **Integration Tests** (if applicable)
  - Scenarios tested end-to-end
  - Real LLM API calls tested (with test keys/mocks)
  - Error scenarios covered

- [ ] **Edge Case Testing**
  - Empty inputs handled gracefully
  - Malformed context handled without crashes
  - LLM timeout/failure scenarios tested

### Documentation

- [ ] **Code Comments**
  - Complex logic explained
  - Security decisions documented
  - Performance considerations noted

- [ ] **Documentation Files Updated**
  - `README.md` reflects new capabilities
  - `docs/multi-agent-scenarios.md` updated if scenarios changed
  - `INTEGRATION_STATUS.md` updated if baseline guarantees affected

- [ ] **API Documentation**
  - Function/method signatures documented
  - Parameter types and return values clear
  - Usage examples provided

---

## 🔍 Pre-Commit Verification

Before committing changes:

### Automated Checks

- [ ] **Tests Pass**

  ```bash
  python3 -m pytest python/multi_agent/tests.py -v
  ```

  **Expected**: 21+ tests passed, 0 failed

- [ ] **Linting Clean**

  ```bash
  npm run lint  # For TypeScript/JavaScript changes
  # OR
  python3 -m pylint python/multi_agent/  # For Python changes
  ```

  **Expected**: No errors (warnings acceptable with justification)

- [ ] **Type Checking** (if applicable)
  ```bash
  mypy python/multi_agent/
  ```
  **Expected**: No type errors

### Manual Verification

- [ ] **Security Scan**
  - No new CodeQL alerts introduced
  - No SonarQube issues (or explicitly acknowledged)
  - Secrets scanning clean (no exposed keys)

- [ ] **Observability Check**
  - Trace logs include necessary context
  - Cost/token metrics accurate
  - Error messages actionable

- [ ] **Performance Impact**
  - No significant latency regression
  - Memory usage within acceptable bounds
  - Token usage doesn't spike unexpectedly

---

## 📤 Pull Request Checklist

When creating a PR:

### PR Description Must Include

- [ ] **Change Summary**
  - What was changed and why
  - Which components affected (protocol, orchestrator, agents, etc.)
  - Breaking changes highlighted

- [ ] **Testing Evidence**
  - Test results (screenshot or paste output)
  - Edge cases tested
  - Manual testing performed (if applicable)

- [ ] **Security Assessment**
  - PII handling reviewed
  - No credentials exposed
  - Logging reviewed for sensitive data

- [ ] **Observability Impact**
  - Tracing updated (if needed)
  - Metrics captured (if needed)
  - Documentation updated

- [ ] **Documentation Updates**
  - README.md updated (if needed)
  - Scenario docs updated (if needed)
  - INTEGRATION_STATUS.md updated (if baseline affected)

### PR Labels

Add appropriate labels:

- `multi-agent` - Changes to multi-agent system
- `security` - Security-related changes
- `breaking-change` - Breaking API changes
- `documentation` - Documentation-only changes
- `enhancement` - New features
- `bugfix` - Bug fixes

### Reviewers

Tag appropriate reviewers:

- Multi-agent system maintainer (required)
- Security reviewer (if security implications)
- Data privacy reviewer (if PII handling changed)

---

## ✅ Post-Merge Verification

After PR is merged:

- [ ] **CI/CD Pipeline Green**
  - All GitHub Actions workflows pass
  - No new CodeQL alerts
  - SonarQube scan clean

- [ ] **Deployment Verification** (if deployed)
  - Canary deployment successful
  - Monitoring shows no errors
  - Performance metrics within SLA

- [ ] **Documentation Published**
  - Updated docs visible to team
  - Scenario library reflects changes
  - Examples tested and working

- [ ] **Baseline Updated** (if major change)
  - Consider tagging new baseline release
  - Update INTEGRATION_STATUS.md with new guarantees
  - Update test expectations if needed

---

## 🚨 Rollback Plan

If issues detected post-merge:

### Immediate Actions

1. **Assess Impact**
   - Is production affected?
   - Are users impacted?
   - Is data at risk?

2. **Rollback Steps**

   ```bash
   # Revert the commit
   git revert <commit-hash>

   # Or rollback to previous baseline
   git checkout <baseline-tag>
   ```

3. **Notify Stakeholders**
   - Team notification (Slack/Teams)
   - Incident report filed
   - Root cause analysis initiated

### Prevention

- **Staging Environment**: Test changes in staging before production
- **Feature Flags**: Use flags for risky changes
- **Gradual Rollout**: Deploy to subset of users first

---

## 📊 Quality Gates

All changes must pass these gates:

| Gate              | Requirement                | Tool             |
| ----------------- | -------------------------- | ---------------- |
| **Unit Tests**    | 100% pass rate             | pytest           |
| **Code Coverage** | ≥80% (no decrease)         | pytest-cov       |
| **Linting**       | 0 errors                   | ESLint/pylint    |
| **Security Scan** | 0 new issues               | CodeQL/SonarQube |
| **Type Checking** | 0 errors                   | mypy             |
| **Documentation** | All public APIs documented | Manual review    |

---

## 🎯 Examples

### Example 1: Adding a New Agent

**Checklist Items**:

- [ ] New agent class extends `BaseAgent`
- [ ] System prompt defined and reviewed
- [ ] Added to orchestrator's agent registry
- [ ] Unit tests for agent-specific behavior
- [ ] Added to `AgentRole` enum in protocol
- [ ] Documentation updated with agent capabilities
- [ ] Example scenario created demonstrating agent

### Example 2: Modifying PII Redaction

**Checklist Items**:

- [ ] New PII pattern tested extensively
- [ ] False positive rate acceptable
- [ ] Performance impact measured
- [ ] Tests cover new PII type
- [ ] Documentation lists supported PII types
- [ ] Security team approval obtained

### Example 3: Adding New Scenario

**Checklist Items**:

- [ ] Scenario registered in orchestrator `_init_scenarios()`
- [ ] Context keys documented
- [ ] Output keys documented
- [ ] Added to `docs/multi-agent-scenarios.md`
- [ ] Integration test for scenario end-to-end
- [ ] Cost/token estimate documented
- [ ] Business owner identified

---

## 📞 Support

**Questions about this checklist?**  
Contact: Multi-Agent System Maintainer

**Propose changes to checklist?**  
Submit PR with rationale and updated checklist

**Report issues?**  
Create GitHub issue with `multi-agent` label

---

**Version History**:

- v1.0.0 (Jan 28, 2026) - Initial checklist based on golden baseline
