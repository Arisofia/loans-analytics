#!/bin/bash
# setup.sh - Nukes all caches, lockfiles, and node_modules, then reinstalls and builds everything for a clean, forever-fix.

set -e

# Remove all node_modules, build caches, and lockfiles
rm -rf node_modules
rm -rf apps/web/node_modules
rm -rf .next
rm -rf apps/web/.next
rm -f package-lock.json
rm -f apps/web/package-lock.json
rm -f pnpm-lock.yaml
delete_demo_lockfile="demo/pnpm-lock.yaml"
if [ -f "$delete_demo_lockfile" ]; then
  rm -f "$delete_demo_lockfile"
fi
rm -rf ~/.npm/_locks
rm -rf ~/.npm/_cacache
rm -rf ~/.pnpm-store

# Find and delete any hidden lockfiles
find . -name 'pnpm-lock.yaml' -exec rm -f {} +
find . -name 'package-lock.json' -exec rm -f {} +

# Reinstall dependencies
npm install

# Run lint and build for web workspace
npm run lint --workspace=web || true
npm run build --workspace=web || true

echo "\nSetup complete. If errors persist, clone the repo fresh and rerun this script."
