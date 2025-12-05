# Contributing

This document outlines the basic steps for creating a pull request. For a more detailed guide on our workflow and governance, please see our [GitHub Workflow Runbook](../docs/GitHub-Workflow-Runbook.md) and [Governance Framework](../GOVERNANCE.md).

## Creating a PR
1. **Squash on merge**: Use squash-and-merge so the main branch history stays clean. Multiple logical commits are fine during development; the final merge will be squashed.
2. **Quality gates**: Run lint/tests and ensure CI (SonarCloud, CodeQL, web/analytics pipelines) is green before requesting review.
3. **Ownership**: Assign yourself, request required reviewers (@codex, @sourcery, @coderabbit, @sonarqube, @gemini, @zencoder), and respond to bot feedback.
4. **Traceability**: Keep changes scoped, with clear commit messages and links to issues or specs.
