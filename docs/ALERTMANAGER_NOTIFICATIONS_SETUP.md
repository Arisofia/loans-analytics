# Alertmanager Notifications Setup Guide

## Quick Setup

### 1. Slack Notifications (Recommended)

**Step 1: Create Slack Webhook**

1. Go to https://api.slack.com/apps
2. Create new app → "From scratch"
3. Name: "Abaco Monitoring"
4. Select your workspace
5. Go to "Incoming Webhooks" → Toggle ON
6. "Add New Webhook to Workspace"
7. Select channel (e.g., `#monitoring`)
8. Copy webhook URL

**Step 2: Configure Environment**

```bash
# Add to .env.local
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

**Step 3: Update Alertmanager Config**
Edit `config/alertmanager.yml`:

```yaml
global:
  slack_api_url: '${SLACK_WEBHOOK_URL}'

receivers:
  - name: 'default-notifications'
    slack_configs:
      - channel: '#monitoring'
        title: '{{ .GroupLabels.alertname }}'
        text: |
          {{ range .Alerts }}
          *Summary:* {{ .Annotations.summary }}
          *Description:* {{ .Annotations.description }}
          {{ end }}
        send_resolved: true
```

**Step 4: Restart Alertmanager**

```bash
docker-compose -f docker-compose.monitoring.yml restart alertmanager
```

**Step 5: Test**

```bash
# Send test alert
curl -X POST http://localhost:9093/api/v1/alerts -d '[{
  "labels": {"alertname":"TestAlert","severity":"warning"},
  "annotations": {"summary":"Test alert","description":"This is a test"}
}]'
```

### 2. Email Notifications

**Step 1: Configure SMTP**
For Gmail:

1. Enable "2-Step Verification" in Google Account
2. Generate "App Password": https://myaccount.google.com/apppasswords
3. Copy the 16-character password

**Step 2: Add to Environment**

```bash
# Add to .env.local
SMTP_HOST=smtp.gmail.com:587
SMTP_USER=your.email@gmail.com
SMTP_PASSWORD=your_app_password_here
ALERT_EMAIL_FROM=alerts@abaco.com
CRITICAL_EMAIL_TO=devops@abaco.com
```

**Step 3: Update Alertmanager Config**

```yaml
global:
  smtp_smarthost: '${SMTP_HOST}'
  smtp_from: '${ALERT_EMAIL_FROM}'
  smtp_auth_username: '${SMTP_USER}'
  smtp_auth_password: '${SMTP_PASSWORD}'
  smtp_require_tls: true

receivers:
  - name: 'critical-alerts'
    email_configs:
      - to: '${CRITICAL_EMAIL_TO}'
        subject: '🚨 CRITICAL: {{ .GroupLabels.alertname }}'
```

## Advanced Configuration

### Multi-Channel Routing

Route different alerts to different channels:

```yaml
route:
  receiver: 'default-notifications'
  routes:
    # Critical → #alerts-critical
    - receiver: 'critical-alerts'
      matchers:
        - severity = "critical"

    # Pipeline → #pipeline-alerts
    - receiver: 'pipeline-team'
      matchers:
        - component =~ "pipeline|kpi-engine"

    # Database → #database-alerts
    - receiver: 'database-team'
      matchers:
        - component =~ "database|supabase"

receivers:
  - name: 'critical-alerts'
    slack_configs:
      - channel: '#alerts-critical'
  - name: 'pipeline-team'
    slack_configs:
      - channel: '#pipeline-alerts'
  - name: 'database-team'
    slack_configs:
      - channel: '#database-alerts'
```

### Custom Alert Templates

Create `alertmanager/templates/custom.tmpl`:

```go
{{ define "slack.default.title" }}
🔥 {{ .Status | toUpper }} | {{ .CommonLabels.alertname }}
{{ end }}

{{ define "slack.default.text" }}
{{ range .Alerts }}
*Severity:* {{ .Labels.severity }}
*Component:* {{ .Labels.component }}
*Summary:* {{ .Annotations.summary }}
*Description:* {{ .Annotations.description }}
{{ if .Annotations.action }}
*Action Required:*
```

{{ .Annotations.action }}

```
{{ end }}
*Runbook:* {{ .Annotations.runbook }}
{{ end }}
{{ end }}
```

Reference in `alertmanager.yml`:

```yaml
templates:
  - '/etc/alertmanager/templates/*.tmpl'
