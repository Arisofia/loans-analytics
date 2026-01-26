#!/bin/bash
set -e

echo "Starting massive merge and purge..."
git checkout main

# Get all remote branches (excluding main and HEAD)
branches=$(git branch -r | grep "origin/" | grep -v "origin/main" | grep -v "origin/HEAD" | sed 's/origin\///')

for branch in $branches; do
  echo "--- Processing branch: $branch ---"
  
  # Try to merge with -X ours to prioritize the cleanup state
  if git merge "origin/$branch" -m "Merge branch $branch into main (prioritizing clean state)" -X ours; then
    echo "Successfully merged $branch"
  else
    echo "Merge failed for $branch, skipping..."
    git merge --abort || true
  fi
done

echo "All merges completed. Pushing main..."
git push origin main

echo "Deleting remote branches..."
for branch in $branches; do
  echo "Deleting remote branch: $branch"
  git push origin --delete "$branch" || echo "Failed to delete remote branch $branch"
done

echo "Purge complete!"
