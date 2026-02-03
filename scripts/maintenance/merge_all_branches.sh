#!/bin/bash
# This script merges all branches that have already been merged into main, then deletes them (except main/master/dev/etc.).
# Usage: Run from the root of your git repository.
set -e
echo "Fetching latest branches..."
git fetch --all --prune
echo "Switching to main branch..."
git checkout main
echo "Pulling latest changes for main..."
git pull
echo "Finding merged branches..."
merged_branches=$(git branch --merged main | grep -vE '(^\*|main|master|dev|develop|release|staging)')
if [ -z "$merged_branches" ]; then
  echo "No merged branches to process."
  exit 0
fi
echo "Deleting merged branches:"
echo "$merged_branches"
for branch in $merged_branches; do
  echo "Deleting branch: $branch"
  git branch -d "$branch"
done
echo "All merged branches (except main/master/dev/etc.) have been deleted."