```

### Inhibition Rules

Suppress noise from cascading failures:

```yaml
inhibit_rules:
  # Suppress warning if critical is firing
  - source_matchers:
      - severity = "critical"
    target_matchers:
      - severity = "warning"
    equal: ['alertname', 'component']

  # Suppress connection alerts if database is down
  - source_matchers:
      - alertname = "DatabaseDown"
    target_matchers:
      - component = "database"
    equal: ['instance']
```

## Testing Notifications

### 1. Send Test Alert

```bash
curl -X POST http://localhost:9093/api/v1/alerts \
  -H "Content-Type: application/json" \
  -d '[{
    "labels": {
      "alertname": "TestAlert",
      "severity": "warning",
      "component": "test"
    },
    "annotations": {
      "summary": "This is a test alert",
      "description": "Testing notification system"
    },
    "startsAt": "'$(date -u +%Y-%m-%dT%H:%M:%S.000Z)'",
    "endsAt": "'$(date -u -d '+5 minutes' +%Y-%m-%dT%H:%M:%S.000Z)'"
  }]'
```

### 2. Trigger Real Alert

Force a condition that triggers an alert:

```bash
# Trigger high connection count alert
# (requires pipeline to be running)
for i in {1..100}; do
  curl -s http://localhost:9090/metrics > /dev/null &
done
```

### 3. Check Alertmanager UI

```bash
open http://localhost:9093
```

View:

- Active alerts
- Silences
- Alert groups
- Receiver status

## Troubleshooting

### No Notifications Received

1. **Check Alertmanager logs:**

```bash
docker logs alertmanager --tail 50
```

2. **Verify webhook URL:**

```bash
echo $SLACK_WEBHOOK_URL
# Should output: https://hooks.slack.com/services/...
```

3. **Test webhook manually:**

```bash
curl -X POST $SLACK_WEBHOOK_URL \
  -H "Content-Type: application/json" \
  -d '{"text":"Test from Alertmanager"}'
```

4. **Check Alertmanager config:**

```bash
docker exec alertmanager amtool config show
```

5. **Validate routing:**

```bash
docker exec alertmanager amtool config routes show
```

### Alerts Not Firing

1. **Check Prometheus rules:**

```bash
curl http://localhost:9090/api/v1/rules | jq '.data.groups[].rules[] | {alert:.name, state:.state}'
```

2. **View active alerts:**

```bash
curl http://localhost:9090/api/v1/alerts | jq '.data.alerts[]'
```

3. **Check alert evaluation:**

```bash
# In Prometheus UI
open http://localhost:9090/alerts
```

### Email Not Working

1. **Test SMTP credentials:**

```bash
# Using swaks (install: brew install swaks)
swaks --to $CRITICAL_EMAIL_TO \
      --from $ALERT_EMAIL_FROM \
      --server $SMTP_HOST \
      --auth LOGIN \
      --auth-user $SMTP_USER \
      --auth-password $SMTP_PASSWORD \
      --tls
```

2. **Check Gmail App Password:**

- Must be 16 characters (no spaces)
- Must have "2-Step Verification" enabled
- Generate new one if unsure

3. **Firewall/Port Issues:**

```bash
# Test SMTP port
telnet smtp.gmail.com 587
```

## Best Practices

### 1. Alert Fatigue Prevention

- Use appropriate severities (critical/warning/info)
- Set reasonable thresholds (`for: 5m` instead of instant)
- Group related alerts together
- Use inhibition rules to suppress cascading alerts

### 2. Notification Channels

- **Critical alerts**: Slack #alerts-critical + Email + PagerDuty
- **Warnings**: Slack #monitoring (batched)
- **Info**: Log only, no notifications

### 3. Alert Quality

- Every alert must be actionable
- Include clear summary and description
- Provide troubleshooting steps in `action` annotation
- Link to runbook for complex issues

### 4. Testing

- Test notification channels monthly
- Validate alert thresholds match reality
- Review and tune alert rules quarterly

## Example Full Configuration

See `config/alertmanager.yml.example` for a complete production-ready configuration.

## Security Notes

- **Never commit webhook URLs or credentials to git**
- Use environment variables for all secrets
- Rotate webhooks if accidentally exposed
- Limit Slack app permissions to "Incoming Webhooks" only
- Use dedicated email account for alerts (not personal)

## Further Reading

- [Alertmanager Documentation](https://prometheus.io/docs/alerting/latest/alertmanager/)
- [Slack Incoming Webhooks](https://api.slack.com/messaging/webhooks)
- [Gmail App Passwords](https://support.google.com/accounts/answer/185833)
