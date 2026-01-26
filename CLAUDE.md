# CLAUDE.md - Project Guidelines

## Build and Development

- **Dev**: `npm run dev` (within `apps/web`)
- **Build**: `npm run build` (within `apps/web`)
- **Type Check**: `npm run type-check`
- **Check All**: `npm run check-all` (Types + Lint + Format)

## Testing

- **Unit Tests**: `npm run test:unit` (Jest)
- **E2E Tests**: `npm run test:e2e` (Playwright)
- **CI E2E**: `npm run test:e2e:ci`
- **Seed Data**: `npm run e2e:seed`

## Code Style & Linting

- **Linting**: `npm run lint` (ESLint 9 with Flat Config)
- **Formatting**: `npm run format` (Prettier)
- **React**: Version 19 (using React Compiler)
- **Styling**: Tailwind CSS 4.0
- **Standards**: Use functional components, TypeScript for type safety, and Zod for schema validation.

## Documentation

- **Source of Truth**: `UNIFIED_DOCS.md` at the root.
- **Legacy Docs**: Most files in `docs/` have been consolidated or removed.

## Environment

- **Framework**: Next.js 15 (App Router)
- **Database/Auth**: Supabase (@supabase/ssr)
- **Deployment**: Azure Static Web Apps / Vercel
