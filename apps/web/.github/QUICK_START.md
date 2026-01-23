# Deployment Quick Start Guide

**TL;DR**: Developers just push code. Automation handles the rest.

---

## Your Daily Workflow

```bash
# 1. Start
git checkout develop
git pull
pnpm install
pnpm dev

# 2. Make changes
# Edit files...

# 3. Before push
pnpm check-all    # Lint + type-check + format
npm test          # Run tests

# 4. Push
git push origin feature/your-feature

# 5. Create PR
# GitHub → Create Pull Request

# 6. Done
# CI validates automatically
# Code review happens
# CI validates again after push
# Merge when approved
```

---

## What Happens After You Push

### If Your PR is to `develop`

```
You push code
    ↓
GitHub Actions CI (lint, types, tests)
    ↓
✅ All pass? Ready for code review
❌ Any fail? Fix and push again
    ↓
Code review approved?
    ↓
✅ Merge to develop
    ↓
Auto-deploy to staging
    ↓
QA validates for 24 hours
```

### If Merging into `develop` (Auto)

```
✅ CI passed
✅ Code reviewed
✅ Merged to develop
    ↓
Auto-trigger: CI again
    ↓
Auto-trigger: Deploy to staging
    ↓
Health check: Passes
    ↓
Slack: #dev-alerts notified
    ↓
QA: Starts 24-hour validation
```

### After 24-hour Staging Validation

```
✅ QA validation complete
    ↓
Create version tag (DevOps job)
    ↓
Tag triggers: CI
    ↓
Tag triggers: Production deploy workflow
    ↓
Manual approval: Required
    ↓
Approve in GitHub → Deploy to production
    ↓
Health checks pass
    ↓
Slack: #prod-alerts notified
    ↓
🎉 Live!
```

---

## CI Check Failures - How to Fix

### Linting Error

```bash
# See the error
pnpm lint

# Auto-fix most
pnpm lint:fix

# Commit & push
git add .
git commit -m "fix: resolve linting issues"
git push
```

### Type Error

```bash
# See the error
pnpm type-check

# Read error message
# Edit TypeScript file to fix
# No auto-fix, requires manual work

git add .
git commit -m "fix: resolve type errors"
git push
```

### Formatting Error

```bash
# Auto-fix
pnpm format

git add .
git commit -m "refactor: format code"
git push
```

### Test Failure

```bash
# Run test
npm test

# See which test failed
# Edit implementation or test

npm test  # Verify fix

git add .
git commit -m "fix: resolve test failure"
git push
```

---

## Common Commands

```bash
# Install deps
pnpm install

# Start dev server
pnpm dev                    # http://localhost:3000

# Code quality
pnpm lint                   # Show lint errors
pnpm lint:fix               # Auto-fix lint errors
pnpm format                 # Auto-format code
pnpm type-check             # Check TypeScript
pnpm check-all              # All three above

# Tests
npm test                    # Run tests
npm test -- --watch        # Watch mode (re-run on change)

# Build
pnpm build                  # Production build
pnpm start                  # Run production build locally

# Git
git checkout -b feature/name              # Create branch
git add .                                  # Stage changes
git commit -m "type: description"         # Commit
git push origin feature/name               # Push
git pull origin develop                   # Get latest develop
git rebase origin/develop                 # Rebase on latest
```

---

## Before You Push - Checklist

- [ ] `pnpm check-all` passes
- [ ] `npm test` passes
- [ ] Code is formatted (no trailing spaces)
- [ ] No `console.log()` or debug code left
- [ ] No secrets in code
- [ ] Commit messages are clear
- [ ] Related to a GitHub issue (mention it)

---

## Branch Naming Convention

```
feature/feature-name          # New features
bugfix/bug-description        # Bug fixes
chore/task-description        # Refactoring, deps, etc.
hotfix/critical-issue         # Urgent production fixes (rare)
```

Example:

```bash
git checkout -b feature/user-authentication
git checkout -b bugfix/login-timeout-issue
git checkout -b chore/update-dependencies
```

