# API Security Guide

> **Deployment scope note (2026-03-28):** This repository does not currently include a checked-in deployment workflow. Validate any deployment guidance in this document against the workflows and Dockerfiles actually present in the repository.

## Overview

This guide covers security implementation for the Loans Analytics API, including authentication, authorization, rate limiting, input validation, and compliance with financial data regulations.

**Security Framework**: Defense in depth with multiple layers (network, application, data)

## Authentication

### JWT (JSON Web Tokens)

**Implementation** (see `src/auth.py` if exists, or integrate with your auth module):

```python
import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")  # 256-bit secret
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

def generate_token(user_id: str, roles: list[str]) -> str:
    """Generate JWT token with user claims."""
    payload = {
        "sub": user_id,  # Subject (user ID)
        "roles": roles,  # User roles for RBAC
        "iat": datetime.utcnow(),  # Issued at
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

def verify_token(token: str) -> dict:
    """Verify JWT token and return payload."""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise ValueError("Token has expired")
    except jwt.InvalidTokenError:
        raise ValueError("Invalid token")

def require_auth(f):
    """Decorator to require valid JWT token."""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization")

        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing or invalid Authorization header"}), 401

        token = auth_header.split(" ")[1]

        try:
            payload = verify_token(token)
            request.user_id = payload["sub"]
            request.user_roles = payload["roles"]
        except ValueError as e:
            return jsonify({"error": str(e)}), 401

        return f(*args, **kwargs)

    return decorated
```

**Usage Example**:

```python
from flask import Flask, request
from python.middleware.rate_limiter import rate_limit, auth_limiter

app = Flask(__name__)

@app.route("/api/loans", methods=["GET"])
@require_auth  # Verify JWT
@rate_limit(auth_limiter)  # Apply rate limiting
def get_loans():
    user_id = request.user_id  # Available after @require_auth
    # Query loans for this user...
    return jsonify({"loans": [...]})
```

### Token Lifecycle

**1. Login** (user provides credentials):

```python
@app.route("/api/auth/login", methods=["POST"])
@rate_limit(auth_limiter)  # Protect against brute force
def login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    # Verify credentials (Supabase Auth, bcrypt, etc.)
    user = authenticate_user(email, password)
    if not user:
        return jsonify({"error": "Invalid credentials"}), 401

    # Generate token
    token = generate_token(user["id"], user["roles"])

    return jsonify({
        "access_token": token,
        "token_type": "Bearer",
        "expires_in": JWT_EXPIRATION_HOURS * 3600
    })
```

**2. API Requests** (client includes token):

```bash
curl -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
     https://api.loans.com/api/loans
```

**3. Token Refresh** (before expiration):

```python
@app.route("/api/auth/refresh", methods=["POST"])
@require_auth  # Verify current token
def refresh_token():
    # Issue new token with extended expiration
    new_token = generate_token(request.user_id, request.user_roles)
    return jsonify({"access_token": new_token})
```

## Authorization (RBAC)

### Role Definitions

**Roles** (from lowest to highest privilege):

1. **`viewer`**: Read-only access to dashboards and KPIs
2. **`analyst`**: Full read access + multi-agent queries
3. **`operator`**: Analyst + pipeline execution
4. **`admin`**: Operator + user management + config changes
5. **`super_admin`**: Full system access + audit log access

### Permission Checks

```python
def require_role(required_role: str):
    """Decorator to require specific role."""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not hasattr(request, "user_roles"):
                return jsonify({"error": "Unauthorized"}), 401

            role_hierarchy = ["viewer", "analyst", "operator", "admin", "super_admin"]
            user_max_role = max(
                (role_hierarchy.index(r) for r in request.user_roles if r in role_hierarchy),
                default=-1
            )
            required_index = role_hierarchy.index(required_role)

            if user_max_role < required_index:
                return jsonify({"error": "Insufficient permissions"}), 403

            return f(*args, **kwargs)

        return decorated
    return decorator
```

**Usage**:

```python
@app.route("/api/pipeline/execute", methods=["POST"])
@require_auth
@require_role("operator")  # Only operators and above
def execute_pipeline():
    # Run pipeline...
    pass

@app.route("/api/admin/users", methods=["POST"])
@require_auth
@require_role("admin")  # Only admins and super_admins
def create_user():
    # Create user...
    pass
```

### Database-Level Security (Supabase RLS)

**Row-Level Security (RLS)** ensures users only see their data:

```sql
-- Enable RLS on fact_loans table
ALTER TABLE fact_loans ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see loans from their organization
CREATE POLICY user_org_isolation ON fact_loans
FOR SELECT
USING (
  organization_id = (
    SELECT organization_id FROM users WHERE id = auth.uid()
  )
);

-- Policy: Admins can see all loans
CREATE POLICY admin_full_access ON fact_loans
FOR ALL
USING (
  EXISTS (
    SELECT 1 FROM users
    WHERE id = auth.uid() AND 'admin' = ANY(roles)
  )
);
```

