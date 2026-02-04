# .vscode Directory Policy

## Purpose

This directory contains shared Visual Studio Code workspace settings, extensions, debuggers, and tasks configured for the abaco-loans-analytics repo. It ensures all team members benefit from consistent linting, schema validation, formatting, recommended extensions, and repeatable automation.

## Quick Fix: "No registered task type 'func'" Error

If you see this error when opening the workspace:

```
Error: there is no registered task type 'func'. Did you miss installing an extension that provides a corresponding task provider?
```

**Solution**: Edit `.vscode/tasks.json` and change the Azure Functions task:

From:

```json
{
  "type": "func",
  "command": "host start"
}
```

To:

```json
{
  "type": "shell",
  "command": "func host start",
  "options": { "cwd": "${workspaceFolder}" }
}
```

Or install the recommended extension: `ms-azuretools.vscode-azurefunctions`

## Allowed Files

- `settings.json`: Team-approved shared workspace settings (never user- or machine-specific configs).
- `tasks.json`: Only tasks required for building/testing/cleaning or otherwise improving team workflows.
- `launch.json`: Launch configs must be generic and portable; no hardcoded or private paths.
- `extensions.json`: Only team-approved extension recommendations.

## Available Tasks

- **Run tests (pytest)** - Execute test suite (Cmd+Shift+B default)
- **Coverage** - Run tests with coverage report
- **func: host start** - Start Azure Functions local development server

## Rules

- No personal workspaces or history files.
- Remove any legacy or unused configurations quarterly.
- No secrets, environment details, or file paths outside the repo root.
- Update documentation when adding or changing config.

## Maintenance

- Audited as part of quarterly repo housekeeping.
- All changes require PR and, ideally, review from at least one other engineer.
