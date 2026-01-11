# Azure App Service Diagnostics Runbook

## Overview

Azure App Service diagnostics is an interactive troubleshooting experience to resolve web app issues (HTTP 500s, slowness, etc.) without additional configuration.

## Steps to Access

1. Navigate to the **Azure Portal**.
2. Select your **App Service** (e.g., `abaco-analytics-dashboard`).
3. On the sidebar, click **Diagnose and solve problems**.

## Key Diagnostic Categories

- **Availability and Performance**: Troubleshoot app downtime, high CPU, or memory usage.
- **Configuration and Management**: Check for environment variable issues or connectivity gaps.
- **Diagnostic Tools**: Access advanced tools like **Auto-healing** and **Process List**.

## Recommended Tools

- **Auto-healing**: Automatically restarts the app based on request count, memory limits, or HTTP status codes.
- **Change Analysis**: Pinpoint specific code or configuration changes that caused healthy behavior to degrade.
- **Profiler**: Lightweight tool for identifying slowness in production code.

## Proactive Monitoring

Use **Proactive CPU Monitoring** to mitigate high CPU usage by setting threshold rules until the root cause is identified.

---
*Derived from Azure App Service Documentation (2026)*
