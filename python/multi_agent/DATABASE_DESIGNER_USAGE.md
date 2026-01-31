# Database Designer Agent - Usage Example

## Overview

The Database Designer Agent (`DatabaseDesignerAgent`) is a specialized AI agent that provides expert guidance on database design, schema optimization, and data architecture decisions.

## Key Capabilities

- **Database Type Selection**: Recommendations for relational, NoSQL, graph, or hybrid architectures
- **Schema Design**: Both normalized and denormalized designs based on use case
- **Entity Relationships**: Proper constraint modeling and relationship design
- **Indexing Strategy**: Query-pattern-based index recommendations
- **Query Optimization**: Performance tuning and query design guidance
- **Scaling Strategies**: Sharding, partitioning, and replication planning
- **Migration Planning**: Data migration and schema evolution strategies

## Basic Usage

```python
from python.multi_agent import MultiAgentOrchestrator, AgentRole, AgentRequest, Message, MessageRole

# Initialize orchestrator
orchestrator = MultiAgentOrchestrator()

# Create a request for database design guidance
request = AgentRequest(
    trace_id="example-123",
    messages=[
        Message(
            role=MessageRole.USER,
            content="""
            I need to design a database schema for a loan management system that tracks:
            - Loan applications with borrower information
            - Loan repayment schedules and payment history
            - Portfolio risk metrics updated daily
            
            Expected scale: 10,000 loans/month, 5 years of history
            Query patterns: Heavy read on portfolio analytics, moderate write on payments
            """
        )
    ],
    context={
        "domain": "fintech lending",
        "expected_qps": 1000,
        "data_retention": "5 years"
    }
)

# Run the agent
response = orchestrator.run_agent(AgentRole.DATABASE_DESIGNER, request)

# Access the response
print(response.message.content)
print(f"Cost: ${response.cost_usd:.4f}")
print(f"Latency: {response.latency_ms:.2f}ms")
```

## Example Questions

The Database Designer agent can help with:

1. **Schema Design**
   - "Design a schema for tracking loan applications and approvals"
   - "Should I use normalized or denormalized tables for portfolio analytics?"

2. **Indexing**
   - "What indexes should I create for fast loan lookup by borrower ID?"
   - "How should I index time-series payment data for efficient queries?"

3. **Query Optimization**
   - "How can I optimize this query that calculates portfolio-at-risk?"
   - "What's the best way to aggregate daily metrics across millions of loans?"

4. **Architecture Decisions**
   - "Should I use PostgreSQL or MongoDB for storing loan documents?"
   - "When should I consider sharding my loans table?"

5. **Migration Strategy**
   - "How do I migrate from a monolithic schema to microservices?"
   - "What's the safest way to add a new column to a large loans table?"

## Integration with Other Agents

The Database Designer agent works well with:

- **Risk Analyst**: Design schemas that support risk metric calculations
- **Ops Optimizer**: Optimize database performance for operational efficiency
- **Compliance**: Ensure data models meet regulatory requirements

## Response Format

The agent provides structured recommendations including:

- **Schema Definitions**: SQL/DDL or NoSQL schema definitions
- **Index Recommendations**: Specific indexes with justifications
- **Example Queries**: Sample queries for common operations
- **Performance Considerations**: Scalability and optimization tips
- **Migration Steps**: Concrete steps for implementation

## Testing

See `python/multi_agent/test_database_designer_agent.py` for comprehensive test examples.

## Demo Script

Run the demonstration script to see the agent in action:

```bash
PYTHONPATH=. python python/multi_agent/demo_database_designer.py
```
