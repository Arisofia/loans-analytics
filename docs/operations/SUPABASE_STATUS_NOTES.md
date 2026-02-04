# Supabase Status Notes (Regional Issues)

**Last Updated**: 2026-02-04

---

## Overview

This document tracks external Supabase service issues that may impact Abaco Loans Analytics. Our project is hosted in **eu-west-3 (Paris, AWS)** region.

---

## Yemen Network Incident (2026-02-03)

### Summary

**Incident**: Regional network issues in Yemen  
**Status**: Investigating  
**Start Time**: 2026-02-03  
**Affected Region**: Yemen (specific ISPs)  
**Our Region**: eu-west-3 (Paris) - **Not Affected**

### Details

- **Title**: Regional network issues in Yemen
- **Scope**: Connection failures to `*.supabase.co` domains from specific ISPs in Yemen
- **Root Cause**: Regional network routing issues (external to Supabase)
- **Affected Services**: All Supabase services for users in Yemen via affected ISPs

### Impact on Abaco Loans Analytics

**Status**: ✅ **No Impact**

| Component | Status         | Notes                                                                       |
| --------- | -------------- | --------------------------------------------------------------------------- |
| Database  | ✅ Operational | Hosted in eu-west-3                                                         |
| API       | ✅ Operational | Global CDN functioning normally                                             |
| Auth      | ✅ Operational | No authentication issues                                                    |
| Storage   | ✅ Operational | Read/write operations working                                               |
| Dashboard | ✅ Accessible  | Supabase dashboard accessible from all locations except affected Yemen ISPs |

**Our User Base**: Currently serves Latin America (Mexico, Colombia, Chile) - no users in Yemen.

### Monitoring

1. **Supabase Status Page**: <https://status.supabase.com/>
   - Subscribe to updates: Enable email notifications
   - RSS feed: <https://status.supabase.com/history.rss>

2. **Project Health Dashboard**:
   - URL: <https://supabase.com/dashboard/project/goxdevkqozomyhsyxhte/settings/general>
   - Check "Health" tab for service metrics

3. **Automated Monitoring**:
   ```bash
   # Add to cron or GitHub Actions workflow
   curl -f https://status.supabase.com/api/v2/status.json | jq '.status.indicator'
   # Expected: "none" (no incidents)
   ```

### Action Items

- [x] Verified our project is in eu-west-3 (not affected)
- [x] Confirmed no users in Yemen
- [x] Documented for future reference
- [ ] Enable Supabase status notifications (optional)

### References

- Supabase Status Page: <https://status.supabase.com/>
- Incident Timeline: <https://status.supabase.com/incidents/[incident-id]>

---

## Regional Considerations for Future

### Current Setup

- **Primary Region**: eu-west-3 (Paris, AWS)
- **Backup Strategy**: Database backups via Supabase Pro plan
- **Disaster Recovery**: See [DISASTER_RECOVERY.md](../DISASTER_RECOVERY.md)

### If We Expand to MENA Region

If Abaco expands operations to Middle East/North Africa:

1. **Evaluate Multi-Region Deployment**:
   - Consider Supabase Read Replicas in me-south-1 (Bahrain)
   - Use Fly.io edge regions for API proximity

2. **Network Resilience**:
   - Implement connection pooling with retry logic
   - Add fallback to direct database connection (bypass Supabase SDK)
   - Use Cloudflare or similar CDN for regional caching

3. **Monitoring**:
   - Add regional health checks from MENA locations
   - Alert on connection failures by region

### Testing Network Resilience

```bash
# Test connection from different regions
# Use VPN or cloud instances in target regions

# Example: Test from Yemen via VPN
curl -H "apikey: $SUPABASE_ANON_KEY" \
  -H "Authorization: Bearer $SUPABASE_ANON_KEY" \
  https://goxdevkqozomyhsyxhte.supabase.co/rest/v1/customer_data \
  --max-time 10

# Expected: 200 OK within 10 seconds
# If timeout: Regional network issue
```

---

## Historical Incidents

### 2026-02-03: Yemen Network Issues

- **Duration**: Ongoing (as of 2026-02-04)
- **Impact**: None on our operations
- **Lessons Learned**: Document external dependencies, verify regional hosting

---

## Escalation Process

### If Supabase Service Degradation Occurs

1. **Check Status Page**: <https://status.supabase.com/>
2. **Verify Our Project Health**: Dashboard → Health tab
3. **Check Application Logs**:

   ```bash
   # Review recent errors
   cd /path/to/abaco-loans-analytics
   tail -100 logs/app.log | grep -i "supabase\|database\|connection"
   ```

4. **Fallback Options** (if critical):
   - **Read-Only Mode**: Serve cached data from Redis/CDN
   - **Maintenance Page**: Display status to users
   - **Direct Database Connection**: Use pg connection string (bypass Supabase SDK)

5. **Communication**:
   - Post status update on internal Slack
   - If customer-facing: Email support@abaco.co with ETA
   - Escalate to CTO if downtime >30 minutes

### Contact Information

- **Supabase Support**: support@supabase.com
- **Emergency Slack**: #infra-alerts
- **On-Call Engineer**: See PagerDuty rotation

---

## Useful Commands

### Check Project Region

```bash
# Via Supabase CLI
supabase projects list

# Via API
curl https://api.supabase.com/v1/projects \
  -H "Authorization: Bearer $SUPABASE_ACCESS_TOKEN" \
  | jq '.[] | select(.id=="goxdevkqozomyhsyxhte") | .region'
```

### Monitor Connection Latency

```bash
# Measure API response time
time curl -s -o /dev/null -H "apikey: $SUPABASE_ANON_KEY" \
  https://goxdevkqozomyhsyxhte.supabase.co/rest/v1/customer_data?select=id&limit=1

# Expected: <200ms from North America, <100ms from Europe
```

### Test Database Connection

```bash
# Direct PostgreSQL connection test
psql "$DATABASE_URL" -c "SELECT NOW();"

# Expected: Current timestamp
```

---

**Next Review**: 2026-03-04  
**Owner**: DevOps Team
