# Vercel Framework Recommendation for New Deployments

## Summary Recommendation
- **Framework Preset:** Next.js (App Router, Next.js 14+)
- **Why:** Native Vercel optimizations (ISR, Image Optimization, Edge Functions, Middleware), strong SEO/SSR, streaming Server Components for mixed static/dynamic data, and first-class TypeScript support. Ideal for fintech analytics that demands compliance, observability, and rapid iteration.
- **Team Fit:** Assumes proficiency with Next.js/SSR; supports mixed data strategies and enterprise governance (security headers, env management, auditable CI).

## Comparative Analysis (Next.js vs Vite/SPA)
| Dimension | Next.js (App Router) | Vite/SPA (React) |
| --- | --- | --- |
| Initial Load (FCP/LCP) | Faster: SSR/SSG + code-splitting; PPR/ISR reduce TTFB and payload | Slower: full client bundle + hydration gate; relies on aggressive caching |
| SEO Coverage | Strong: HTML pre-rendered; Metadata API; dynamic routes with ISR | Weak: CSR-first; needs pre-render hacks; bots may miss dynamic content |
| Vercel Optimization | Native: Image Optimization, Edge Functions/Middleware, ISR cache, Analytics/Speed Insights | Limited: requires manual CDN/image setup; fewer edge primitives |
| Real-time/Data | Server Components stream data; Route Handlers/APIs colocated; Edge auth | Client-only fetching; backend hosted elsewhere; higher latency |
| Complexity | Moderate: SSR/RSC patterns, caching strategies, middleware | Low: familiar SPA patterns only |
| Scalability | Auto-edge scaling; DB pooling with Route Handlers; multi-region cache | Frontend only; must build/operate separate backend |
| Compliance/Observability | Built-in headers, Middleware for auth/A/B testing; Vercel Analytics + Speed Insights; supports logging and tracing | Mostly client-centric; requires extra services for telemetry/compliance |

## Deployment Strategy on Vercel (Next.js Preset)
1. **Project Settings → General**
   - Root Directory: `apps/web` (for monorepo)
   - Framework Preset: **Next.js**
2. **Build & Install Commands**
   - Install: `npm install` (workspace-aware) or `npm ci`
   - Build: `npm run build` (executes from `apps/web` when Root Directory is set)
   - Dev: `npm run dev`
   - Output Directory: `.next`
3. **Environment & Secrets** (Vercel Dashboard → Environment Variables)
   - `NODE_ENV=production`
   - `DATABASE_URL=<postgres-url>`
   - `NEXT_PUBLIC_API_URL=<public-api>`
   - `NEXT_RUNTIME=experimental-edge` (for edge-first routes, optional)
4. **Recommended next.config.ts settings**
   - Enable `reactStrictMode`, `swcMinify`, and AVIF/WebP images
   - Configure `experimental.serverActions` and `experimental.ppr` for streaming/partial prerendering where safe
   - Harden headers (HSTS, XSS, Referrer-Policy), and prefer Edge Middleware for auth/geo-based rules
5. **CI/CD & Quality Gates**
   - Pre-deploy checks: `npm run lint`, `npm run test` (if defined), `npm run build`
   - Observability: add `@vercel/analytics` and `@vercel/speed-insights` in `app/layout.tsx`
   - Auditing: lockfile in repo; enable branch protection + required checks; use Vercel deployments with GitHub Checks for traceability
6. **Performance & KPI Tracking**
   - Target <2s FCP and <2.5s LCP for landing pages; monitor via Vercel Speed Insights
   - Track cache HIT ratio for ISR/Edge cache; alert on miss spikes
   - Dashboard: surface build duration, error rate, p95 latency, and bundle size per deployment

## Command Snippets (copy/paste)
- **Local build (monorepo aware):**
  ```bash
  cd apps/web && npm run build
  ```
- **Preview deploy via Vercel CLI:**
  ```bash
  vercel --cwd apps/web
  ```
- **Production deploy:**
  ```bash
  vercel --prod --cwd apps/web
  ```
- **Pull envs locally:**
  ```bash
  vercel env pull apps/web/.env.local
  ```

## Why Not Vite/SPA for This Use Case
- Lacks native SSR/ISR, so SEO and initial render speed depend on client hydration.
- Requires separate backend + CDN configuration for images/edge caching, increasing operational surface area.
- Observability, auth, and compliance controls must be stitched together manually rather than leveraging Vercel middleware/Edge Functions.

## Roles & Responsibilities (RACI-style)
- **Product/Analytics:** define KPIs (FCP, LCP, conversion, DAU), instrumentation events, and dashboards.
- **Engineering:** implement Next.js App Router, caching strategy (ISR/PPR), middleware for auth/compliance, and CI gates.
- **DevOps/SRE:** manage Vercel project settings, environment secrets, incident playbooks, and release governance.
- **Security/Compliance:** review headers, data residency, logging/PII handling, and audit trails.

## Continuous Improvement
- Run quarterly performance audits (Lighthouse/Speed Insights); regressions >10% trigger remediation.
- Rotate secrets regularly and enforce least-privilege for Vercel/GitHub tokens.
- Keep Next.js and Vercel CLI updated to inherit platform optimizations and security patches.
