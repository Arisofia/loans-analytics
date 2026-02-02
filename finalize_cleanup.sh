#!/bin/bash
# Complete the cleanup consolidation and commit
set -e

cd "$(git rev-parse --show-toplevel)" || exit 1

echo "🎯 Completing cleanup consolidation..."
echo ""

# Step 1: Remove the helper script
echo "1️⃣  Removing temporary consolidation script..."
rm -f consolidate_cleanup_scripts.sh && echo "   ✓ Deleted: consolidate_cleanup_scripts.sh"

# Step 2: Make clean.sh executable
echo ""
echo "2️⃣  Making clean.sh executable..."
chmod +x clean.sh && echo "   ✓ clean.sh is now executable"

# Step 3: Execute the cleanup
echo ""
echo "3️⃣  Executing unified cleanup..."
echo ""
./clean.sh

# Step 4: Stage all changes
echo ""
echo "4️⃣  Staging all changes..."
git add -A && echo "   ✓ All changes staged"

# Step 5: Show what will be committed
echo ""
echo "📋 Changes to be committed:"
git status --short

echo ""
echo "5️⃣  Ready to commit!"
echo ""
echo "Run this command to commit:"
echo ""
echo 'git commit -m "chore: unify all cleanup scripts into single clean.sh

- Consolidate 11 cleanup scripts into 1 unified clean.sh
- Remove 17 status report files from root directory
- Remove 4 Gradle build files (not applicable to Python project)
- Remove 5 orphaned config files
- Remove 6 duplicate documentation files
- Reorganize 3 orphaned directories (fi-analytics, projects, models)
- Clean all Python/Node caches
- Remove empty directories

Total: 50+ files consolidated/removed
Single entry point: ./clean.sh (with --dry-run, --caches-only, --workflows-only options)

Resolves technical debt priority 2: Script sprawl consolidation"'

echo ""
echo "Or simply run: git commit"
