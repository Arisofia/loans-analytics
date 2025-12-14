# CLAUDE.md - Developer Reference Guide

**Last Updated**: 2025-12-14  
**Project**: Abaco Loans Analytics (Next.js Web App)

Quick reference for developers on deployment, testing, and troubleshooting.

---

## Quick Start Commands

### Development

```bash
npm install --legacy-peer-deps
npm run dev              # Start dev server (localhost:3000)
npm run build            # Production build
npm run lint             # Check code style
npm run type-check       # TypeScript validation
```

### Testing & Validation

```bash
npm run build            # Full production build
npm run lint             # ESLint
npm run type-check       # TypeScript errors
```

### Environment Setup (Local)

```bash
cp .env.example .env.local    # Create local env file
# Edit .env.local with:
NEXT_PUBLIC_SUPABASE_URL=your-url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-key
npm run dev
```

---

## GitHub Secrets Configuration

**Location**: https://github.com/your-org/abaco-loans-analytics/settings/secrets/actions

### Required Secrets

| Secret                                  | Source                                      | Purpose            |
| --------------------------------------- | ------------------------------------------- | ------------------ |
| `VERCEL_TOKEN`                          | https://vercel.com/account/tokens           | Deploy to Vercel   |
| `VERCEL_ORG_ID`                         | Vercel dashboard > Settings > General       | Organization ID    |
| `VERCEL_PROJECT_ID`                     | Vercel dashboard > Project Settings         | Project ID         |
| `NEXT_PUBLIC_SUPABASE_URL`              | Supabase dashboard > Project Settings       | Database URL       |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY`         | Supabase dashboard > Project Settings > API | Client key         |
| `NEXT_PUBLIC_SUPABASE_URL_STAGING`      | Staging Supabase project                    | Staging DB URL     |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY_STAGING` | Staging Supabase project                    | Staging client key |

### Optional Secrets

| Secret                   | Source            | Purpose                   |
| ------------------------ | ----------------- | ------------------------- |
| `NEXT_PUBLIC_SENTRY_DSN` | https://sentry.io | Error tracking (optional) |

### How to Add Secrets

1. Go to GitHub repo > Settings > Secrets and variables > Actions
2. Click "New repository secret"
3. Add each secret from table above
4. Secrets are encrypted and only available in CI/CD

---

## CI/CD Workflow Explanation

### Pipeline Overview

```
Push to GitHub
    ↓
[Lint] [Type-Check] (parallel)
    ↓
[Build] (depends on lint & type-check)
    ↓
Branch check:
  ├─ main → [Deploy to Production]
  └─ staging → [Deploy to Staging]
```

### File: `.github/workflows/ci-main.yml`

**Triggers**:

- Push to `main` → Production deployment
- Push to `staging` → Staging deployment
- Pull request to `main` or `staging` → Lint, type-check, build only (no deploy)

**Jobs**:

1. **Lint** - ESLint checks (npm run lint)
2. **Type-Check** - TypeScript validation (npm run type-check)
3. **Build** - Production build (npm run build)
4. **Deploy Production** - Vercel deployment (main branch only)
5. **Deploy Staging** - Vercel staging (staging branch only)

### How Deployments Work

1. Push code to GitHub
2. GitHub Actions runs lint → type-check → build
3. If main: Deploy to production Vercel project
4. If staging: Deploy to staging Vercel project
5. Check deployment status: https://vercel.com/dashboard

---

## Staging Workflow

### Deploy to Staging

```bash
git checkout -b staging
# Make changes, commit
git push -u origin staging
# CI/CD automatically deploys to staging
```

### Deploy Staging to Production

```bash
# Option 1: Pull staging into main
git checkout main
git pull origin main
git merge staging
git push origin main

# Option 2: Cherry-pick commits
git checkout main
git cherry-pick staging
git push origin main
```

### View Staging Environment

- **URL**: https://abaco-loans-analytics-staging.vercel.app
- **Environment Variables**: Uses `*_STAGING` secrets from GitHub

---

## Monitoring & Error Tracking

### Sentry (Error Tracking)

**Configuration**: `src/sentry.client.config.ts`

**Access Dashboard**: https://sentry.io

#### How It Works

- Automatically catches JavaScript errors in browser
- Sends to Sentry dashboard
- Environment-aware:
  - Production: 10% of errors (sample)
  - Staging: 100% of errors (all)

#### View Errors

1. Go to https://sentry.io
2. Select project: "abaco-loans-analytics"
3. Check Issues tab for error logs

#### Disable Sentry (Optional)

If `NEXT_PUBLIC_SENTRY_DSN` is not set, Sentry is disabled.

---

## Deployment Procedures

### Production Deployment

#### Automatic (Recommended)

```bash
git checkout main
# Make changes
git commit -m "feat: your change"
git push origin main
# CI/CD automatically builds and deploys
```

#### Check Deployment Status

```bash
# GitHub: https://github.com/your-org/abaco-loans-analytics/actions
# Vercel: https://vercel.com/dashboard/abaco-loans-analytics
```

#### Verify Production

1. Check build status on GitHub Actions
2. Verify at: https://abaco-loans-analytics.vercel.app
3. Check Sentry for errors: https://sentry.io

### Staging Deployment

```bash
git push origin staging
# CI/CD builds and deploys to staging
# View at: https://abaco-loans-analytics-staging.vercel.app
```

---

## Rollback Procedures

### Rollback Recent Deployment

#### Option 1: Revert Commit (Recommended)

