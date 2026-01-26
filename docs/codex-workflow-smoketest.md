# Codex Workflow Smoke Test

This file exists to trigger PR workflows and confirm Codex automation is running end-to-end.
- Purpose: workflow health check only; no product impact.
- Expected:
  - PR assignee check
  - Codex review
  - Gemini review
  - Vercel preview (may fail if config incomplete)
  - SonarCloud