## Rate Limiting

### Implementation

**Rate limiter already implemented** in `python/middleware/rate_limiter.py`:

```python
from python.middleware.rate_limiter import (
    RateLimiter,
    TokenBucketRateLimiter,
    rate_limit,
    api_limiter,      # 100 requests per 10 seconds
    auth_limiter,     # 5 requests per 60 seconds
    dashboard_limiter # Token bucket: 100 rate, 1000 capacity
)
```

### Rate Limit Strategies

**1. Sliding Window** (default for API endpoints):

- Prevents burst attacks
- Use `api_limiter` for general API routes

**2. Token Bucket** (for dashboard/streaming):

- Allows short bursts while maintaining long-term rate
- Use `dashboard_limiter` for real-time dashboards

**3. Per-User Rate Limiting**:

```python
from python.middleware.rate_limiter import RateLimiter

user_rate_limiter = RateLimiter(max_requests=1000, window_seconds=3600)  # 1000/hour

@app.route("/api/multi-agent/query", methods=["POST"])
@require_auth
def query_agent():
    identifier = f"user:{request.user_id}"

    if not user_rate_limiter.is_allowed(identifier):
        return jsonify({
            "error": "Rate limit exceeded",
            "retry_after": user_rate_limiter.window_seconds
        }), 429

    # Process multi-agent query (expensive LLM call)
    ...
```

### Rate Limit Headers (RFC 6585)

**Include rate limit info in responses**:

```python
@app.after_request
def add_rate_limit_headers(response):
    if hasattr(request, "rate_limit_info"):
        info = request.rate_limit_info
        response.headers["X-RateLimit-Limit"] = str(info["limit"])
        response.headers["X-RateLimit-Remaining"] = str(info["remaining"])
        response.headers["X-RateLimit-Reset"] = str(info["reset"])
    return response
```

## Input Validation

### Schema Validation with Pydantic

**Example: Loan creation endpoint**:

```python
from pydantic import BaseModel, Field, validator
from decimal import Decimal
from datetime import date

class LoanCreateRequest(BaseModel):
    borrower_name: str = Field(..., min_length=2, max_length=100)
    amount: Decimal = Field(..., gt=0, decimal_places=2)
    rate: float = Field(..., ge=0.01, le=1.0)  # 1%-100%
    disbursement_date: date

    @validator("borrower_name")
    def validate_name(cls, v):
        if not v.replace(" ", "").isalpha():
            raise ValueError("Name must contain only letters and spaces")
        return v

    @validator("amount")
    def validate_amount(cls, v):
        if v > Decimal("10000000"):  # $10M max
            raise ValueError("Amount exceeds maximum loan size")
        return v

@app.route("/api/loans", methods=["POST"])
@require_auth
@require_role("operator")
def create_loan():
    try:
        loan_data = LoanCreateRequest(**request.get_json())
    except ValidationError as e:
        return jsonify({"errors": e.errors()}), 400

    # Insert into database...
    return jsonify({"loan_id": "..."}), 201
```

### SQL Injection Prevention

**ALWAYS use parameterized queries**:

```python
# ✅ SAFE (parameterized)
from supabase import create_client

supabase = create_client(supabase_url, supabase_anon_key)
result = supabase.table("fact_loans") \
    .select("*") \
    .eq("borrower_name", user_input) \
    .execute()

# ❌ UNSAFE (string concatenation)
query = f"SELECT * FROM fact_loans WHERE borrower_name = '{user_input}'"  # DON'T DO THIS
```

### XSS Prevention

**Sanitize outputs** (especially in Streamlit dashboards):

```python
import bleach

def sanitize_html(text: str) -> str:
    """Remove potentially dangerous HTML tags."""
    allowed_tags = ["b", "i", "u", "em", "strong"]
    return bleach.clean(text, tags=allowed_tags, strip=True)

# In Streamlit
import streamlit as st
user_comment = sanitize_html(user_comment_input)
st.markdown(user_comment, unsafe_allow_html=False)  # safe=False is default
```

## PII Protection

### Guardrails in Multi-Agent System

**PII redaction** is enforced in LLM-facing flows via `python/multi_agent/guardrails.py`:

```python
from python.multi_agent.guardrails import Guardrails

# Before sending text to an LLM
safe_prompt = Guardrails.redact_pii(user_query)

# Example:
# Input: "Analyze loan for juan.perez@empresa.com.mx"
# Output: "Analyze loan for [REDACTED]"
```

For pipeline-side transformations, use the masking/normalization rules implemented in
`src/pipeline/transformation.py` and keep those rules aligned with security policy.