```bash
git log --oneline          # Find commit hash
git revert <commit-hash>
git push origin main
# CI/CD redeploys with reverted changes
```

#### Option 2: Deploy Previous Version

```bash
git checkout main
git reset --hard <previous-commit-hash>
git push --force origin main
# WARNING: Force push can cause issues; use revert instead
```

#### Option 3: Rollback on Vercel

1. Go to https://vercel.com/dashboard
2. Select project: abaco-loans-analytics
3. Go to Deployments tab
4. Find previous working deployment
5. Click "..." → Promote to Production

### Verify Rollback

1. Check deployment on GitHub Actions
2. Verify at production URL
3. Monitor Sentry for continued errors

---

## Performance Optimization

### Build Optimization

```bash
npm run build      # Check build output
# Output shows:
# - Route count (13 static, 1 dynamic, 1 API)
# - Build size (~2.3 MB)
# - Optimization tips
```

### Runtime Optimization

- **Static Routes**: Pre-rendered at build time
- **Dynamic Routes**: Rendered on-demand
- **API Routes**: Optimized Node.js functions

### Image Optimization

- Next.js auto-optimizes images
- Use `next/image` component for automatic serving

### Bundle Analysis

```bash
npm run build -- --analyze    # (if configured)
```

---

## Security Best Practices

### Environment Variables

- **NEVER commit `.env.local`** (it's in .gitignore)
- **NEVER log secrets** in console
- Use GitHub Secrets for all sensitive data
- Rotate secrets regularly

### Data Validation

- CSV input validated with Zod (`src/lib/validation.ts`)
- All API responses type-checked
- CSV exports escape special characters
- 50MB file size limit enforced

### HTTPS

- Vercel enforces HTTPS automatically
- All traffic redirected to HTTPS

### Headers Security

- CSP (Content Security Policy) configured in `next.config.js`
- X-Frame-Options prevent clickjacking
- X-Content-Type-Options prevent MIME sniffing

### Dependency Security

```bash
npm audit                    # Check for vulnerabilities
npm audit --fix              # Auto-fix low-severity issues
npm audit --audit-level=moderate  # Show moderate+ issues
```

---

## Troubleshooting

### Build Fails Locally

```bash
rm -rf node_modules package-lock.json
npm install --legacy-peer-deps
npm run build
```

### Type Errors

```bash
npm run type-check           # Show all errors
npm run type-check -- --listFiles  # List checked files
```

### ESLint Failures

```bash
npm run lint                 # Show errors
npm run lint -- --fix        # Auto-fix where possible
```

### Deployment Won't Trigger

1. Check GitHub Actions: https://github.com/your-org/abaco-loans-analytics/actions
2. Verify GitHub Secrets are set
3. Check build logs for errors
4. Ensure `.github/workflows/ci-main.yml` exists and is valid YAML

### Sentry Errors Not Showing

1. Verify `NEXT_PUBLIC_SENTRY_DSN` is set
2. Check browser console for Sentry errors
3. Verify project on Sentry dashboard exists
4. Check sampling rate (10% production, 100% staging)

### Vercel Deployment Fails

1. Check Vercel logs: https://vercel.com/dashboard
2. Verify environment variables are set in Vercel project
3. Check `npm run build` runs locally without errors
4. Review deployment logs for specific error

---

## Testing Data Pipeline

### Validate CSV Input

```typescript
import { validateCsvInput } from '@/lib/validation'

const csvContent = fs.readFileSync('loans.csv', 'utf-8')
const result = validateCsvInput(csvContent)

if (result.success) {
  console.log('CSV valid, lines:', result.data.lines.length)
} else {
  console.error('CSV error:', result.error, result.details)
}
```

### Validate Analytics Output

```typescript
import { validateAnalytics } from '@/lib/validation'

const analyticsData = processLoanRows(loans)
const result = validateAnalytics(analyticsData)

if (result.success) {
  console.log('Analytics valid')
  console.log('Warnings:', result.warnings)
} else {
  console.error('Analytics error:', result.error, result.details)
}
```

---

## Project Structure

```
/apps/web
├── .github/workflows/
│   └── ci-main.yml              # CI/CD pipeline
├── src/
│   ├── app/                     # Next.js app router
│   ├── lib/
│   │   ├── validation.ts        # Zod schemas & validation
│   │   ├── analyticsProcessor.ts
│   │   ├── exportHelpers.ts
│   │   └── loanData.ts
│   ├── sentry.client.config.ts  # Sentry configuration
│   └── types/
│       └── analytics.ts         # TypeScript types
├── package.json
├── next.config.js
├── tsconfig.json
├── .env.example
├── README.md
└── CLAUDE.md (this file)
```

---

## Useful Links

| Resource           | URL                                                       |
| ------------------ | --------------------------------------------------------- |
| GitHub Repo        | https://github.com/your-org/abaco-loans-analytics         |
| Vercel Dashboard   | https://vercel.com/dashboard                              |
| GitHub Actions     | https://github.com/your-org/abaco-loans-analytics/actions |
| Sentry Dashboard   | https://sentry.io                                         |
| Supabase Dashboard | https://supabase.com/dashboard                            |
| Next.js Docs       | https://nextjs.org/docs                                   |

---

## Contact & Support

- **GitHub Issues**: Report bugs at repo issues page
- **Sentry**: Check error logs at sentry.io
- **Vercel Support**: https://vercel.com/support
- **Team**: Add team communication channel

---

**Last Verified**: 2025-12-14  
**Status**: ✅ Production Ready
