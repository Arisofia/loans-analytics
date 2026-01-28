# Abaco Loans Analytics - Unified Documentation

This is the single source of truth for the Abaco Loans Analytics platform.

## Architecture Overview

**Production Flow**: Azure Web Form → n8n → Supabase → Python Multi-Agent System

### Components

1. **Data Ingestion**: Azure Web Forms collect loan application and portfolio data
2. **Workflow Orchestration**: n8n handles data processing, validation, and routing
3. **Data Storage**: Supabase PostgreSQL with real-time subscriptions
4. **Analytics Engine**: Python multi-agent system for:
   - Risk assessment and scoring
   - KPI calculations (PAR-30, PAR-90, Collection Rate)
   - Portfolio health monitoring
   - Automated reporting and alerts

## Multi-Agent System

The Python multi-agent architecture consists of:

### Core Agents
- **Orchestrator Agent**: Coordinates workflow between agents
- **Risk Agent**: Analyzes loan portfolio risk metrics
- **Compliance Agent**: Ensures regulatory compliance
- **Reporting Agent**: Generates automated reports
- **Data Quality Agent**: Validates data integrity

### Agent Protocol
- **Communication**: Event-driven via protocol messages
- **Tracing**: OpenTelemetry instrumentation
- **Error Handling**: Graceful degradation with retry logic
- **Observability**: Azure Monitor integration

## Key Performance Indicators (KPIs)

### Portfolio Health
- **PAR-30** (Portfolio at Risk 30 days): Loans overdue 1-30 days / Total portfolio
- **PAR-90** (Portfolio at Risk 90 days): Loans overdue 90+ days / Total portfolio
- **Collection Rate**: Payments collected / Payments expected
- **Default Rate**: Defaulted loans / Total loans

### Risk Metrics
- **Expected Loss**: Probability of default × Exposure at default × Loss given default
- **Credit Score Distribution**: Risk segmentation across portfolio
- **Concentration Risk**: Exposure to specific sectors/geographies

## Data Models

### Core Tables (Supabase)
```sql
-- Loans table
loans (
  id uuid PRIMARY KEY,
  borrower_id uuid REFERENCES borrowers(id),
  amount numeric,
  status varchar,
  disbursed_at timestamp,
  maturity_date date
)

-- Payments table
payments (
  id uuid PRIMARY KEY,
  loan_id uuid REFERENCES loans(id),
  amount numeric,
  paid_at timestamp,
  status varchar
)

-- Risk assessments
risk_assessments (
  id uuid PRIMARY KEY,
  loan_id uuid REFERENCES loans(id),
  score numeric,
  category varchar,
  assessed_at timestamp
)
```

## Development

### Local Setup
```bash
# Install dependencies
make setup

# Start services
make docker-up

# Run tests
make test

# Format & lint
make format lint
```

### Docker Services
- **n8n**: http://localhost:5678 (Workflow UI)
- **Python Agents**: http://localhost:8000 (API)
- **PostgreSQL**: localhost:5432 (Database)

### Environment Variables
See `.env.example` for required configuration:
- Database credentials
- LLM API keys (OpenAI, Anthropic)
- n8n authentication
- Azure Monitor (optional)

## Deployment

### Prerequisites
- Azure subscription
- Supabase project
- GitHub repository secrets configured

### CI/CD Pipeline
1. **ci.yml**: Code quality checks (lint, format, test)
2. **codeql.yml**: Security scanning
3. **docker-ci.yml**: Build and push Docker images
4. **deploy.yml**: Deploy to production
5. **lint_and_policy.yml**: Policy enforcement
6. **pr-review.yml**: Automated PR reviews
7. **unified_data_pipeline.yml**: Data pipeline validation

### Production Deployment
```bash
# Build Docker image
docker build -t abaco-analytics:latest .

# Deploy to Azure Container Apps / Kubernetes
kubectl apply -f k8s/deployment.yaml

# Monitor deployment
make docker-logs
```

## Security

### Best Practices
- Never commit secrets or credentials
- Use environment variables for all sensitive data
- Enable row-level security (RLS) in Supabase
- Implement API key rotation
- Monitor for security vulnerabilities with CodeQL

### Data Privacy
- PII masking for sensitive fields
- Audit logging for all data access
- Encryption at rest and in transit
- GDPR/CCPA compliance measures

## Monitoring & Observability

### Tracing
- OpenTelemetry instrumentation across all agents
- Distributed tracing for multi-agent workflows
- Azure Monitor integration for production

### Metrics
- Request latency and throughput
- Agent execution time
- Database query performance
- Error rates and types

### Logging
- Structured JSON logging
- Log aggregation via Azure Monitor
- Retention: 30 days (dev), 90 days (prod)

## Testing

### Test Pyramid
- **Unit Tests**: Individual agent logic (`tests/agents/`)
- **Integration Tests**: Multi-agent workflows (`tests/integration/`)
- **End-to-End Tests**: Full pipeline validation (`tests/e2e/`)

### Coverage Requirements
- Minimum 80% code coverage
- 100% coverage for critical paths (risk calculations, compliance)

### Running Tests
```bash
make test              # Run all tests
make test-coverage     # With coverage report
pytest tests/agents/   # Specific test directory
```

## API Reference

### Agents API
```
POST /api/v1/analyze
  - Trigger portfolio analysis
  - Returns: analysis_id, status

GET /api/v1/reports/{id}
  - Retrieve analysis results
  - Returns: KPIs, risk metrics, recommendations

POST /api/v1/webhooks/n8n
  - n8n webhook endpoint
  - Accepts: loan data, triggers processing
```

## Troubleshooting

### Common Issues

**n8n not starting**:
```bash
docker-compose logs n8n
# Check credentials in .env
```

**Agent errors**:
```bash
docker-compose logs python_agents
# Check LLM API keys
# Verify database connection
```

**Database connection issues**:
```bash
# Test connection
psql $DATABASE_URL
# Check Supabase status
```

## Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/name`
3. Make changes with tests
4. Run quality checks: `make format lint test`
5. Submit PR with description

## Support & Resources

- **Repository**: https://github.com/Arisofia/abaco-loans-analytics
- **Issues**: Open GitHub issues for bugs/features
- **Documentation**: This file (docs/UNIFIED.md)
- **Detailed Docs**: See `docs/unified/unified_docs.md`

## Appendix

### Related Documentation
- [DEPLOYMENT.md](../DEPLOYMENT.md) - Deployment procedures
- [SECURITY.md](../SECURITY.md) - Security policies
- [Analytics Vision](Analytics-Vision.md) - Product vision
- [KPI Operating Model](KPI-Operating-Model.md) - KPI definitions
- [Architecture Proposal](architecture_proposal_v2.md) - System design

### Tech Stack
- **Language**: Python 3.11
- **Framework**: LangChain, LangGraph
- **Database**: PostgreSQL (Supabase)
- **Orchestration**: n8n
- **Observability**: OpenTelemetry, Azure Monitor
- **CI/CD**: GitHub Actions
- **Container**: Docker, Docker Compose

### Version History
- **v2.0.0** (2026-01): Production-focused architecture, multi-agent system
- **v1.0.0** (2025): Initial release with Streamlit dashboard
