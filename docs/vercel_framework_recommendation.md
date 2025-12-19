# Vercel Framework Preset Recommendation

## Project Profile Assumptions

- Project type: flexible (public marketing, admin dashboards, SaaS, fintech analytics)
- Stack: React + TypeScript + Tailwind CSS with Node.js backend
- Goals: SEO, fast initial load, strong developer velocity, dynamic + static data
- Team expertise: advanced with Next.js and SSR

## Recommendation

Use **Next.js (App Router, Next.js 14+)** as the Vercel Framework Preset.

### Rationale

1. **Performance and UX**
   - Server Components and React Suspense enable streamed UI for dashboards and KPIs with lower TTFB and faster FCP/LCP than SPA-only stacks.
   - Hybrid SSG/ISR/SSR for marketing pages yields SEO-ready HTML and cache-friendly responses.
   - Built-in image optimization and edge caching reduce payload and latency globally.
2. **Data + Compliance**
   - API Routes, Edge Functions, and Route Handlers support secure data access patterns (token-based, signed URLs) close to users.
   - Incremental Static Regeneration supports audit-friendly versioning of marketing content while dashboards can remain dynamic.
3. **Ops and Observability**
   - Vercel Analytics and Speed Insights deliver KPI dashboards for performance, with middleware for security headers and routing.
   - Minimal configuration drift: Vercel auto-detects Next.js; deploy previews integrate with GitHub PRs for traceability.
4. **Developer Efficiency**
   - First-class TypeScript, SWC bundling, and file-based routing reduce boilerplate versus custom Vite/SPA setups.

## Comparison: Next.js vs. Vite/SPA (React)

| Criterion              | Next.js (App Router)                                         | Vite/SPA (React)                                                    |
| ---------------------- | ------------------------------------------------------------ | ------------------------------------------------------------------- |
| Initial Load (FCP/LCP) | Faster via SSR/SSG/ISR + code splitting; edge caching        | Slower initial HTML (CSR); larger first bundle                      |
| SEO                    | Native SSR/SSG; metadata API for structured SEO              | CSR requires extra prerendering for SEO; less reliable crawlability |
| Vercel Optimizations   | Built-in Image Optimization, Edge Functions, Middleware, ISR | Manual setup for images/caching; limited edge primitives            |
| Dynamic Data           | Route Handlers + Server Components; streaming responses      | Client-only fetch; higher latency and heavier bundles               |
| Complexity             | Moderate (SSR/RSC concepts) but opinionated                  | Lower entry barrier; more manual perf/security wiring               |
| Maintainability        | Convention-driven; preview deployments per PR                | More custom glue; harder consistency across teams                   |

## Deployment Strategy (Vercel)

- **Framework Preset:** Next.js (auto-detected). No override needed.
- **Commands**
  - Install: `npm install`
  - Build: `npm run build`
  - Output directory: `.next`
- **Environment**
  - Configure secrets in Vercel (e.g., `DATABASE_URL`, `NEXT_PUBLIC_API_URL`, storage keys).
  - Use regions close to data gravity; prefer Edge for auth and routing.
- **Security + Compliance**
  - Enforce security headers (HSTS, CSP, Referrer-Policy, Permissions-Policy) via middleware or `next.config.js` headers.
  - Use signed URLs for blob/analytics exports and rotate keys via Vercel secrets.
- **Observability KPIs**
  - Track FCP, LCP, CLS, TTFB via Vercel Analytics/Speed Insights.
  - Add business KPIs (export success rate, latency, error budgets) to dashboards surfaced in PR checks.
- **GitHub Workflow**
  - Use preview deployments per PR; require lint, type-check, and unit tests in CI.
  - Gate production deploys on passing checks and manual approval for compliance-sensitive changes.

## Commands (copy/paste)

```bash
# Build and verify locally
npm install
npm run lint
npm run build

# Deploy with Vercel CLI (after linking)
vercel
vercel --prod
```
