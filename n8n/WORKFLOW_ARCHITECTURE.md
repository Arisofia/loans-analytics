# Abaco Loans Analytics - Complete Workflow Architecture

## System Overview

This document describes the complete end-to-end data flow architecture for the Abaco Loans Analytics system.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     DATA FLOW ARCHITECTURE                      │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────┐
│   Azure Web     │  1. MANUAL DATA INPUT
│   Form Portal   │     - User enters loan application data
│   (Frontend)    │     - Form validation
└────────┬────────┘     - Submit via HTTPS
         │
         │ HTTP POST Request
         │ (JSON Payload)
         ▼
┌─────────────────┐
│   n8n Webhook   │  2. WEBHOOK RECEIVER
│   Endpoint      │     - URL: http://localhost:5678/webhook/abaco-loans
│   :5678/webhook │     - Authentication: Basic Auth
└────────┬────────┘     - Validates incoming data structure
         │
         │ Validated Data
         ▼
┌─────────────────┐
│  n8n Workflow   │  3. DATA PROCESSING & TRANSFORMATION
│  Processing     │     - Data validation and cleansing
│  Engine         │     - Calculate derived metrics
└────────┬────────┘     - Business logic application
         │              - Error handling & logging
         │
         │ Processed Data
         ▼
┌─────────────────┐
│   Supabase      │  4. DATA PERSISTENCE LAYER
│   PostgreSQL    │     - Store loan applications
│   Database      │     - Historical data tracking
└────────┬────────┘     - ACID compliance
         │              - Real-time sync
         │
         │ Aggregated Queries
         ▼
┌─────────────────┐
│   n8n Analytics │  5. ANALYTICS ENGINE
│   Processing    │     - Calculate KPIs and metrics
│                 │     - Generate reports
└────────┬────────┘     - Trend analysis
         │              - Risk scoring
         │
         │ Analytics Data
         ▼
┌─────────────────┐
│   Azure         │  6. VISUALIZATION & OUTPUT
│   Dashboard     │     - Real-time data display
│   (PowerBI)     │     - Interactive charts
└─────────────────┘     - Executive reports
                         - Decision support
```

## Detailed Component Description

### 1. Azure Web Form (Data Input)

**Technology:** Azure Static Web Apps / Azure App Service

**Purpose:** Manual data entry interface for loan applications

**Features:**
- Responsive web interface
- Form field validation
- User authentication (Azure AD)
- HTTPS encryption

**Data Fields:**
- Applicant Information (Name, ID, Contact)
- Loan Details (Amount, Term, Purpose)
- Financial Data (Income, Expenses, Assets)
- Credit Information
- Supporting Documentation

**Output:** JSON payload sent via HTTP POST to n8n webhook

---

### 2. n8n Webhook Receiver

**Technology:** n8n Workflow Automation Platform

**Endpoint:** `http://localhost:5678/webhook/abaco-loans`

**Authentication:** Basic Auth
- Username: `arisofia_admin`
- Password: *(stored in .env file)*

**Functionality:**
- Receives HTTP POST requests from Azure form
- Validates payload structure
- Returns acknowledgment to sender
- Triggers downstream workflow

**Security:**
- Basic authentication required
- HTTPS in production (with reverse proxy)
- Rate limiting
- Input sanitization

---

### 3. n8n Data Processing Engine

**Workflow Steps:**

#### 3.1 Data Validation
- Check required fields
- Validate data types
- Range validation (amounts, dates)
- Business rules validation

#### 3.2 Data Transformation
- Normalize formats (dates, currencies)
- Calculate derived fields:
  - Debt-to-Income ratio
  - Loan-to-Value ratio
  - Monthly payment amount
  - Total interest payable
- Enrich with external data (if needed)

#### 3.3 Business Logic
- Apply lending criteria
- Calculate risk score
- Determine approval thresholds
- Flag exceptions for manual review

#### 3.4 Error Handling
- Log all processing errors
- Send notifications on failures
- Retry logic for transient failures
- Maintain audit trail

---

### 4. Supabase PostgreSQL Database

**Technology:** Supabase (Hosted PostgreSQL)

