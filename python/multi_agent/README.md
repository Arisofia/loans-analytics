# Documentation for Multi-Agent System

## Architecture Overview
The multi-agent system is designed to handle complex tasks by coordinating multiple agents. Each agent is responsible for a specific aspect of the task, allowing for increased efficiency and modularity.

## Quick Start Guide
To get started with the multi-agent system:
1. Clone the repository.
2. Install required dependencies using `pip install -r requirements.txt`.
3. Start the agent using `python main.py`.

## Usage Examples
### Single Agent Queries
```python
response = agent.query('What is the status of the loan?')
print(response)
```

### Scenarios
1. **Loan Application Processing:** The application is processed by multiple agents to ensure a quick turnaround.
2. **Customer Support:** Agents collaborate to provide answers to customer inquiries efficiently.

## Configuration Options
You can configure the agents by modifying the `config.yaml` file. Here you can set options such as:
- Timeout durations
- Logging levels
- Agent-specific parameters

## Agent Descriptions
- **Data Processing Agent:** Handles data extraction and transformation.
- **Decision-Making Agent:** Analyzes data and makes recommendations.
- **Communication Agent:** Manages interactions with users and other systems.

## Observability Features
The system includes logging and monitoring features:
- Logs can be viewed in `logs/` directory.
- Monitoring metrics are available via the integrated dashboard.

## Guardrails Explanation
Guardrails are implemented to ensure safe operation of agents:
- Input validation
- Rate limiting to avoid system overload

## Migration Guide from Legacy Code
To migrate from the legacy system:
1. Review deprecated functions in the legacy code.
2. Replace calls with the corresponding functions in the new system.
3. Test thoroughly to ensure functionality is preserved.

This documentation provides a comprehensive overview of the multi-agent system, enabling you to quickly understand and effectively utilize its features.