# .vscode Directory Policy

## Purpose

This directory contains shared Visual Studio Code workspace settings, extensions, debuggers, and tasks configured for the abaco-loans-analytics repo. It ensures all team members benefit from consistent linting, schema validation, formatting, recommended extensions, and repeatable automation.

## Allowed Files

- `settings.json`: Team-approved shared workspace settings (never user- or machine-specific configs).
- `tasks.json`: Only tasks required for building/testing/cleaning or otherwise improving team workflows.
- `launch.json`: Launch configs must be generic and portable; no hardcoded or private paths.
- `extensions.json`: Only team-approved extension recommendations.

## Rules

- No personal workspaces or history files.
- Remove any legacy or unused configurations quarterly.
- No secrets, environment details, or file paths outside the repo root.
- Update documentation when adding or changing config.

## Maintenance

- Audited as part of quarterly repo housekeeping.
- All changes require PR and, ideally, review from at least one other engineer.
