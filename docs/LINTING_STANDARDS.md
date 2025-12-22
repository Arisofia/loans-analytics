# Linting & Code Quality Standards

## Overview

This document defines the linting, type checking, and code quality standards for the Abaco Loans Analytics repository.

## TypeScript/JavaScript Standards (Web)

### ESLint Configuration

Located in `apps/web/eslint.config.mjs` and `apps/web/.eslintrc.json`.

**Enforced Rules:**
- `@typescript-eslint/no-unused-vars`: Unused variables must match pattern `^_` (e.g., `_error`)
- `@typescript-eslint/no-explicit-any`: Warn on `any` types (use proper types instead)
- `@typescript-eslint/no-non-null-assertion`: Warn on non-null assertions (suppress with comment when justified)
- `@typescript-eslint/no-floating-promises`: Error on unhandled promises
- `react-hooks/rules-of-hooks`: Error on hook rule violations
- `no-console`: Warn on `console.log` (allow only `console.warn` and `console.error`)

### Common Issues & Fixes

#### Unused Variables
**Problem:** `catch (error) { ... }` triggers error if `error` is unused
```typescript
// ❌ Bad
try { ... } catch (error) { alert('Error!'); }

// ✅ Good
try { ... } catch (_error) { alert('Error!'); }
```

#### Non-null Assertions
**Problem:** Required environment variables cause warnings
```typescript
// ❌ Bad
const url = process.env.API_URL!;

// ✅ Good
// eslint-disable-next-line @typescript-eslint/no-non-null-assertion
const url = process.env.API_URL!;
```

#### Any Types
**Problem:** `any` type defeats type checking
```typescript
// ❌ Bad
catch (err: any) {
  console.log(err.message);
}

// ✅ Good
catch (err) {
  const msg = err instanceof Error ? err.message : 'Unknown error';
  console.log(msg);
}
```

#### Console Methods
**Problem:** Logging to `console.log` is restricted
```typescript
// ❌ Bad
console.log('Downloading image...', error);

// ✅ Good
console.error('Error downloading image:', error);
```

### Running Lint Commands

```bash
# Check for errors
npm run lint --prefix apps/web

# Auto-fix fixable errors
npm run lint:fix --prefix apps/web

# Type check (TypeScript)
npm run type-check --prefix apps/web

# Format check (Prettier)
npm run format:check --prefix apps/web

# Run all checks
npm run check-all --prefix apps/web
```

## Vercel Configuration

Located in `vercel.json`.

### Valid Configuration

**Modern format (v3+):**
```json
{
  "framework": "nextjs",
  "buildCommand": "npm run build --prefix apps/web",
  "outputDirectory": "apps/web/.next"
}
```

### Deprecated Configuration

❌ **NEVER use v2 config:**
```json
{
  "version": 2,
  "builds": [...],
  "routes": [...]
}
```

<<<<<<< HEAD
This causes Vercel deployment failures due to an incompatible config version.
=======
This causes Vercel deployment failures with: `version should be <= 2`
>>>>>>> fix/ci-workflow-codecov

## GitHub Actions Workflows

### Valid Workflow Steps

❌ **NEVER put JavaScript code in shell steps:**
```yaml
- name: Update Figma Slides
  run: |
    const cron = require('node-cron');  # ❌ Invalid!
```

✅ **Use JavaScript actions or scripts:**
```yaml
- name: Update Figma Slides
  run: echo "Job placeholder - implement Figma API integration"
  
# OR use actions/github-script@v7
- name: Update Figma Data
  uses: actions/github-script@v7
  with:
    script: |
      const axios = require('axios');
      // JavaScript code here
```

## Pre-commit Hooks

To catch issues before they reach GitHub:

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run manually (all files)
pre-commit run --all-files

# Specific hook
pre-commit run eslint --all-files
```

### Configured Hooks

- `trim-trailing-whitespace`: Remove trailing spaces
- `end-of-file-fixer`: Ensure newline at EOF
- `check-yaml`: Validate YAML syntax
- `black`: Format Python code
- `isort`: Sort Python imports
- `eslint`: Lint TypeScript/JavaScript (disabled for non-merge files in CI)

## CI/CD Validation

### Lint & Type Check Pipeline
Triggered on: `push` (main/develop), `pull_request`, manual dispatch

**Jobs:**
1. `lint-and-type-check`: ESLint, TypeScript, Prettier, Next.js build
2. `vercel-config-validation`: Checks vercel.json schema
3. `github-workflow-validation`: Validates workflow files

### Failure Conditions
- Any ESLint errors → Build fails
- TypeScript errors → Build fails
- Prettier format violations → Build fails
- Vercel config invalid schema → Build fails
- Next.js build failure → Build fails

## Local Development Workflow

### Before Committing

```bash
# 1. Run all checks
npm run check-all --prefix apps/web

# 2. Auto-fix issues
npm run lint:fix --prefix apps/web

# 3. Commit
git add apps/web/
git commit -m "Feature: description"

# Pre-commit hooks run automatically
```

### If Pre-commit Fails

```bash
# Review the error
# Make corrections
# Stage and commit again (pre-commit reruns automatically)
```

### If CI Fails

1. Check the GitHub Actions log for the specific error
2. Reproduce locally: `npm run check-all --prefix apps/web`
3. Fix issues
4. Commit with message: `fix: address linting/type errors`
5. Push again

## Troubleshooting

### ESLint Issues

**"'error' is defined but never used"**
- Rename to `_error` or use it: `console.error(error)`

**"Forbidden non-null assertion"**
- Add `// eslint-disable-next-line` comment above the line
- Or refactor to proper type narrowing

**"Unexpected console statement"**
- Change `console.log` to `console.warn` or `console.error`
- Or use `// eslint-disable-next-line` if logging is intentional

### Build Issues

**"Invalid project directory provided"**
- Check ESLint config syntax
- Run `npm ci` to reinstall dependencies

**Vercel deployment fails with schema error**
- Verify `vercel.json` uses v3+ format (no `version` field or `version: 3`)
- Check required fields: `framework`, `buildCommand`, `outputDirectory`

## Standards Update Process

When updating eslint rules or vercel config:

1. Document the change in this file
2. Update `.eslintrc.json`, `eslint.config.mjs`, or `vercel.json`
3. Create CI validation (add to `.github/workflows/ci-lint-validation.yml`)
4. Communicate changes to team via PR description
5. Ensure all existing code complies before merging
