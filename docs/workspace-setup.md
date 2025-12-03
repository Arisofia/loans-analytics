# Workspace setup and build reference
This repository uses npm workspaces to coordinate the Next.js app in `apps/web` and any shared packages under `packages/`.
Follow the steps below to install dependencies, run local commands from the monorepo root, and troubleshoot registry access.
## Installing dependencies
1. From the repository root, install all workspace dependencies:
   ```bash
   npm install
   ```
2. The root `package.json` exposes helpers so you can run workspace scripts without `cd`-ing:
   ```bash
   npm run dev:web    # Start the Next.js dev server for apps/web
   npm run lint:web   # Lint the web workspace
   npm run build:web  # Build the web workspace
   ```
## Network and registry troubleshooting
If `npm install` fails with `403 Forbidden` errors, the request is being blocked before it reaches the npm registry.
Common causes and mitigations:
- **Proxy settings:** unset or override `http_proxy`/`https_proxy` environment variables if a corporate proxy is intercepting traffic.
- **Custom registries:** ensure `.npmrc` points to the public registry for all scopes:
  ```ini
  registry=https://registry.npmjs.org/
  @supabase:registry=https://registry.npmjs.org/
  strict-ssl=true
  ```
- **Connectivity tests:** verify outbound HTTPS connectivity with a simple curl check:
  ```bash
  curl -I https://registry.npmjs.org/react
  ```
  Successful output should return `200` or `304` instead of `403`.
Documenting these steps keeps workspace installs reproducible and makes network-related failures auditable.
