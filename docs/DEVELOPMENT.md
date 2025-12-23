# Development Guide

## Setup

1. **Clone & Install**

   ```bash
   git clone <repo>
   cd nextjs-with-supabase
   npm ci
   ```

2. **Configure Environment**

   ```bash
   cp .env.example .env.local
   ```

   - Get credentials from [Supabase Dashboard](https://supabase.com/dashboard)
   - Add to `.env.local`

3. **Start Development**
   ```bash
   npm run dev
   ```

## Code Style

### TypeScript

- Use strict mode (enabled in tsconfig.json)
- Avoid `any` - use `unknown` or proper types
- Define return types for public functions

### React Components

- Prefer Server Components
- Use `"use client"` only when needed
- Keep components focused and reusable

### File Organization

```
components/
  ├── ui/              # Reusable UI components
  ├── forms/           # Form components
  └── layout/          # Layout components

lib/
  ├── utils.ts         # Utility functions
  ├── database.types.ts # Database types
  └── constants.ts     # Constants
```

## Testing

```bash
# Run tests
npm run test

# Watch mode
npm run test -- --watch

# Coverage
npm run test:coverage
```

## Deployment Checklist

- [ ] Run `npm run lint`
- [ ] Run `npm run type-check`
- [ ] Run `npm run test`
- [ ] Build: `npm run build`
- [ ] Test build: `npm run start`

## Troubleshooting

### Port 3000 in use

```bash
PORT=3001 npm run dev
```

### Supabase connection fails

- Check `NEXT_PUBLIC_SUPABASE_URL`
- Check `NEXT_PUBLIC_SUPABASE_ANON_KEY`
- Verify Supabase project is active

### Type errors

```bash
npm run type-check
```

## Resources

- [Next.js Docs](https://nextjs.org/docs)
- [Supabase Docs](https://supabase.com/docs)
- [Tailwind CSS](https://tailwindcss.com)
- [TypeScript](https://www.typescriptlang.org)
