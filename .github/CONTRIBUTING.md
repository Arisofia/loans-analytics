# Contributing to Abaco Loans Analytics

Thank you for contributing to the Abaco Loans Analytics project! This guide outlines our development practices to ensure code quality and team collaboration.

## Branch Naming Conventions

Use consistent prefixes for all branches to organize work by category:

```
feat/<description>        # New features
fix/<description>         # Bug fixes
chore/<description>       # Maintenance, dependencies, tooling
docs/<description>        # Documentation updates
refactor/<description>    # Code refactoring without feature changes
test/<description>        # Test additions or improvements
perf/<description>        # Performance improvements
```

### Examples

- `feat/user-authentication`
- `fix/login-button-alignment`
- `chore/update-dependencies`
- `docs/add-api-documentation`
- `refactor/extract-common-utils`

## Commit Message Convention

Follow the Conventional Commits format for clear, semantic commit messages:

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Type

- **feat**: A new feature
- **fix**: A bug fix
- **chore**: Maintenance (dependencies, tooling, etc.)
- **docs**: Documentation changes
- **refactor**: Code refactoring
- **test**: Adding or updating tests
- **perf**: Performance improvements

### Scope (optional)

The scope specifies what part of the codebase is affected:

- `auth`, `ui`, `api`, `database`, `analytics`, `web`, etc.

### Subject

- Use imperative mood ("add", "fix", "improve")
- Don't capitalize first letter
- No period at the end
- Max 50 characters

### Examples

```
feat(auth): add OAuth2 integration
fix(ui): resolve button hover state bug
chore(deps): update npm packages
docs(readme): add setup instructions
refactor(api): extract request validation logic
```

## Pull Request Workflow

### Before Creating a PR

1. Create a new branch with the appropriate prefix
2. Make your changes following commit conventions
3. Squash related commits into logical units
4. Ensure tests pass: `npm run test` or `pytest`
5. Run linting: `npm run lint` or similar

### Creating a PR

1. **One commit per PR**: Use squash-and-merge to keep history clean
2. **Title format**: Follow conventional commits format
3. **Description**: Clearly explain the "why" and "what"
4. **Link issues**: Reference related issues (e.g., "Closes #123")
5. **Request reviewers**: Assign appropriate team members

### PR Review Status

- **Approved**: PR ready for merge
- **Changes Requested**: Address feedback within 3 days or PR will be auto-closed
- **Review Required**: Pending reviewer decision

### Merging

- **Approved PRs**: Merged daily
- **Stale PRs**: Auto-closed after 5 days of inactivity (labeled: `do-not-close`, `important`, `blocked` are exempt)
- **Merge Method**: Squash and merge (one commit per feature)

## Commit Hygiene Best Practices

✅ **DO**

- Write descriptive commit messages
- Keep commits focused and atomic
- Reference issues in commit bodies
- Use clear, specific language

❌ **DON'T**

- Don't use generic messages like "fix bug" or "chore: retrigger CI"
- Don't mix unrelated changes in one commit
- Don't commit without testing
- Don't force-push to shared branches

## Dependency Management

**Dependabot**

- Automatically creates PRs for dependency updates (see .github/dependabot.yml for config)
- Direct dependencies only (not transitive)
- Weekly checks for GitHub Actions, pip, npm (see config for details)
- PRs auto-labeled: `dependencies`, `npm`/`python`/`ci-cd`
- All PRs assigned to `codex` automation agent for initial triage
- Minor and patch updates are grouped to reduce PR noise
- If you add new apps/services or move dependencies to subfolders, update the directory matchers in dependabot.yml
- For critical updates, add a human reviewer or use CODEOWNERS for extra review
- Use branch protection rules to require review/CI for Dependabot PRs

**Escalation:**

- If a Dependabot PR breaks the build or exposes a security issue, escalate to the security contact in SECURITY.md

**Best Practices:**

- Review and merge Dependabot PRs promptly to keep dependencies current
- Document any limitations or customizations in SECURITY.md or this file

## Automation & CI/CD

### GitHub Actions Workflows

- **Auto-close stale PRs**: PRs inactive 5+ days are auto-closed
- **Stale PR label**: Added automatically before closure
- **Exemptions**: PRs labeled `do-not-close`, `important`, `blocked` are not auto-closed

### Quality Gates

All PRs must pass:

- Linting (ESLint, Pylint, etc.)
- Unit tests (Jest, pytest)
- Type checks (TypeScript, mypy)
- Code coverage thresholds
- SonarQube quality gates

## Questions?

Contact the development team or open an issue for clarification.

Thanks for maintaining code quality! 🚀