### Audit Logging

**Track all PII access**:

```python
def log_pii_access(user_id: str, resource: str, action: str):
    """Log PII access to compliance audit trail."""
    from datetime import datetime

    supabase.table("audit_logs").insert({
        "user_id": user_id,
        "resource": resource,
        "action": action,
        "timestamp": datetime.utcnow().isoformat(),
        "ip_address": request.remote_addr
    }).execute()

@app.route("/api/loans/<loan_id>", methods=["GET"])
@require_auth
def get_loan(loan_id):
    log_pii_access(request.user_id, f"loan:{loan_id}", "read")
    # Fetch loan...
```

**Query audit logs** (super_admin only):

```sql
-- Recent PII access by user
SELECT * FROM audit_logs
WHERE user_id = 'user_123'
ORDER BY timestamp DESC
LIMIT 100;

-- Suspicious access patterns (high frequency)
SELECT user_id, COUNT(*) as access_count
FROM audit_logs
WHERE timestamp > NOW() - INTERVAL '1 hour'
GROUP BY user_id
HAVING COUNT(*) > 100;
```

## HTTPS/TLS Configuration

### Force HTTPS

**Cloud providers handle TLS termination**, but enforce HTTPS in app:

```python
from flask import redirect, request

@app.before_request
def force_https():
    if not request.is_secure and not request.headers.get("X-Forwarded-Proto") == "https":
        url = request.url.replace("http://", "https://", 1)
        return redirect(url, code=301)
```

### Certificate Management

**Automatic with cloud providers**:

