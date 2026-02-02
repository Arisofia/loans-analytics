# 🔐 Authentication & User Management Guide

**Complete guide to setting up user authentication for Abaco Loans Analytics platform**

---

## 📋 Overview

This guide covers three authentication approaches:

1. **Streamlit Built-in Auth** (Simplest - for dashboard)
2. **FastAPI OAuth2 + JWT** (Production-grade - for API)
3. **Supabase Auth** (Cloud-ready - integrated solution)

Choose based on your deployment scenario and security requirements.

---

## 🎯 Quick Decision Matrix

| Scenario | Recommended Approach | Setup Time |
|----------|---------------------|------------|
| Internal dashboard only | Streamlit Built-in | 15 min |
| API + Dashboard | FastAPI OAuth2 + Streamlit | 1 hour |
| Cloud deployment | Supabase Auth | 30 min |
| Enterprise SSO | Supabase + SAML/OIDC | 2 hours |

---

## 1️⃣ Streamlit Built-in Authentication

**Best For**: Quick internal deployment, small teams (<20 users)

### Installation

```bash
pip install streamlit-authenticator
```

### Step 1: Generate Password Hashes

```python
# scripts/generate_password_hash.py
import bcrypt

def hash_password(password: str) -> str:
    """Generate bcrypt hash for password."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

if __name__ == "__main__":
    # Generate hashes for your team
    users = {
        "admin": "your_secure_password_here",
        "analyst": "another_password",
        "uploader": "third_password",
    }
    
    print("Add these to .streamlit/secrets.toml:")
    print("\n[passwords]")
    for username, password in users.items():
        hashed = hash_password(password)
        print(f'{username} = "{hashed}"')
```

Run it:
```bash
python scripts/generate_password_hash.py
```

### Step 2: Create Secrets File

Create `.streamlit/secrets.toml`:

```toml
# .streamlit/secrets.toml

[passwords]
# These are bcrypt hashes - NOT plain text passwords
admin = "$2b$12$KIXhs7D0zV5j9v7fXvUOxe7YR7Jx6B9Z1k2L3M4N5O6P7Q8R9S0T1"
analyst = "$2b$12$differenthashhere123456789012345678901234567890123456"
viewer = "$2b$12$anotherhash12345678901234567890123456789012345678901"

[roles]
# Define role capabilities
admin = ["admin", "analyst", "upload", "view"]
analyst = ["analyst", "view"]
viewer = ["view"]

[cookie]
name = "abaco_auth_cookie"
key = "your_random_secret_key_here_min_32_chars"  # Generate with: openssl rand -hex 32
expiry_days = 30
```

**⚠️ Security Note**: Add `.streamlit/secrets.toml` to `.gitignore`!

### Step 3: Implement Auth in Streamlit App

Edit `streamlit_app.py`:

```python
import streamlit as st
import streamlit_authenticator as stauth

# Load credentials from secrets
names = list(st.secrets["passwords"].keys())
usernames = list(st.secrets["passwords"].keys())
hashed_passwords = list(st.secrets["passwords"].values())

# Create authenticator
authenticator = stauth.Authenticate(
    names,
    usernames,
    hashed_passwords,
    st.secrets["cookie"]["name"],
    st.secrets["cookie"]["key"],
    st.secrets["cookie"]["expiry_days"],
)

# Login widget
name, authentication_status, username = authenticator.login("Login", "main")

# Handle authentication states
if authentication_status == False:
    st.error("Username/Password is incorrect")
    st.stop()
elif authentication_status == None:
    st.warning("Please enter your username and password")
    st.stop()

# User is authenticated
st.write(f"Welcome *{name}*!")

# Add logout button in sidebar
authenticator.logout("Logout", "sidebar")

# Check user role for feature access
user_role = st.secrets["roles"].get(username, ["view"])

if "upload" in user_role:
    st.sidebar.markdown("### 📤 Upload Data")
    uploaded_file = st.sidebar.file_uploader("Upload CSV")

if "admin" in user_role:
    st.sidebar.markdown("### ⚙️ Admin Panel")
    if st.sidebar.button("Manage Users"):
        st.info("Admin features coming soon")

# Rest of your dashboard code here...
```

### Step 4: Test

```bash
streamlit run streamlit_app.py
```

Visit `http://localhost:8501` and login with your credentials.

---

## 2️⃣ FastAPI OAuth2 + JWT Authentication

**Best For**: Production APIs, mobile apps, external integrations

### Installation

```bash
pip install python-jose[cryptography] passlib[bcrypt] python-multipart
```

### Step 1: Create Auth Module

Create `python/apps/analytics/api/auth.py`:

