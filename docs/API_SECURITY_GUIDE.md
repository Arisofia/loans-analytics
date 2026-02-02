# API Security Guide

**Status**: Production-Ready  
**Last Updated**: February 2, 2026  
**Compliance**: OWASP ASVS, PCI-DSS 3.4, SOC 2

---

## Table of Contents

1. [Overview](#overview)
2. [Authentication & Authorization](#authentication--authorization)
3. [Input Validation](#input-validation)
4. [Rate Limiting](#rate-limiting)
5. [Security Headers](#security-headers)
6. [Error Handling](#error-handling)
7. [Logging & Monitoring](#logging--monitoring)
8. [Data Protection](#data-protection)
9. [API Security Checklist](#api-security-checklist)

---

## Overview

This guide documents security implementations for all APIs in the Abaco Loans Analytics platform, including:

- **Streamlit Dashboard** (Port 8501)
- **Supabase Edge Functions** (Serverless endpoints)
- **Internal APIs** (Analytics, Pipeline triggers)

### Security Architecture

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │ HTTPS
┌──────▼──────┐
│ Load Balancer│ ← Rate Limiting
└──────┬──────┘
       │
┌──────▼──────┐
│   Nginx     │ ← Security Headers, WAF
└──────┬──────┘
       │
┌──────▼──────┐
│ Application │ ← Input Validation, Auth
└──────┬──────┘
       │
┌──────▼──────┐
│  Database   │ ← Row-Level Security
└─────────────┘
```

---

## Authentication & Authorization

### JWT Authentication (Supabase)

**Implementation**: `supabase/functions/_shared/cors.ts`

```typescript
import { createClient } from '@supabase/supabase-js';

export async function authenticateRequest(req: Request): Promise<User | null> {
  const authHeader = req.headers.get('authorization');
  
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return null;
  }
  
  const token = authHeader.replace('Bearer ', '');
  const supabase = createClient(
    Deno.env.get('SUPABASE_URL')!,
    Deno.env.get('SUPABASE_ANON_KEY')!
  );
  
  const { data: { user }, error } = await supabase.auth.getUser(token);
  
  if (error || !user) {
    return null;
  }
  
  return user;
}
```

**Usage in Edge Functions**:

```typescript
// supabase/functions/figma-kpis/index.ts
Deno.serve(async (req) => {
  const corsResponse = handleCors(req);
  if (corsResponse) return corsResponse;
  
  // Authenticate request
  const user = await authenticateRequest(req);
  if (!user) {
    return new Response('Unauthorized', { status: 401 });
  }
  
  // Process authenticated request
  // ...
});
```

### Role-Based Access Control (RBAC)

**Database-Level** (Supabase RLS):

```sql
-- Enable Row-Level Security
ALTER TABLE fact_loans ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see their own organization's loans
CREATE POLICY "org_access" ON fact_loans
  FOR SELECT
  USING (
    auth.jwt() ->> 'org_id' = organization_id::text
  );

-- Policy: Admin role can see all loans
CREATE POLICY "admin_access" ON fact_loans
  FOR ALL
  USING (
    auth.jwt() ->> 'role' = 'admin'
  );
```

**Application-Level** (Python):

```python
from functools import wraps
from typing import Callable, List

def require_role(allowed_roles: List[str]):
    """Decorator to enforce role-based access control."""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(user, *args, **kwargs):
            if not user or user.get('role') not in allowed_roles:
                raise PermissionError(
                    f"Access denied. Required roles: {allowed_roles}"
                )
            return func(user, *args, **kwargs)
        return wrapper
    return decorator

# Usage:
@require_role(['admin', 'analyst'])
def get_sensitive_metrics(user, metric_id: str):
    # ... fetch metrics ...
    pass
```

### API Key Authentication (Alternative)

For machine-to-machine communication:

```python
import hashlib
import hmac
import os

def verify_api_key(request_api_key: str) -> bool:
    """Verify API key using constant-time comparison."""
    expected_key = os.getenv('API_KEY_HASH')
    
    if not expected_key:
        raise ValueError("API_KEY_HASH not configured")
    
    # Constant-time comparison to prevent timing attacks
    return hmac.compare_digest(
        hashlib.sha256(request_api_key.encode()).hexdigest(),
        expected_key
    )

# Usage in endpoint:
def protected_endpoint(api_key: str):
    if not verify_api_key(api_key):
        raise HTTPException(status_code=401, detail="Invalid API key")
    # ... process request ...
```

---

## Input Validation

### Schema Validation (Pydantic)

**Already Implemented**: `python/validation.py`

```python
from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import date

class LoanRequest(BaseModel):
    """Validated loan creation request."""
    
    loan_id: str = Field(..., min_length=5, max_length=50, pattern=r'^[A-Z0-9-]+$')
    amount: float = Field(..., gt=0, le=1_000_000)
    borrower_id: str = Field(..., min_length=5, max_length=50)
    disbursement_date: date
    term_months: int = Field(..., ge=1, le=60)
    interest_rate: float = Field(..., ge=0, le=100)
    
    @validator('interest_rate')
    def validate_interest_rate(cls, v):
        if v < 0.01 or v > 99.99:
            raise ValueError('Interest rate must be between 0.01% and 99.99%')
        return v
    
    @validator('disbursement_date')
    def validate_disbursement_date(cls, v):
        if v > date.today():
            raise ValueError('Disbursement date cannot be in the future')
        return v

# Usage:
def create_loan(request_data: dict):
    try:
        loan = LoanRequest(**request_data)
        # Process validated loan
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.errors())
```

### Path Traversal Prevention

**Already Implemented**: `python/apps/analytics/api/main.py`

```python
import re
from pathlib import Path

def validate_path(path: str, base_dir: str) -> Path:
    """
    Validate file path to prevent directory traversal attacks.
    
    Security checks:
    - No absolute paths
    - No parent directory traversal (..)
    - Character whitelist validation
    - Resolved path must be within base_dir
    """
    # Reject absolute paths
    if path.startswith('/'):
        raise ValueError("Absolute paths not allowed")
    
    # Reject parent traversal
    if '..' in path:
        raise ValueError("Parent directory traversal not allowed")
    
    # Character whitelist (alphanumeric + dash, underscore, slash, dot)
    if not re.match(r'^[a-zA-Z0-9_/.-]+$', path):
        raise ValueError("Invalid characters in path")
    
    # Resolve and validate containment
    base = Path(base_dir).resolve()
    target = (base / path).resolve()
    
    if not str(target).startswith(str(base)):
        raise ValueError("Path escapes base directory")
    
    return target

# Usage:
def read_file(file_path: str):
    try:
        validated_path = validate_path(file_path, '/app/data')
        with open(validated_path, 'r') as f:
            return f.read()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

### SQL Injection Prevention

**Best Practice**: Always use parameterized queries.

```python
from supabase import Client

# ❌ NEVER DO THIS (vulnerable to SQL injection)
def bad_query(supabase: Client, loan_id: str):
    query = f"SELECT * FROM fact_loans WHERE loan_id = '{loan_id}'"
    return supabase.rpc('execute_sql', {'query': query}).execute()

# ✅ CORRECT: Use Supabase query builder
def safe_query(supabase: Client, loan_id: str):
    return supabase.table('fact_loans') \
        .select('*') \
        .eq('loan_id', loan_id) \
        .execute()

# ✅ CORRECT: Parameterized query (if using raw SQL)
def safe_parameterized_query(conn, loan_id: str):
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM fact_loans WHERE loan_id = %s",
        (loan_id,)
    )
    return cursor.fetchall()
```

### XSS Prevention

For Streamlit dashboard (automatic escaping):

```python
import streamlit as st
import html

# Streamlit automatically escapes HTML in most components
st.write(user_input)  # Safe

# If you need to display HTML, sanitize first
from bleach import clean

def display_user_html(user_html: str):
    """Display user-provided HTML safely."""
    allowed_tags = ['p', 'br', 'strong', 'em', 'a']
    allowed_attributes = {'a': ['href', 'title']}
    
    clean_html = clean(
        user_html,
        tags=allowed_tags,
        attributes=allowed_attributes,
        strip=True
    )
    
    st.markdown(clean_html, unsafe_allow_html=True)
```

---

## Rate Limiting

### Implementation Options

#### Option 1: Nginx Rate Limiting (Recommended)

**Configuration**: `nginx-conf/nginx.conf`

```nginx
# Define rate limit zones
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
limit_req_zone $binary_remote_addr zone=dashboard_limit:10m rate=100r/s;
limit_req_zone $binary_remote_addr zone=auth_limit:10m rate=5r/m;

server {
    listen 80;
    server_name api.abaco.com;
    
    # Strict rate limit for authentication endpoints
    location /api/auth/ {
        limit_req zone=auth_limit burst=3 nodelay;
        limit_req_status 429;
        proxy_pass http://backend:8501;
    }
    
    # Moderate rate limit for API endpoints
    location /api/ {
        limit_req zone=api_limit burst=20 nodelay;
        limit_req_status 429;
        proxy_pass http://backend:8501;
    }
    
    # Relaxed rate limit for dashboard
    location / {
        limit_req zone=dashboard_limit burst=200 nodelay;
        limit_req_status 429;
        proxy_pass http://backend:8501;
    }
}
```

#### Option 2: Application-Level Rate Limiting

**Create**: `python/middleware/rate_limiter.py`

```python
from functools import wraps
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Callable, Optional
import threading
import logging

logger = logging.getLogger(__name__)

class TokenBucketRateLimiter:
    """
    Token bucket algorithm for rate limiting.
    More sophisticated than simple counter, allows bursts.
    """
    
    def __init__(
        self,
        rate: int,  # tokens per second
        capacity: int,  # bucket capacity
        window_seconds: int = 60
    ):
        self.rate = rate
        self.capacity = capacity
        self.window = timedelta(seconds=window_seconds)
        self.buckets = defaultdict(lambda: {
            'tokens': capacity,
            'last_update': datetime.now()
        })
        self.lock = threading.Lock()
    
    def _refill_bucket(self, identifier: str) -> None:
        """Refill tokens based on elapsed time."""
        bucket = self.buckets[identifier]
        now = datetime.now()
        elapsed = (now - bucket['last_update']).total_seconds()
        
        # Add tokens based on elapsed time
        new_tokens = elapsed * self.rate
        bucket['tokens'] = min(
            self.capacity,
            bucket['tokens'] + new_tokens
        )
        bucket['last_update'] = now
    
    def is_allowed(self, identifier: str, tokens: int = 1) -> bool:
        """
        Check if request is allowed.
        
        Args:
            identifier: User ID or IP address
            tokens: Number of tokens to consume (default 1)
        
        Returns:
            True if allowed, False if rate limit exceeded
        """
        with self.lock:
            self._refill_bucket(identifier)
            bucket = self.buckets[identifier]
            
            if bucket['tokens'] >= tokens:
                bucket['tokens'] -= tokens
                return True
            
            logger.warning(
                f"Rate limit exceeded for {identifier}. "
                f"Tokens available: {bucket['tokens']:.2f}"
            )
            return False
    
    def get_wait_time(self, identifier: str, tokens: int = 1) -> float:
        """Get time to wait before next request is allowed (seconds)."""
        with self.lock:
            self._refill_bucket(identifier)
            bucket = self.buckets[identifier]
            
            if bucket['tokens'] >= tokens:
                return 0.0
            
            tokens_needed = tokens - bucket['tokens']
            return tokens_needed / self.rate

# Global rate limiters
api_limiter = TokenBucketRateLimiter(rate=10, capacity=20)  # 10/sec, burst 20
auth_limiter = TokenBucketRateLimiter(rate=0.083, capacity=5)  # 5/min, burst 5

def rate_limit(
    limiter: TokenBucketRateLimiter,
    tokens: int = 1,
    error_message: str = "Rate limit exceeded"
):
    """Decorator for rate limiting endpoints."""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Extract identifier from request
            identifier = kwargs.get('user_id') or kwargs.get('ip_address') or 'anonymous'
            
            if not limiter.is_allowed(identifier, tokens):
                wait_time = limiter.get_wait_time(identifier, tokens)
                raise Exception(
                    f"{error_message}. Retry after {wait_time:.1f} seconds."
                )
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

# Usage examples:
@rate_limit(api_limiter, tokens=1)
def get_loan_details(loan_id: str, user_id: str):
    # ... fetch loan details ...
    pass

@rate_limit(auth_limiter, tokens=1, error_message="Too many login attempts")
def login(username: str, password: str, ip_address: str):
    # ... authenticate user ...
    pass
```

#### Option 3: Cloud Provider Rate Limiting

**Azure API Management**:

```xml
<policies>
    <inbound>
        <rate-limit calls="100" renewal-period="60" />
        <rate-limit-by-key calls="10" renewal-period="1" counter-key="@(context.Request.IpAddress)" />
    </inbound>
</policies>
```

**AWS API Gateway**:

```json
{
  "throttle": {
    "rateLimit": 100,
    "burstLimit": 200
  }
}
```

---

## Security Headers

### Nginx Configuration

**File**: `nginx-conf/security-headers.conf`

```nginx
# X-Frame-Options: Prevent clickjacking
add_header X-Frame-Options "SAMEORIGIN" always;

# X-Content-Type-Options: Prevent MIME sniffing
add_header X-Content-Type-Options "nosniff" always;

# X-XSS-Protection: Enable browser XSS filter (legacy browsers)
add_header X-XSS-Protection "1; mode=block" always;

# Referrer-Policy: Control referrer information
add_header Referrer-Policy "strict-origin-when-cross-origin" always;

# Permissions-Policy: Disable unnecessary browser features
add_header Permissions-Policy "geolocation=(), microphone=(), camera=(), payment=(), usb=(), magnetometer=(), gyroscope=()" always;

# Strict-Transport-Security: Enforce HTTPS (only enable after HTTPS is working)
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;

# Content-Security-Policy: Control resource loading
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; img-src 'self' data: https:; font-src 'self' data: https://fonts.gstatic.com; connect-src 'self' https://*.supabase.co wss://*.supabase.co; frame-ancestors 'self'; form-action 'self';" always;

# Remove server header (nginx version disclosure)
server_tokens off;
more_clear_headers Server;
```

### Streamlit Configuration

**File**: `~/.streamlit/config.toml`

```toml
[server]
enableCORS = false
enableXsrfProtection = true
maxUploadSize = 200
maxMessageSize = 200
enableStaticServing = true
enableWebsocketCompression = true

[browser]
gatherUsageStats = false
```

### Supabase Edge Functions

**File**: `supabase/functions/_shared/security-headers.ts`

```typescript
export const securityHeaders = {
  'X-Frame-Options': 'DENY',
  'X-Content-Type-Options': 'nosniff',
  'X-XSS-Protection': '1; mode=block',
  'Referrer-Policy': 'strict-origin-when-cross-origin',
  'Permissions-Policy': 'geolocation=(), microphone=(), camera=()',
  'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
};

export function applySecurityHeaders(response: Response): Response {
  const headers = new Headers(response.headers);
  
  Object.entries(securityHeaders).forEach(([key, value]) => {
    headers.set(key, value);
  });
  
  return new Response(response.body, {
    status: response.status,
    statusText: response.statusText,
    headers,
  });
}
```

---

## Error Handling

### Secure Error Responses

**Principles:**
- ❌ Never expose stack traces to clients
- ❌ Never reveal internal paths or database structure
- ✅ Log detailed errors server-side
- ✅ Return generic errors to clients

**Implementation**: `python/apps/analytics/api/main.py`

```python
import logging
import re
from typing import Any, Dict

logger = logging.getLogger(__name__)

def _sanitize_for_logging(data: Any, max_length: int = 200) -> str:
    """
    Sanitize data for logging to prevent log injection.
    
    Security checks:
    - Remove newlines, carriage returns, tabs
    - Remove ANSI escape codes
    - Remove null bytes
    - Truncate to max_length
    """
    if not isinstance(data, str):
        data = str(data)
    
    # Remove control characters
    data = data.replace('\n', '\\n')
    data = data.replace('\r', '\\r')
    data = data.replace('\t', '\\t')
    data = data.replace('\0', '')
    
    # Remove ANSI escape codes
    data = re.sub(r'\x1b\[[0-9;]*m', '', data)
    
    # Truncate
    if len(data) > max_length:
        data = data[:max_length] + '...'
    
    return data

def handle_error(error: Exception, user_visible: bool = False) -> Dict[str, Any]:
    """
    Handle errors securely.
    
    Args:
        error: The exception to handle
        user_visible: If True, include error message in response
    
    Returns:
        Error response dictionary
    """
    # Log full error server-side
    logger.error(
        f"Error occurred: {type(error).__name__}",
        exc_info=True,
        extra={
            'error_type': type(error).__name__,
            'error_message': _sanitize_for_logging(str(error))
        }
    )
    
    # Return generic error to client
    if user_visible and isinstance(error, (ValueError, PermissionError)):
        return {
            'error': 'Request failed',
            'message': _sanitize_for_logging(str(error), max_length=100),
            'code': 'VALIDATION_ERROR'
        }
    
    return {
        'error': 'Internal server error',
        'message': 'An error occurred processing your request',
        'code': 'INTERNAL_ERROR'
    }

# Usage:
try:
    result = process_request(user_input)
except Exception as e:
    error_response = handle_error(e, user_visible=True)
    return JSONResponse(status_code=500, content=error_response)
```

### Error Codes

| Code | HTTP Status | Description | User-Facing |
|------|-------------|-------------|-------------|
| `VALIDATION_ERROR` | 400 | Invalid input | Yes |
| `UNAUTHORIZED` | 401 | Authentication required | Yes |
| `FORBIDDEN` | 403 | Insufficient permissions | Yes |
| `NOT_FOUND` | 404 | Resource not found | Yes |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests | Yes |
| `INTERNAL_ERROR` | 500 | Server error | No (generic) |
| `DATABASE_ERROR` | 500 | Database failure | No (generic) |
| `TIMEOUT` | 504 | Request timeout | Yes |

---

## Logging & Monitoring

### Secure Logging Practices

**Already Implemented**: `python/logging_config.py`

```python
import logging
from typing import Any, Dict

class SecureFormatter(logging.Formatter):
    """Custom formatter that sanitizes sensitive data."""
    
    SENSITIVE_KEYS = {
        'password', 'token', 'api_key', 'secret', 'authorization',
        'cookie', 'session', 'ssn', 'credit_card'
    }
    
    def format(self, record: logging.LogRecord) -> str:
        # Sanitize extra fields
        if hasattr(record, 'extra'):
            record.extra = self._sanitize_dict(record.extra)
        
        return super().format(record)
    
    def _sanitize_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Replace sensitive values with <redacted>."""
        sanitized = {}
        for key, value in data.items():
            if any(sensitive in key.lower() for sensitive in self.SENSITIVE_KEYS):
                sanitized[key] = '<redacted>'
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_dict(value)
            else:
                sanitized[key] = value
        return sanitized

# Configure logger
logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
handler.setFormatter(SecureFormatter(
    fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
))
logger.addHandler(handler)
logger.setLevel(logging.INFO)
```

### Audit Logging

**Implementation**:

```python
import logging
from datetime import datetime
from typing import Optional

audit_logger = logging.getLogger('audit')

def log_security_event(
    event_type: str,
    user_id: Optional[str],
    action: str,
    resource: str,
    result: str,
    ip_address: Optional[str] = None,
    metadata: Optional[Dict] = None
):
    """
    Log security-relevant events for compliance.
    
    Events to log:
    - Authentication attempts (success/failure)
    - Authorization failures
    - Data access (sensitive resources)
    - Configuration changes
    - Privilege escalations
    """
    audit_logger.info(
        f"Security Event: {event_type}",
        extra={
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': event_type,
            'user_id': user_id or 'anonymous',
            'action': action,
            'resource': resource,
            'result': result,
            'ip_address': ip_address,
            'metadata': metadata or {}
        }
    )

# Usage examples:
log_security_event(
    event_type='AUTH_SUCCESS',
    user_id='user-123',
    action='login',
    resource='web_dashboard',
    result='success',
    ip_address='192.168.1.1'
)

log_security_event(
    event_type='AUTH_FAILURE',
    user_id=None,
    action='login',
    resource='web_dashboard',
    result='failure',
    ip_address='192.168.1.1',
    metadata={'reason': 'invalid_credentials'}
)

log_security_event(
    event_type='DATA_ACCESS',
    user_id='user-123',
    action='read',
    resource='fact_loans',
    result='success',
    metadata={'loan_count': 100}
)
```

---

## Data Protection

### PII Masking

**Already Implemented**: `src/compliance.py`

```python
from typing import Any, Dict
import re

class PIIMasker:
    """Mask personally identifiable information."""
    
    # Regex patterns for PII detection
    SSN_PATTERN = re.compile(r'\b\d{3}-\d{2}-\d{4}\b')
    EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
    PHONE_PATTERN = re.compile(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b')
    CREDIT_CARD_PATTERN = re.compile(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b')
    
    @classmethod
    def mask_text(cls, text: str) -> str:
        """Mask PII in text."""
        text = cls.SSN_PATTERN.sub('XXX-XX-XXXX', text)
        text = cls.EMAIL_PATTERN.sub('[EMAIL REDACTED]', text)
        text = cls.PHONE_PATTERN.sub('XXX-XXX-XXXX', text)
        text = cls.CREDIT_CARD_PATTERN.sub('XXXX-XXXX-XXXX-XXXX', text)
        return text
    
    @classmethod
    def mask_dict(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Mask PII in dictionary values."""
        masked = {}
        for key, value in data.items():
            if isinstance(value, str):
                masked[key] = cls.mask_text(value)
            elif isinstance(value, dict):
                masked[key] = cls.mask_dict(value)
            else:
                masked[key] = value
        return masked

# Usage:
raw_data = "Contact: john.doe@example.com, SSN: 123-45-6789"
masked_data = PIIMasker.mask_text(raw_data)
# Result: "Contact: [EMAIL REDACTED], SSN: XXX-XX-XXXX"
```

### Encryption at Rest

**Database** (Supabase/PostgreSQL):
- Automatic encryption at rest via cloud provider
- TDE (Transparent Data Encryption) enabled

**File Storage** (Azure Blob):

```python
from azure.storage.blob import BlobServiceClient
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential

def upload_encrypted_file(file_path: str, blob_name: str):
    """Upload file with encryption."""
    # Get encryption key from Key Vault
    credential = DefaultAzureCredential()
    vault_client = SecretClient(
        vault_url="https://your-vault.vault.azure.net",
        credential=credential
    )
    encryption_key = vault_client.get_secret("storage-encryption-key").value
    
    # Upload with encryption
    blob_service = BlobServiceClient(
        account_url="https://youraccount.blob.core.windows.net",
        credential=credential
    )
    
    blob_client = blob_service.get_blob_client(
        container="secure-data",
        blob=blob_name
    )
    
    with open(file_path, "rb") as data:
        blob_client.upload_blob(
            data,
            overwrite=True,
            cpk=encryption_key  # Customer-provided key
        )
```

### Encryption in Transit

**Enforce HTTPS** (Nginx):

```nginx
server {
    listen 80;
    server_name api.abaco.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.abaco.com;
    
    # SSL certificates
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    
    # Modern SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256';
    ssl_prefer_server_ciphers off;
    
    # OCSP stapling
    ssl_stapling on;
    ssl_stapling_verify on;
    
    # ... rest of configuration ...
}
```

---

## API Security Checklist

### Pre-Production

- [ ] All endpoints require authentication (except public endpoints)
- [ ] HTTPS enforced (no HTTP allowed)
- [ ] Rate limiting configured for all endpoints
- [ ] Input validation implemented (Pydantic models)
- [ ] SQL injection prevention (parameterized queries)
- [ ] XSS prevention (output encoding)
- [ ] Path traversal prevention (file access validation)
- [ ] CSRF protection enabled (Streamlit: enableXsrfProtection)
- [ ] Security headers configured (X-Frame-Options, CSP, etc.)
- [ ] CORS restricted to specific origins (not `*`)
- [ ] Error messages don't expose sensitive information
- [ ] PII masking enabled in logs
- [ ] Audit logging configured
- [ ] Secrets stored in vault (not environment variables)
- [ ] API documentation up to date
- [ ] Security testing completed (OWASP Top 10)
- [ ] Penetration testing passed
- [ ] Code review completed (security focus)

### Runtime Monitoring

- [ ] Monitor failed authentication attempts
- [ ] Alert on rate limit violations
- [ ] Track API error rates
- [ ] Monitor suspicious activity patterns
- [ ] Log all data access (sensitive resources)
- [ ] Track privilege changes
- [ ] Monitor certificate expiration
- [ ] Alert on security header violations
- [ ] Track API usage by endpoint
- [ ] Monitor response times

### Compliance

- [ ] OWASP ASVS Level 2 compliance verified
- [ ] PCI-DSS 3.4 requirements met (if applicable)
- [ ] SOC 2 controls documented
- [ ] GDPR compliance (data subject rights)
- [ ] Regular security audits scheduled
- [ ] Incident response plan documented
- [ ] Data retention policies implemented
- [ ] Privacy policy published

---

## Additional Resources

- **OWASP Top 10**: https://owasp.org/www-project-top-ten/
- **OWASP ASVS**: https://owasp.org/www-project-application-security-verification-standard/
- **CWE/SANS Top 25**: https://cwe.mitre.org/top25/
- **Supabase Security**: https://supabase.com/docs/guides/platform/security
- **Python Security**: https://python.readthedocs.io/en/stable/library/security_warnings.html

---

**Document Version**: 1.0  
**Maintained By**: Security Team  
**Review Cycle**: Quarterly