- **Azure Functions**: Azure manages certs (Let's Encrypt)
- **AWS Lambda + API Gateway**: AWS Certificate Manager (ACM)
- **GCP Cloud Run**: Google-managed certs
- **Railway**: Automatic Let's Encrypt certs

**Custom domains**: Add DNS CNAME record pointing to cloud provider hostname.

## CORS (Cross-Origin Resource Sharing)

**Configure CORS for frontend-backend separation**:

```python
from flask_cors import CORS

app = Flask(__name__)

# Production: Restrict to specific origins
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "https://dashboard.loans.com").split(",")

CORS(app, resources={
    r"/api/*": {
        "origins": ALLOWED_ORIGINS,
        "methods": ["GET", "POST", "PUT", "DELETE"],
        "allow_headers": ["Content-Type", "Authorization"],
        "expose_headers": ["X-RateLimit-Limit", "X-RateLimit-Remaining"],
        "max_age": 3600  # Preflight cache duration
    }
})
```

**Testing**:

```bash
# Verify CORS headers
curl -H "Origin: https://dashboard.loans.com" \
     -H "Access-Control-Request-Method: POST" \
     -H "Access-Control-Request-Headers: Content-Type" \
     -X OPTIONS \
     https://api.loans.com/api/loans
```

## Security Headers

**Add security headers to all responses**:

```python
@app.after_request
def add_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response
```

## Secret Management

### Environment Variables

**NEVER commit secrets to Git**:

```bash
# .env file (add to .gitignore)
JWT_SECRET_KEY=your-256-bit-secret
SUPABASE_ANON_KEY=your-anon-key
OPENAI_API_KEY=sk-...
```

**Generate secure secrets**:

```bash
# 256-bit random secret for JWT
openssl rand -hex 32

# Or using Python
python -c "import secrets; print(secrets.token_hex(32))"
```

### Cloud Secret Stores

**Azure Key Vault**:

```python
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

credential = DefaultAzureCredential()
client = SecretClient(vault_url="https://your-vault.vault.azure.net", credential=credential)

jwt_secret = client.get_secret("jwt-secret-key").value
```

**AWS Secrets Manager**:

```python
import boto3

client = boto3.client("secretsmanager")
response = client.get_secret_value(SecretId="prod/loans/jwt-secret")
jwt_secret = response["SecretString"]
```

**GCP Secret Manager**:

```python
from google.cloud import secretmanager

client = secretmanager.SecretManagerServiceClient()
name = "projects/your-project/secrets/jwt-secret/versions/latest"
response = client.access_secret_version(request={"name": name})
jwt_secret = response.payload.data.decode("UTF-8")
```

## Compliance & Regulations

### GDPR (General Data Protection Regulation)

**If serving EU customers**:

1. **Data Portability**: Provide API to export user data

   ```python
   @app.route("/api/users/<user_id>/export", methods=["GET"])
   @require_auth
   @require_role("admin")
   def export_user_data(user_id):
       # Export all user data in JSON format
       data = {...}
       return jsonify(data), 200
   ```

2. **Right to Deletion**: Implement hard delete (not just soft delete)

   ```python
   @app.route("/api/users/<user_id>", methods=["DELETE"])
   @require_auth
   @require_role("admin")
   def delete_user(user_id):
       # Cascade delete all related data
       supabase.table("users").delete().eq("id", user_id).execute()
       log_pii_access(request.user_id, f"user:{user_id}", "delete")
       return "", 204
   ```

3. **Data Minimization**: Only collect necessary PII (already enforced by schema)

### CCPA (California Consumer Privacy Act)

**If serving California customers**:

- Same data portability and deletion requirements as GDPR
- Disclosure of data collection practices (privacy policy)

### PCI DSS (Payment Card Industry)

**If handling credit card data**:

- **Never store full credit card numbers** (use tokenization via Stripe/PayPal)
- **PCI compliance not required** if using third-party payment processor
- If absolutely necessary: Use PCI-compliant hosting (Azure/AWS/GCP are certified)

### Financial Regulations (Mexico-specific)

**CNBV (Comisión Nacional Bancaria y de Valores)**:

- **Audit trail**: 7-year retention (already implemented in `audit_logs` table)
- **Data residency**: Consider storing data in Mexico region (Supabase doesn't have Mexico DC, use AWS `us-west-2` or Azure `South Central US` as closest)
- **Anti-money laundering (AML)**: Implement transaction monitoring (future feature)

## Incident Response

### Security Incident Checklist

**If credentials leaked**:

1. **Immediate**: Rotate all secrets (`JWT_SECRET_KEY`, API keys, database passwords)
2. **Revoke tokens**: Invalidate all JWT tokens (change secret key forces re-login)
3. **Audit logs**: Check `audit_logs` for unauthorized access
4. **Notify users**: Email affected users within 72 hours (GDPR requirement)
5. **Post-mortem**: Document incident in `docs/incidents/YYYY-MM-DD-description.md`

**If unauthorized access detected**:

1. **Isolate**: Disable compromised user account
2. **Investigate**: Query audit logs for scope of breach
3. **Contain**: Review and update firewall rules, rate limits
4. **Recover**: Restore from backup if data corrupted
5. **Report**: Notify relevant authorities if financial data breached

### Monitoring for Threats

**Prometheus alerts** (see `config/rules/security-alerts.yml`):

- Failed login attempts >10 in 5min → Potential brute force
- Rate limit violations >100/hour → DDoS attempt
- Multiple users from same IP → Account sharing or bot
- API calls outside business hours → Suspicious activity

**Application Insights queries**:

```kusto
// Failed authentication attempts
requests
| where timestamp > ago(1h)
| where resultCode == 401
| summarize count() by client_IP
| where count_ > 10
| order by count_ desc
```

## Testing Security

### Automated Security Scans

**GitHub Actions workflow** (already in `.github/workflows/security-scan.yml`):

- **Bandit**: Scans Python code for common vulnerabilities
- **Safety**: Checks dependencies for known CVEs
- **CodeQL**: Semantic code analysis for SQL injection, XSS, etc.

**Run locally**:

```bash
make security-check  # Runs bandit + safety
```

### Penetration Testing

**Manual tests** (use staging environment):

1. **SQL Injection**: Try `' OR '1'='1` in all inputs
2. **XSS**: Try `<script>alert('XSS')</script>` in text fields
3. **CSRF**: Submit forms without valid CSRF token (if implemented)
4. **Rate limiting**: Send 1000 requests to `/api/auth/login` rapidly
5. **JWT tampering**: Modify token payload and replay

**External pentest** (recommended annually):

- Hire third-party security firm (e.g., Cobalt, Synack)
- Budget: $5K-$20K for SMB-scale audit

## Security Checklist (Production Readiness)

- [ ] **JWT_SECRET_KEY**: 256-bit random secret (not default value)
- [ ] **HTTPS**: Enforced (no HTTP allowed)
- [ ] **Rate limiting**: Enabled on all public endpoints
- [ ] **Input validation**: Pydantic schemas on all POST/PUT endpoints
- [ ] **PII masking**: Verified in transformation phase output
- [ ] **Supabase RLS**: Row-level security policies enabled
- [ ] **CORS**: Restricted to production frontend domain
- [ ] **Security headers**: X-Frame-Options, CSP, HSTS configured
- [ ] **Secret management**: Using cloud secret store (not .env in production)
- [ ] **Audit logging**: All PII access logged to `audit_logs` table
- [ ] **Dependency scanning**: `make security-check` passes in CI/CD
- [ ] **Monitoring**: Prometheus alerts configured for security events
- [ ] **Backup**: Database backups enabled (30-day retention)
- [ ] **Incident response**: Runbook documented in `runbooks/security-incident.md`
- [ ] **Penetration test**: Completed within last 12 months

---

**Last Updated**: 2026-02-02  
**Maintained By**: Security Team  
**Review Frequency**: Quarterly + after each security incident
