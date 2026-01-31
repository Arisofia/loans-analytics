# Microservice Designer Agent - Usage Examples

## Overview
The microservice_designer agent (MicroArchitect) is now available for use in VS Code with GitHub Copilot to help design distributed microservice architectures.

## How to Invoke

In GitHub Copilot Chat (VS Code), use the `@microservice_designer` prefix:

### Example 1: Complete Architecture Design
```
@microservice_designer Design a microservice architecture for an e-commerce platform handling 10M users and 50K orders per day. Include service boundaries, communication patterns, and data strategies.
```

### Example 2: Service Decomposition
```
@microservice_designer I have a monolithic lending platform. How should I decompose it into microservices? The main functions are loan origination, underwriting, servicing, and collections.
```

### Example 3: Communication Pattern Selection
```
@microservice_designer What's the best communication pattern between an Order Service and Payment Service? The payment must be confirmed before order confirmation.
```

### Example 4: Data Consistency Strategy
```
@microservice_designer Design a saga pattern for handling a distributed transaction across Order, Payment, and Inventory services.
```

### Example 5: Resilience Design
```
@microservice_designer What resilience patterns should I implement for a Payment Service that calls external payment gateways?
```

### Example 6: Event Schema Design
```
@microservice_designer Design event schemas for an order processing workflow with events like order.created, order.confirmed, order.shipped.
```

### Example 7: Migration Strategy
```
@microservice_designer How do I migrate from our current monolith to microservices without disrupting production? We have 5 engineers and can't do a big-bang rewrite.
```

### Example 8: Technology Selection
```
@microservice_designer Should I use Kafka or RabbitMQ for event-driven communication in a fintech system processing 10K transactions per day?
```

## Agent Capabilities

### Domain-Driven Design
- Identifies bounded contexts in your domain
- Defines clear service boundaries based on business capabilities
- Maps relationships between contexts
- Recommends decomposition strategies

### Communication Patterns
- REST API design with best practices
- gRPC for service-to-service communication
- Event-driven architectures (pub/sub, event sourcing)
- Hybrid approaches (sync + async)
- Message broker selection (Kafka, RabbitMQ, EventBridge)

### Data Management
- Database per service pattern
- Data consistency strategies (sagas, CQRS, event sourcing)
- API composition patterns
- Reference data handling
- Polyglot persistence recommendations

### Resilience Patterns
- Circuit breakers
- Retry with exponential backoff
- Bulkheads
- Timeouts
- Rate limiting
- Graceful degradation and fallbacks

### Deployment & Operations
- Blue-green deployments
- Canary deployments
- Rolling deployments
- Container orchestration (Kubernetes)
- Serverless considerations
- Service mesh (Istio, Linkerd)

### Cross-Cutting Concerns
- Authentication & authorization
- Logging & observability (metrics, logs, traces)
- Configuration management
- Secret management
- API gateway patterns

## Domain Context

The agent understands:
- **Fintech requirements** (strong consistency, audit trails, PII protection)
- **E-commerce patterns** (order processing, inventory management)
- **SaaS architectures** (multi-tenancy, feature flags, billing)
- **Organizational constraints** (team size, DevOps maturity)
- **Scaling considerations** (startup → enterprise)

## Example Conversations

### Example 1: New Microservice Architecture

**User:** 
```
@microservice_designer We're building a new loan management system. Core functions are:
- Loan application and underwriting
- Loan servicing (payments, statements)
- Collections and delinquency management
- Reporting and analytics

Expected scale: 1000 new loans per day, 10K active loans, 5-person engineering team.

Design the microservice architecture.
```

