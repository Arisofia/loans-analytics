# Cleanup and Preparation for the New Implementation

This guide documents the repository cleanup and preparation workflow for the new
pipeline (Web Form Azure → n8n Webhook → Supabase → Analytics). Run commands from
the repository root after creating a working branch.

## 1) Backup and Baseline Review

```bash
git checkout -b cleanup-new-impl

git archive -o backup.zip HEAD

tree -L 3 > structure_before.txt

rg -n "looker" \
  --glob "*.py" --glob "*.yml" --glob "*.yaml" --glob "*.md" \
  --glob "!.git/**" --glob "!.venv/**" --glob "!node_modules/**" \
  . > integrations_remaining.txt
```

## 2) Comprehensive Cleanup Script

Run the repo cleanup script in dry-run mode, review the log, and then apply.

```bash
chmod +x complete-cleanup.sh
./complete-cleanup.sh --dry-run
./complete-cleanup.sh
```

## 3) Config and Environment Unification

```bash
# Unify env files into .env.example (manual review recommended)
# cat .env.staging .env.production .env.local > .env

# Optional: merge environment YAMLs if needed
# pip install pyaml
# yaml-merge config/environments/*.yml > config/unified_env.yml
```

## 4) Prepare for n8n + Webhook Flow

```bash
# Start services
# docker-compose up -d --build

# Verify n8n
# curl -fsS http://localhost:5678
```

## 5) Final Verification

```bash
rg -n "looker" . > post_cleanup.txt
```

## 6) Commit and Push

```bash
git add .
git commit -m "cleanup: prepare repo for new implementation"

git push origin cleanup-new-impl
```