```python
"""Authentication module for FastAPI."""

import os
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

# Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Models
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class User(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = None
    roles: list[str] = []

class UserInDB(User):
    hashed_password: str

# Mock database (replace with real database)
fake_users_db = {
    "admin": {
        "username": "admin",
        "full_name": "Admin User",
        "email": "admin@abaco.com",
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # "secret"
        "disabled": False,
        "roles": ["admin", "analyst"],
    },
    "analyst": {
        "username": "analyst",
        "full_name": "Data Analyst",
        "email": "analyst@abaco.com",
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
        "disabled": False,
        "roles": ["analyst"],
    },
}

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Generate password hash."""
    return pwd_context.hash(password)

def get_user(username: str) -> Optional[UserInDB]:
    """Get user from database."""
    if username in fake_users_db:
        user_dict = fake_users_db[username]
        return UserInDB(**user_dict)
    return None

def authenticate_user(username: str, password: str) -> Optional[UserInDB]:
    """Authenticate user credentials."""
    user = get_user(username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """Get current user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError as exc:
        raise credentials_exception from exc
    
    user = get_user(username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Ensure user is active."""
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def require_role(required_role: str):
    """Dependency to check user has required role."""
    async def role_checker(current_user: User = Depends(get_current_active_user)):
        if required_role not in current_user.roles:
            raise HTTPException(
                status_code=403,
                detail=f"Insufficient permissions. Required role: {required_role}"
            )
        return current_user
    return role_checker
```

### Step 2: Add Auth Endpoints to FastAPI

Edit `python/apps/analytics/api/main.py`:

```python
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta

from .auth import (
    authenticate_user,
    create_access_token,
    get_current_active_user,
    require_role,
    Token,
    User,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)

app = FastAPI(title="Abaco Analytics API")

@app.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login endpoint - returns JWT token."""
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """Get current user info."""
    return current_user

# Protected endpoint example
@app.post("/upload")
async def upload_data(
    file: str,  # Simplified - add UploadFile type
    current_user: User = Depends(require_role("analyst"))
):
    """Upload data - requires analyst role."""
    return {
        "status": "success",
        "uploaded_by": current_user.username,
        "message": "Data uploaded successfully"
    }

# Admin-only endpoint example
@app.post("/users")
async def create_user(
    username: str,
    password: str,
    current_user: User = Depends(require_role("admin"))
):
    """Create new user - admin only."""
    # Add user creation logic here
    return {"status": "user created", "username": username}
```

### Step 3: Test API Authentication

Start server:
```bash
cd python/apps/analytics/api
uvicorn main:app --reload
```

Test login:
```bash
# Get token
curl -X POST "http://localhost:8000/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=secret"

# Response: {"access_token": "eyJ...", "token_type": "bearer"}

# Use token for protected endpoint
curl -X GET "http://localhost:8000/users/me" \
  -H "Authorization: Bearer eyJ..."
```

### Step 4: Environment Configuration

Add to `.env.local`:
```bash
# JWT Configuration
JWT_SECRET_KEY="your-random-secret-key-min-32-characters"  # Generate with: openssl rand -hex 32
JWT_ALGORITHM="HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
```

---

## 3️⃣ Supabase Authentication

**Best For**: Cloud deployment, scalable solution, built-in user management

### Prerequisites

You already have Supabase configured! Just need to enable auth features.

### Step 1: Enable Supabase Auth

Visit your Supabase dashboard:
```
https://app.supabase.com/project/goxdevkqozomyhsyxhte/auth/users
```

Enable authentication providers:
- ✅ Email/Password
- Optional: Google, GitHub, Azure AD (SSO)

### Step 2: Create Auth Helper

Create `python/auth/supabase_auth.py`:

```python
"""Supabase authentication helper."""

import os
from typing import Optional

from supabase import create_client, Client

# Initialize Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")  # Use anon key for auth

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def sign_up(email: str, password: str, metadata: dict = None) -> dict:
    """Create new user account."""
    response = supabase.auth.sign_up({
        "email": email,
        "password": password,
        "options": {"data": metadata or {}}
    })
    return response

def sign_in(email: str, password: str) -> dict:
    """Sign in existing user."""
    response = supabase.auth.sign_in_with_password({
        "email": email,
        "password": password
    })
    return response

def sign_out() -> None:
    """Sign out current user."""
    supabase.auth.sign_out()

def get_user() -> Optional[dict]:
    """Get current authenticated user."""
    user = supabase.auth.get_user()
    return user

def reset_password(email: str) -> dict:
    """Send password reset email."""
    response = supabase.auth.reset_password_email(email)
    return response
```

### Step 3: Integrate with Streamlit

```python
# streamlit_app.py with Supabase auth
import streamlit as st
from python.auth.supabase_auth import sign_in, sign_up, get_user, sign_out

# Initialize session state
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.user = None

# Check if user is already logged in
if not st.session_state.authenticated:
    # Show login/signup form
    tab1, tab2 = st.tabs(["Login", "Sign Up"])
    
    with tab1:
        st.subheader("Login")
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        
        if st.button("Login"):
            try:
                response = sign_in(email, password)
                st.session_state.authenticated = True
                st.session_state.user = response.user
                st.rerun()
            except Exception as e:
                st.error(f"Login failed: {str(e)}")
    
    with tab2:
        st.subheader("Sign Up")
        new_email = st.text_input("Email", key="signup_email")
        new_password = st.text_input("Password", type="password", key="signup_password")
        full_name = st.text_input("Full Name")
        
        if st.button("Create Account"):
            try:
                response = sign_up(new_email, new_password, {"full_name": full_name})
                st.success("Account created! Please check your email to verify.")
            except Exception as e:
                st.error(f"Signup failed: {str(e)}")
    
    st.stop()

# User is authenticated - show dashboard
st.sidebar.markdown(f"### Welcome, {st.session_state.user.email}!")

if st.sidebar.button("Logout"):
    sign_out()
    st.session_state.authenticated = False
    st.session_state.user = None
    st.rerun()

# Your dashboard code here...
```