**Agent Response:**
```
Based on your requirements, I recommend a pragmatic microservice architecture:

=== SERVICE BOUNDARIES ===

1. Application Service
   - Loan application intake
   - Document collection
   - Application status tracking
   
2. Underwriting Service
   - Credit decisioning
   - Risk assessment
   - Approval workflow
   
3. Loan Service
   - Loan lifecycle management
   - Amortization schedules
   - Loan status tracking
   
4. Payment Service
   - Payment processing
   - Payment history
   - Transaction management
   
5. Collections Service
   - Delinquency tracking
   - Collection workflows
   - Recovery management
   
6. Reporting Service (CQRS Read Model)
   - Analytics queries
   - Dashboard data
   - Regulatory reports

=== COMMUNICATION PATTERNS ===

Synchronous (REST):
- Application queries
- Underwriting decision API
- Payment processing

Asynchronous (RabbitMQ):
- application.submitted → Underwriting
- loan.approved → Loan Service
- payment.received → Loan Service
- loan.delinquent → Collections

Rationale: RabbitMQ over Kafka due to lower volume and operational simplicity

=== DATA STRATEGY ===

Database per Service (PostgreSQL):
- application_db: Applications, documents
- underwriting_db: Decisions, risk scores
- loan_db: Loans, schedules
- payment_db: Payments, transactions
- collections_db: Delinquencies, actions
- reporting_db: Materialized views (CQRS)

Consistency:
- Loan approval: Orchestrated saga
  1. Underwriting approves
  2. Create loan in Loan Service
  3. Notify customer
  4. On failure: Mark application as failed
  
- Payment processing: Event-driven
  1. Payment received
  2. Update loan balance
  3. Trigger collections if needed

=== RESILIENCE ===

Critical patterns for fintech:
- Circuit breaker on payment gateway calls
- Idempotency keys for all financial transactions
- Retries with exponential backoff
- Audit logging for all state changes
- Decimal precision for all monetary values

=== DEPLOYMENT ===

Recommended for 5-person team:
- Docker Compose for local development
- Kubernetes (EKS/GKE/AKS) for production
- Blue-green deployments for critical services
- Rolling deployments for non-critical

=== PHASED ROLLOUT ===

Phase 1 (MVP): Start with 3 services
- Application + Underwriting (combined initially)
- Loan + Payment (combined initially)
- Reporting (read-only)

Phase 2: Split as team grows
- Separate Application and Underwriting
- Separate Loan and Payment
- Add Collections service

This approach balances microservice benefits with team capacity.
```

### Example 2: Saga Pattern Design

**User:**
```
@microservice_designer Design a saga for order processing across these services:
- Order Service (creates order)
- Payment Service (charges customer)
- Inventory Service (reserves stock)
- Shipping Service (creates shipment)

If any step fails, we need to roll back.
```

**Agent Response:**
```
I recommend an Orchestration-Based Saga for this workflow:

=== SAGA ORCHESTRATOR ===

OrderProcessingSaga (in Order Service or dedicated Saga Service)

Steps:
1. Create Order (status: PENDING)
2. Reserve Payment → PaymentService.reservePayment()
3. Reserve Inventory → InventoryService.reserveStock()
4. Create Shipment → ShippingService.createShipment()
5. Confirm Order (status: CONFIRMED)

Compensating Actions (on failure):
- Step 2 fails → Cancel order
- Step 3 fails → Release payment, cancel order
- Step 4 fails → Release inventory, release payment, cancel order

=== IMPLEMENTATION ===

Saga State Machine:
- PENDING → PAYMENT_RESERVED → INVENTORY_RESERVED → SHIPMENT_CREATED → CONFIRMED
- FAILED states trigger compensations

Event Flow:
```yaml
order.created:
  saga_id: "saga_123"
  order_id: "ord_456"
  status: PENDING

payment.reserved:
  saga_id: "saga_123"
  transaction_id: "txn_789"
  status: SUCCESS

# If payment fails:
payment.failed:
  saga_id: "saga_123"
  reason: "insufficient_funds"
  
# Triggers:
order.cancelled:
  saga_id: "saga_123"
  reason: "payment_failed"
