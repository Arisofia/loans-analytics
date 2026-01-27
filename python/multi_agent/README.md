# Multi-Agent System Documentation

## Architecture Overview
This multi-agent system is designed to facilitate complex interactions and decision-making processes through coordinated agents.

## Quick Start
To get started, clone the repository and install the required dependencies:
```bash
git clone https://github.com/Arisofia/abaco-loans-analytics.git
cd abaco-loans-analytics
pip install -r requirements.txt
```

## Usage Examples
### Single Agent Query
To initiate a query using a single agent, execute the following command:
```python
from agents import SingleAgent
agent = SingleAgent()
response = agent.query('Your query here')
print(response)
```

### Scenario Execution
Execution of scenarios can be done via the following command:
```python
from scenarios import execute_scenario
execute_scenario('scenario_name')
```

### Custom Scenarios
Custom scenarios can be created by following the predefined structure in the `scenarios` directory. Be sure to define necessary parameters and expected outcomes.

### Configuration via .env
Configuration settings can be managed through a `.env` file. Here’s an example of a `.env` file:
```plaintext
AGENT_COUNT=4
TIMEOUT=30
"""

## List of Agents
1. **Agent A**: Description of Agent A.
2. **Agent B**: Description of Agent B.
3. **Agent C**: Description of Agent C.
4. **Agent D**: Description of Agent D.

## Observability Features
The system includes observability features such as logging, monitoring, and alerting to facilitate tracking and debugging.

## Guardrails
Guardrails are implemented to ensure agents operate within predefined parameters, thereby preventing erroneous actions.

## Migration Guide from Legacy Code
Transitioning from the legacy codebase involves:
1. Reviewing existing functionality.
2. Mapping legacy components to new agent structures.
3. Testing extensively to ensure feature parity.

For further information, refer to the full documentation and API specifications.