---

## PR Title & Description

**Title**: Clear, concise (< 60 chars)

```
✅ "Add user authentication"
✅ "Fix login timeout error"
❌ "stuff"
❌ "wip"
```

**Description**:

```
## What
Brief description of what you changed.

## Why
Why this change was needed.

## How
How you implemented the solution.

## Testing
How you tested the changes.

## Screenshots (if UI)
Before/after if visual changes.

## Related Issues
Closes #123
```

---

## Code Review Tips

**When requesting review**:

- Tag 2 people: @person1 @person2
- Link any related issues: "Closes #123"
- Explain any non-obvious decisions

**When reviewing code**:

- ✅ Approve if it's good
- 🔄 Request changes if issues
- 💬 Comment on specific lines

**Responding to feedback**:

- Answer each comment (threaded reply)
- Push fixes to same branch
- CI re-runs automatically
- Request re-review when done

---

## Deployment Roles

**Frontend Developer**: You are here ↓

- Push code to feature branch
- Create PRs to develop
- Respond to code review
- Watch staging deployment (24h validation)

**QA**: After your merge

- Validates in staging for 24 hours
- Tests the feature thoroughly
- Signs off for production

**DevOps**: After QA signs off

- Creates version tag
- Approves production deployment
- Monitors health checks
- Can rollback if issues

---

## During Code Review

**If reviewer requests changes**:

1. Read the comment carefully
2. Make the requested change
3. Push to same branch (new commit)
4. Reply with a comment explaining the fix
5. Request re-review

**If reviewer approves**:

1. Ready to merge!
2. Click "Merge pull request"
3. Wait for auto-deployment to staging
4. Check Slack for deployment confirmation

---

## Quick Links

- **GitHub**: [Repository](https://github.com/[owner]/[repo])
- **Actions**: [Workflows](https://github.com/[owner]/[repo]/actions)
- **Deployments**: [Environments](https://github.com/[owner]/[repo]/deployments)
- **Staging**: <https://staging.abaco-loans-analytics.com>
- **Production**: <https://abaco-loans-analytics.com>
- **Slack**: #dev-alerts, #prod-alerts, #dev-help

---

## Getting Help

**CI check failing?**
→ See "CI Check Failures - How to Fix" above

**Question about code?**
→ Post in #dev-help with context

**Need to understand a feature?**
→ Ask your code reviewer

**Deployment issue?**
→ Post in #dev-alerts with workflow link

**Production emergency?**
→ Post in #incidents with severity level

---

## Troubleshooting

### "pnpm: command not found"

```bash
npm install -g pnpm
```

### "node_modules corruption"

```bash
rm -rf node_modules pnpm-lock.yaml
pnpm install
```

### "Merge conflict"

```bash
git pull origin develop        # Get latest
git rebase origin/develop      # Rebase your changes
# Resolve conflicts in editor
git add .
git rebase --continue
git push -f origin feature/name
```

### "Accidentally committed to main"

```bash
git reset HEAD~1              # Undo commit, keep changes
git checkout -b feature/name  # Create feature branch
git push origin feature/name  # Push feature branch
```

### "Forgot to commit something"

```bash
# Edit files...
git add .
git commit --amend            # Amend to last commit
git push -f origin feature/name
```

---

## Don't

❌ Push to main or develop directly (create PR)
❌ Merge your own PR
❌ Commit secrets or keys
❌ Force push after code review
❌ Ignore CI failures
❌ Disable security checks
❌ Deploy manually (let CI do it)

---

## Reference Docs

- **Deployment Config**: `.github/DEPLOYMENT_CONFIG.md`
- **Team Runbooks**: `.github/TEAM_RUNBOOKS.md`
- **Slack Coordination**: `.github/DEPLOYMENT_COORDINATION.md`
- **Engineering Standards**: `ENGINEERING_STANDARDS.md`
- **Operations Guide**: `OPERATIONS.md`