```

=== CODE STRUCTURE ===

```python
class OrderProcessingSaga:
    def __init__(self, order_id, saga_repository):
        self.saga_id = generate_saga_id()
        self.order_id = order_id
        self.state = SagaState.PENDING
        self.repository = saga_repository
    
    async def execute(self):
        try:
            # Step 1: Create order
            await self.create_order()
            
            # Step 2: Reserve payment
            payment_result = await self.reserve_payment()
            if not payment_result.success:
                await self.compensate_payment()
                return SagaResult.FAILED
            
            # Step 3: Reserve inventory
            inventory_result = await self.reserve_inventory()
            if not inventory_result.success:
                await self.compensate_payment()
                await self.compensate_inventory()
                return SagaResult.FAILED
            
            # Step 4: Create shipment
            shipment_result = await self.create_shipment()
            if not shipment_result.success:
                await self.compensate_payment()
                await self.compensate_inventory()
                await self.compensate_shipment()
                return SagaResult.FAILED
            
            # All steps succeeded
            await self.confirm_order()
            return SagaResult.SUCCESS
            
        except Exception as e:
            await self.compensate_all()
            raise
    
    async def compensate_payment(self):
        await payment_service.release_payment(self.order_id)
    
    async def compensate_inventory(self):
        await inventory_service.release_stock(self.order_id)
    
    async def compensate_shipment(self):
        await shipping_service.cancel_shipment(self.order_id)
```

=== PERSISTENCE ===

Store saga state in database:
```sql
CREATE TABLE saga_instances (
    saga_id UUID PRIMARY KEY,
    saga_type VARCHAR(50),
    order_id VARCHAR(100),
    state VARCHAR(20),
    current_step INT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    completed_at TIMESTAMP,
    compensation_started_at TIMESTAMP,
    error_message TEXT
);

CREATE TABLE saga_steps (
    id BIGSERIAL PRIMARY KEY,
    saga_id UUID REFERENCES saga_instances(saga_id),
    step_name VARCHAR(50),
    status VARCHAR(20),
    request_payload JSONB,
    response_payload JSONB,
    executed_at TIMESTAMP,
    error TEXT
);
```

=== OBSERVABILITY ===

Track saga progress:
- Log each step execution
- Emit metrics for saga duration
- Alert on high compensation rate
- Distributed tracing with saga_id

This ensures reliable order processing with automatic rollback on failures.
```

### Example 3: Resilience Pattern Selection

**User:**
```
@microservice_designer My Payment Service calls external payment gateways. Sometimes they timeout or return 500 errors. How should I handle this?
```

**Agent Response:**
```
For a Payment Service calling external gateways, implement multiple resilience patterns:

=== RESILIENCE STRATEGY ===

1. CIRCUIT BREAKER (Primary Pattern)
```python
from circuitbreaker import circuit

@circuit(failure_threshold=5, recovery_timeout=30, expected_exception=PaymentGatewayError)
async def process_payment(payment_request):
    response = await payment_gateway_client.charge(payment_request)
    return response

# Configuration:
# - Open circuit after 5 consecutive failures
# - Stay open for 30 seconds
# - Automatically test recovery with half-open state
```

2. RETRY WITH EXPONENTIAL BACKOFF
```python
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((TimeoutError, ConnectionError))
)
async def call_payment_gateway(request):
    return await gateway.process(request)

# Retry schedule:
# - Attempt 1: Immediate
# - Attempt 2: Wait 2 seconds
# - Attempt 3: Wait 4 seconds
# - Max attempts: 3
```

3. TIMEOUT (Prevent Hanging)
```python
import asyncio

async def process_with_timeout(payment_request):
    try:
        # 5-second timeout for gateway call
        result = await asyncio.wait_for(
            payment_gateway_client.charge(payment_request),
            timeout=5.0
        )
        return result
    except asyncio.TimeoutError:
        logger.error("Payment gateway timeout", extra={
            "payment_id": payment_request.id,
            "gateway": payment_request.gateway
        })
        raise PaymentTimeoutError()
```

4. BULKHEAD (Isolate Resources)
```python
from concurrent.futures import ThreadPoolExecutor

# Separate thread pools per gateway
stripe_pool = ThreadPoolExecutor(max_workers=10, thread_name_prefix="stripe")
paypal_pool = ThreadPoolExecutor(max_workers=10, thread_name_prefix="paypal")

async def process_stripe_payment(request):
    # Limits Stripe calls to 10 concurrent
    return await stripe_pool.submit(call_stripe, request)