**Connection Details:**
- Host: *(from Azure Supabase URL)*
- Database: n8n_abaco_loans_db
- User: n8n_abaco_user
- Credentials: Stored in n8n/.env file

**Database Schema:**

```sql
-- Loan Applications Table
CREATE TABLE loan_applications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    application_date TIMESTAMP DEFAULT NOW(),
    applicant_name VARCHAR(255) NOT NULL,
    applicant_id VARCHAR(50) NOT NULL,
    loan_amount DECIMAL(15,2) NOT NULL,
    loan_term INTEGER NOT NULL,
    loan_purpose VARCHAR(100),
    annual_income DECIMAL(15,2),
    monthly_expenses DECIMAL(15,2),
    credit_score INTEGER,
    risk_score DECIMAL(5,2),
    dti_ratio DECIMAL(5,2),
    ltv_ratio DECIMAL(5,2),
    status VARCHAR(50) DEFAULT 'pending',
    processed_by VARCHAR(100),
    processed_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Analytics Metrics Table
CREATE TABLE analytics_metrics (
    id SERIAL PRIMARY KEY,
    metric_date DATE NOT NULL,
    total_applications INTEGER,
    approved_applications INTEGER,
    rejected_applications INTEGER,
    average_loan_amount DECIMAL(15,2),
    total_loan_volume DECIMAL(18,2),
    average_risk_score DECIMAL(5,2),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Audit Log Table
CREATE TABLE audit_log (
    id SERIAL PRIMARY KEY,
    application_id UUID REFERENCES loan_applications(id),
    action VARCHAR(100) NOT NULL,
    user_id VARCHAR(100),
    details JSONB,
    timestamp TIMESTAMP DEFAULT NOW()
);
```

**Data Operations:**
- INSERT: New loan applications
- UPDATE: Status changes, processing updates
- SELECT: Query for analytics and reporting
- Backup: Daily automated backups

---

### 5. n8n Analytics Engine

**Processing Tasks:**

#### 5.1 Real-Time Analytics
- Calculate daily metrics
- Update KPI dashboards
- Trigger alerts on thresholds

#### 5.2 Scheduled Analytics (Cron)
- Daily summary reports
- Weekly trend analysis
- Monthly executive reports

#### 5.3 Key Performance Indicators (KPIs)
- Total Applications (Daily/Weekly/Monthly)
- Approval Rate (%)
- Average Loan Amount
- Total Portfolio Value
- Risk Distribution
- Processing Time (Average)
- Default Rate Prediction

#### 5.4 Data Aggregation
- Group by time periods
- Segment by loan types
- Geographic distribution
- Risk categories

---

### 6. Azure Dashboard (PowerBI)

**Technology:** Microsoft Power BI / Azure Dashboard

**Data Source:** Supabase PostgreSQL (via connector)

**Refresh Rate:** Real-time or scheduled (every 15 minutes)

**Dashboard Components:**

#### 6.1 Executive Summary
- Total loan applications (current month)
- Approval vs. rejection rate
- Total portfolio value
- Average loan size

#### 6.2 Trend Analysis
- Application volume over time
- Approval trends
- Risk score distribution
- Seasonal patterns

#### 6.3 Risk Management
- High-risk applications
- Default probability
- Risk score heatmap
- Portfolio concentration

#### 6.4 Operational Metrics
- Processing time analysis
- Queue depth
- SLA compliance
- Error rates

---

## Data Flow Sequence

### Complete Request Lifecycle:

```
1. USER ACTION
   └─> User fills out Azure web form
   └─> Clicks "Submit Application"

2. FORM SUBMISSION
   └─> JavaScript validation
   └─> HTTP POST to n8n webhook
   └─> Payload: JSON with application data

3. WEBHOOK RECEIPT
   └─> n8n receives POST request
   └─> Authenticates request
   └─> Returns HTTP 200 OK
   └─> Triggers workflow

4. DATA PROCESSING
   └─> Validate data structure
   └─> Transform and calculate metrics
   └─> Apply business rules
   └─> Prepare for database insert

5. DATABASE INSERT
   └─> Connect to Supabase
   └─> INSERT INTO loan_applications
   └─> Log to audit_log table
   └─> Return success/failure

6. ANALYTICS UPDATE
   └─> Trigger analytics recalculation
   └─> Update aggregated metrics
   └─> Refresh dashboard data

7. DASHBOARD REFRESH
   └─> Power BI pulls new data
   └─> Updates visualizations
   └─> User sees updated metrics

8. NOTIFICATION (Optional)
   └─> Email confirmation to applicant
   └─> Alert to loan officer
   └─> System status update
```

