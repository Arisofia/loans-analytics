#!/bin/bash
# Script: merge_all_branches.sh
# Description: Switch to main, pull latest, and merge all merged branches into main.
set -e

echo "Switching to main branch..."
git checkout main

echo "Pulling latest changes from origin/main..."
git pull

echo "Merging all merged branches into main..."
for branch in $(git branch --merged | grep -v '\*\|main'); do
  echo "Merging $branch into main..."
  git merge $branch || {
    echo "Merge conflict or error with $branch. Resolve manually and re-run if needed.";
    exit 1;
  }
done

echo "All merged branches have been merged into main."