```

5. FALLBACK (Graceful Degradation)
```python
async def process_payment_with_fallback(payment_request):
    try:
        # Try primary gateway
        return await process_via_stripe(payment_request)
    except PaymentGatewayError:
        logger.warning("Stripe unavailable, trying fallback")
        try:
            # Fallback to secondary gateway
            return await process_via_paypal(payment_request)
        except PaymentGatewayError:
            # Both failed - queue for later
            await payment_queue.enqueue(payment_request)
            return PaymentResult(status="QUEUED", message="Payment queued for retry")
```

=== IDEMPOTENCY (Critical for Payments) ===

Always use idempotency keys to prevent duplicate charges:

```python
async def process_payment(payment_request):
    # Generate idempotency key from payment_id
    idempotency_key = f"payment_{payment_request.payment_id}"
    
    # Check if already processed
    existing = await payment_repo.get_by_idempotency_key(idempotency_key)
    if existing:
        return existing  # Return cached result
    
    # Process new payment
    result = await payment_gateway.charge(
        amount=payment_request.amount,
        idempotency_key=idempotency_key
    )
    
    # Store result
    await payment_repo.save(result)
    return result
```

=== MONITORING & ALERTING ===

Track gateway health:

```yaml
Metrics:
  - payment_gateway_request_total (counter)
  - payment_gateway_request_duration_seconds (histogram)
  - payment_gateway_errors_total (counter by type)
  - payment_gateway_circuit_breaker_state (gauge: 0=closed, 1=open)

Alerts:
  - Error rate > 5% for 5 minutes → Page on-call
  - Gateway response time p99 > 5s → Warning
  - Circuit breaker open → Critical alert
  - Retry queue depth > 1000 → Warning
```

=== COMPLETE IMPLEMENTATION ===

```python
from circuitbreaker import circuit
from tenacity import retry, stop_after_attempt, wait_exponential
import asyncio
import logging

logger = logging.getLogger(__name__)

class PaymentService:
    def __init__(self, gateway_client, payment_repo):
        self.gateway_client = gateway_client
        self.payment_repo = payment_repo
    
    async def process_payment(self, payment_request):
        # Check idempotency
        idempotency_key = f"payment_{payment_request.payment_id}"
        existing = await self.payment_repo.get_by_key(idempotency_key)
        if existing:
            return existing
        
        try:
            # Process with resilience patterns
            result = await self._process_with_resilience(payment_request)
            await self.payment_repo.save(result, idempotency_key)
            return result
            
        except Exception as e:
            logger.exception("Payment processing failed", extra={
                "payment_id": payment_request.payment_id,
                "error": str(e)
            })
            raise
    
    @circuit(failure_threshold=5, recovery_timeout=30)
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def _process_with_resilience(self, payment_request):
        try:
            result = await asyncio.wait_for(
                self.gateway_client.charge(payment_request),
                timeout=5.0
            )
            return result
        except asyncio.TimeoutError:
            raise PaymentGatewayTimeoutError()
        except Exception as e:
            raise PaymentGatewayError(str(e))
```

This multi-layered approach ensures payment reliability even when gateways are unstable.
```

## Best Practices

1. **Provide Context**: Share scale, team size, and constraints
2. **Be Specific**: Describe exact use case and requirements
3. **Ask Questions**: Let the agent clarify before designing
4. **Iterate**: Refine design based on feedback
5. **Consider Constraints**: Mention organizational and technical limitations

## Integration with Existing Codebase

For Abaco Loans Analytics specifically, the agent can help with:

- **Extracting Services from Monolith**: Breaking up the data pipeline into services
- **Multi-Agent Architecture**: Designing microservices for AI agents
- **Event-Driven KPIs**: Moving from batch to real-time KPI calculation
- **API Design**: Creating APIs for external consumption
- **Migration Strategy**: Strangler fig pattern for gradual transition

## Feedback & Improvements

To suggest improvements to the agent:
1. Open an issue with `[Agent]` prefix
2. Describe architecture scenario not well covered
3. Provide example requirements and desired output

Agent configuration: `.github/agents/microservice_designer.md`
