# Development & Automation Reference

## Quick Start Commands

### Linting & Type Checking (Web)

```bash
# Run all checks (lint, type-check, format)
npm run check-all --prefix apps/web

# Lint only (ESLint)
npm run lint --prefix apps/web

# Auto-fix linting issues
npm run lint:fix --prefix apps/web

# Type check (TypeScript compiler)
npm run type-check --prefix apps/web

# Format check (Prettier)
npm run format:check --prefix apps/web

# Auto-format code
npm run format --prefix apps/web
```

### Building & Testing

```bash
# Build Next.js app
npm run build --prefix apps/web

# Run dev server
npm run dev --prefix apps/web

# Start production server
npm start --prefix apps/web
```

### Pre-commit Hooks

```bash
# Install pre-commit hooks
pre-commit install

# Run all hooks manually
pre-commit run --all-files

# Run specific hook
pre-commit run eslint --all-files

# Skip hooks on commit (not recommended)
git commit --no-verify
```

## CI/CD Validation

### GitHub Actions Workflows

**Lint & Type Validation** (`.github/workflows/ci-lint-validation.yml`)
- Triggers: `push` (main/develop), `pull_request`, manual dispatch
- Jobs:
  - `lint-and-type-check`: ESLint, TypeScript, Prettier, Next.js build
  - `vercel-config-validation`: Validates vercel.json schema
  - `github-workflow-validation`: Checks for workflow issues

**Run locally to debug CI failures:**

```bash
# Simulate CI lint/type checks
npm run check-all --prefix apps/web

# Simulate Vercel config validation
node -e "
const fs = require('fs');
try {
  const config = JSON.parse(fs.readFileSync('vercel.json'));
  if (!config.framework) throw new Error('Missing framework field');
  if (!config.buildCommand) throw new Error('Missing buildCommand field');
  if (!config.outputDirectory) throw new Error('Missing outputDirectory field');
  if (config.version === 2) throw new Error('Deprecated version 2 - use v3 or omit');
  console.log('✅ vercel.json is valid');
} catch (e) {
  console.error('❌ Invalid vercel.json:', e.message);
  process.exit(1);
}
"
```

## Common Issues & Solutions

### ESLint Errors

#### Unused Variables
```bash
# Issue: 'error' is defined but never used
# Solution: Rename to _error pattern
sed -i.bak 's/catch (error)/catch (_error)/g' apps/web/src/**/*.tsx
```

#### Non-null Assertions
```bash
# Issue: Forbidden non-null assertion warnings
# Solution: Add eslint-disable-next-line comment or refactor

# In middleware.ts, supabaseClient.ts:
# eslint-disable-next-line @typescript-eslint/no-non-null-assertion
const url = process.env.NEXT_PUBLIC_SUPABASE_URL!;
```

#### Console Methods
```bash
# Issue: Unexpected console statement (only warn/error allowed)
# Solution: Use console.error or console.warn instead of console.log

sed -i.bak "s/console\.log('Error/console.error('Error/g" apps/web/src/**/*.tsx
```

#### Any Types
```bash
# Issue: Unexpected any type
# Solution: Use proper type narrowing

# Instead of:
catch (err: any) { ... }

# Use:
catch (err) {
  const msg = err instanceof Error ? err.message : 'Unknown error';
  console.error(msg);
}
```

### Vercel Deployment Failures

#### Schema Validation Error
```bash
# ❌ Problem: "version should be <= 2"
# This happens with deprecated v2 config

# ✅ Solution: Update vercel.json to modern format
cat > vercel.json << 'EOF'
{
  "framework": "nextjs",
  "buildCommand": "npm run build --prefix apps/web",
  "outputDirectory": "apps/web/.next"
}
EOF
```

### Build Failures

#### "Invalid project directory provided"
```bash
# Usually caused by ESLint config issues
# Solution:
npm ci --prefix apps/web  # Clean reinstall
npm run lint --prefix apps/web  # Check errors
npm run lint:fix --prefix apps/web  # Auto-fix
```

#### "Cannot format for target version Python 3.9"
```bash
# Black formatting issue in Python code
# Usually safe to ignore in CI, focus on TypeScript issues

# But if needed, update pyproject.toml:
[tool.black]
target-version = ['py311']
```

## Configuration Files Reference

| File | Purpose | Standards |
|------|---------|-----------|
| `apps/web/eslint.config.mjs` | ESLint rules | No `any` types, no unused vars, console.warn/error only |
| `apps/web/.eslintrc.json` | ESLint setup | Extends `next/core-web-vitals` |
| `vercel.json` | Vercel deployment | v3+ format, has framework/buildCommand/outputDirectory |
| `.github/workflows/ci-lint-validation.yml` | Lint validation | Runs ESLint, TypeScript, Prettier, vercel validation |
| `docs/LINTING_STANDARDS.md` | Documentation | Full guide to linting rules and troubleshooting |
| `CLAUDE.md` | This file | Quick reference for developers |

## Vibe Solutioning Checklist

✅ Robust linting (ESLint enforced, no unknown patterns)
✅ Type safety (TypeScript, no `any` types without reason)
✅ Vercel config validation (CI checks schema)
✅ Workflow validation (CI checks for JavaScript in shells)
✅ Pre-commit hooks (catch issues locally)
✅ Comprehensive documentation (LINTING_STANDARDS.md)
✅ CI/CD tests (test_ci_standards.py)
✅ Zero ambiguity (all rules documented)
✅ Automated enforcement (GitHub Actions pipeline)

## Next Steps

1. **Local development**: Run `npm run check-all --prefix apps/web` before committing
2. **Pre-commit hooks**: Run `pre-commit install` once per clone
3. **CI failures**: Check `.github/workflows/ci-lint-validation.yml` logs
4. **Questions**: Refer to `docs/LINTING_STANDARDS.md`
