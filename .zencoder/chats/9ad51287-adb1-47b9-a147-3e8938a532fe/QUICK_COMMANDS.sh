#!/bin/bash
# Quick Commands to Complete the Merge Conflict Fix
# Run these commands in sequence

set -e  # Exit on error

echo "=================================================="
echo "MERGE CONFLICT RESOLUTION - FINAL STEPS"
echo "=================================================="
echo ""

# Step 1: Verify no conflicts remain
echo "Step 1/5: Verifying conflicts are resolved..."
if grep -r "<<<<<<< HEAD" --include="*.py" --include="*.sh" --include="*.yml" . 2>/dev/null | grep -v ".zencoder"; then
    echo "❌ ERROR: Conflict markers still found!"
    echo "Please resolve remaining conflicts before continuing."
    exit 1
else
    echo "✅ No conflict markers found"
fi
echo ""

# Step 2: Stage auto-resolved files
echo "Step 2/5: Staging auto-resolved files..."
git add .github/workflows/ci.yml
git add src/pipeline/transformation.py
echo "✅ Files staged"
git status --short
echo ""

# Step 3: Show what will be committed
echo "Step 3/5: Verifying staged changes..."
read -p "Review the changes above. Continue? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Aborted by user"
    exit 1
fi
echo ""

# Step 4: Continue rebase
echo "Step 4/5: Continuing rebase..."
echo "⚠️  NOTE: Git may open an editor for commit message."
echo "    Just save and close the editor to proceed."
echo ""
read -p "Ready to continue rebase? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Aborted by user"
    exit 1
fi

git rebase --continue
echo "✅ Rebase continued"
echo ""

# Step 5: Verify completion
echo "Step 5/5: Verifying rebase completion..."
if git status | grep -q "rebase in progress"; then
    echo "⚠️  Rebase still in progress. More conflicts may exist."
    echo "Run this script again after resolving."
    exit 1
else
    echo "✅ Rebase completed successfully!"
fi
echo ""

# Show current branch
echo "=================================================="
echo "REBASE COMPLETE!"
echo "=================================================="
echo ""
echo "Current branch: $(git branch --show-current)"
echo "Commits ahead of origin/main: $(git rev-list --count origin/main..HEAD)"
echo ""

# Suggest next steps
echo "Next Steps:"
echo "  1. Run quality checks:  make quality"
echo "  2. If tests pass:       git push origin $(git branch --show-current) --force-with-lease"
echo "  3. Create PR if needed"
echo ""
echo "To verify changes:"
echo "  git log --oneline -10"
echo "  git diff origin/main..HEAD --stat"
echo ""