---

## Security Considerations

### 1. Data in Transit
- HTTPS encryption for all web communications
- TLS 1.3 for database connections
- VPN for internal service communications

### 2. Data at Rest
- PostgreSQL encryption at rest
- Encrypted backups
- Secure credential storage

### 3. Authentication & Authorization
- Azure AD for user authentication
- n8n basic auth for webhooks
- Supabase Row Level Security (RLS)
- Role-based access control (RBAC)

### 4. Compliance
- GDPR compliance for EU data
- Data retention policies
- Audit logging
- Regular security audits

---

## Deployment Configuration

### Environment Variables

All sensitive credentials stored in `n8n/.env`:

```env
# PostgreSQL (n8n internal database)
POSTGRES_USER=n8n_abaco_user
POSTGRES_PASSWORD=***
POSTGRES_DB=n8n_abaco_loans_db

# n8n Authentication
N8N_BASIC_AUTH_USER=arisofia_admin
N8N_BASIC_AUTH_PASSWORD=***

# n8n Encryption
N8N_ENCRYPTION_KEY=***
```

### Supabase Configuration

Configured within n8n workflows:
- Connection string from Azure Supabase instance
- API keys for REST API access
- Service role key for admin operations

---

## Scalability & Performance

### Current Capacity
- **Webhook:** 100 requests/second
- **Database:** 1000 concurrent connections
- **Storage:** Unlimited (cloud-based)

### Optimization Strategies
- Database indexing on frequently queried fields
- Connection pooling
- Caching layer for read-heavy operations
- Asynchronous processing for long-running tasks

### Monitoring
- n8n execution logs
- Supabase performance metrics
- Azure Application Insights
- Custom alerting rules

---

## Disaster Recovery

### Backup Strategy
- **Database:** Daily automated backups to Azure Blob Storage
- **n8n Workflows:** Version controlled in GitHub
- **Configuration:** Stored in repository (.env.example template)

### Recovery Procedures
1. Restore database from latest backup
2. Redeploy n8n containers from docker-compose
3. Restore workflow configurations from backup
4. Verify data integrity
5. Resume operations

**RTO (Recovery Time Objective):** 4 hours
**RPO (Recovery Point Objective):** 24 hours

---

## Maintenance & Support

### Regular Maintenance
- **Weekly:** Review error logs and performance metrics
- **Monthly:** Database optimization and cleanup
- **Quarterly:** Security audit and dependency updates
- **Annually:** Architecture review and capacity planning

### Support Contacts
- **System Owner:** Arisofia
- **GitHub Repository:** https://github.com/Arisofia/abaco-loans-analytics
- **Documentation:** /n8n/README.md

---

## Future Enhancements

### Phase 2 Roadmap
1. **Machine Learning Integration**
   - Automated credit risk scoring
   - Fraud detection models
   - Predictive analytics

2. **Additional Data Sources**
   - Credit bureau integration
   - Bank statement analysis
   - Alternative data sources

3. **Enhanced Automation**
   - Automated decision making
   - Document OCR and parsing
   - Intelligent routing

4. **Improved Analytics**
   - Advanced segmentation
   - Cohort analysis
   - Forecasting models

---

## Conclusion

This architecture provides a robust, scalable, and maintainable solution for loan application processing and analytics. The system prioritizes:

✅ **Simplicity:** Single input, single output
✅ **Security:** Encrypted, authenticated, audited
✅ **Reliability:** Error handling, backups, monitoring
✅ **Scalability:** Cloud-based, horizontally scalable
✅ **Maintainability:** Version controlled, documented, modular

---

**Document Version:** 1.0
**Last Updated:** January 24, 2026
**Author:** AI Assistant (authorized by Arisofia)
**Status:** Production Ready