### Step 4: Row Level Security (RLS)

Enable RLS in Supabase for data isolation:

```sql
-- In Supabase SQL Editor

-- Enable RLS on your tables
ALTER TABLE fact_loans ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see their own data
CREATE POLICY "Users can view own loans"
ON fact_loans
FOR SELECT
USING (auth.uid() = user_id);

-- Policy: Admins can see all data
CREATE POLICY "Admins can view all loans"
ON fact_loans
FOR SELECT
USING (
    EXISTS (
        SELECT 1 FROM auth.users
        WHERE auth.uid() = id
        AND raw_user_meta_data->>'role' = 'admin'
    )
);
```

---

## 🔒 Security Best Practices

### Password Requirements

Enforce strong passwords:
```python
import re

def validate_password(password: str) -> tuple[bool, str]:
    """Validate password strength."""
    if len(password) < 12:
        return False, "Password must be at least 12 characters"
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain uppercase letter"
    if not re.search(r"[a-z]", password):
        return False, "Password must contain lowercase letter"
    if not re.search(r"\d", password):
        return False, "Password must contain number"
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Password must contain special character"
    return True, "Password is strong"
```

### Environment Variables

**Never commit secrets!** Always use:

```bash
# .env.local (add to .gitignore)
JWT_SECRET_KEY="..."
SUPABASE_SECRET_API_KEY="..."
GRAFANA_ADMIN_PASSWORD="..."
```

### Token Expiration

- Access tokens: 30 minutes
- Refresh tokens: 7 days
- Session cookies: 30 days

### Rate Limiting

Add rate limiting to prevent brute force:

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/token")
@limiter.limit("5/minute")  # Max 5 login attempts per minute
async def login(...):
    ...
```

---

## 👥 User Roles & Permissions

### Recommended Role Structure

```yaml
Roles:
  admin:
    - Full system access
    - User management
    - Configuration changes
    - All data access
  
  analyst:
    - View all dashboards
    - Run reports
    - Query agents
    - Export data
  
  uploader:
    - Upload data files
    - View own uploads
    - Basic reports
  
  viewer:
    - Read-only dashboard access
    - No data export
    - No agent queries
```

### Implementation Example

```python
# Role-based access control
PERMISSIONS = {
    "admin": ["upload", "view", "export", "manage_users", "configure"],
    "analyst": ["upload", "view", "export", "query_agents"],
    "uploader": ["upload", "view"],
    "viewer": ["view"],
}

def has_permission(user_role: str, permission: str) -> bool:
    """Check if role has permission."""
    return permission in PERMISSIONS.get(user_role, [])
```

---

## 🧪 Testing Authentication

Create test users:

```bash
# Generate test credentials
python scripts/create_test_users.py
```

Test script (`scripts/create_test_users.py`):

```python
"""Create test users for development."""

import bcrypt

def create_test_users():
    users = {
        "admin@test.com": {"password": "Admin123!@#", "role": "admin"},
        "analyst@test.com": {"password": "Analyst123!@#", "role": "analyst"},
        "viewer@test.com": {"password": "Viewer123!@#", "role": "viewer"},
    }
    
    print("Test Users:")
    print("=" * 50)
    for email, data in users.items():
        hashed = bcrypt.hashpw(data["password"].encode(), bcrypt.gensalt())
        print(f"\nEmail: {email}")
        print(f"Password: {data['password']}")
        print(f"Role: {data['role']}")
        print(f"Hash: {hashed.decode()}")

if __name__ == "__main__":
    create_test_users()
```

---

## 📚 Next Steps

1. **Choose authentication method** based on your needs
2. **Implement chosen solution** following steps above
3. **Test with multiple users** using different roles
4. **Enable 2FA** for admin accounts (Supabase supports this)
5. **Set up audit logging** to track user actions
6. **Review security regularly** (quarterly password rotation)

---

## 🆘 Troubleshooting

### "Token has expired"
- Increase `ACCESS_TOKEN_EXPIRE_MINUTES`
- Implement refresh tokens
- Check system clock sync

### "Invalid credentials"
- Verify password hash generation
- Check bcrypt rounds (default: 12)
- Ensure username/email is lowercase

### "CORS errors"
- Add frontend URL to FastAPI CORS middleware
- Check Supabase allowed URLs in dashboard

### "Session not persisting"
- Check cookie settings (secure, httponly, samesite)
- Verify SECRET_KEY is consistent across restarts
- Clear browser cookies and retry

---

**Last Updated**: 2026-02-02  
**Security Review**: Quarterly  
**Contact**: security@abaco.com
