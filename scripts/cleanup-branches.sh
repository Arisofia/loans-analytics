#!/bin/bash
# cleanup-branches.sh

set -e

echo "🧹 Limpiando branches locales merged..."

git fetch --all --prune

git branch --merged main | grep -v "main" | xargs -r git branch -d

echo "📋 Branches NO merged (revisar manualmente):"
git branch --no-merged main

git remote prune origin || true
git remote prune arisofia || true
git remote prune upstream || true

echo "✅ Limpieza completada!"
