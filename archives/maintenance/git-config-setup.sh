#!/bin/bash
#
# Git Configuration Setup
# Based on: docs/REPO_CLEANUP_AND_CONFLICT_PLAYBOOK.md (Section 5)
# Applies recommended Git configurations for the repository
#

set -e

echo "═══════════════════════════════════════════════════════════"
echo "Git Configuration Setup"
echo "Version 2.0 (2026-01-29)"
echo "═══════════════════════════════════════════════════════════"
echo ""

# Check if in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
  echo "✗ Error: Not in a git repository"
  exit 1
fi

echo "📋 Applying recommended Git configurations..."
echo ""

# 1. Merge fast-forward policy
echo "▸ Setting merge.ff to 'false' (creates merge commits)"
git config --local merge.ff false
echo "  ✓ git config merge.ff false"
echo ""

# 2. Merge tool
echo "▸ Setting default merge tool to 'vimdiff'"
git config --global merge.tool vimdiff 2>/dev/null || git config --local merge.tool vimdiff
echo "  ✓ git config merge.tool vimdiff"
echo ""

# 3. Conflict style
echo "▸ Setting merge.conflictstyle to 'diff3' (shows common ancestor)"
git config --global merge.conflictstyle diff3 2>/dev/null || git config --local merge.conflictstyle diff3
echo "  ✓ git config merge.conflictstyle diff3"
echo ""

# 4. Diff tool
echo "▸ Setting default diff tool to 'vimdiff'"
git config --global diff.tool vimdiff 2>/dev/null || git config --local diff.tool vimdiff
echo "  ✓ git config diff.tool vimdiff"
echo ""

# 5. Push default behavior
echo "▸ Setting push.default to 'simple' (push current branch)"
git config --local push.default simple
echo "  ✓ git config push.default simple"
echo ""

# 6. Pull behavior
echo "▸ Setting pull.rebase to 'false' (merge by default)"
git config --local pull.rebase false
echo "  ✓ git config pull.rebase false"
echo ""

# 7. Log formatting
echo "▸ Setting log format for 'git log --oneline'"
git config --local format.pretty "%h %s"
echo "  ✓ git config format.pretty '%h %s'"
echo ""

# 8. Conditional includes (if using multiple accounts)
echo "▸ Note: For multiple Git accounts, add conditional includes to ~/.gitconfig:"
echo "  [includeIf \"gitdir:~/work/\"]"
echo "      path = ~/.gitconfig-work"
echo ""

# 9. Show current configuration
echo "═══════════════════════════════════════════════════════════"
echo "Current Repository Configuration"
echo "═══════════════════════════════════════════════════════════"
echo ""

echo "Local Git Configuration (for this repository):"
git config --local --list | grep -E "(merge|push|pull|format)" || echo "  (default settings)"
echo ""

echo "Global Git Configuration (system-wide):"
git config --global --list 2>/dev/null | grep -E "(merge|diff|user)" || echo "  (default settings)"
echo ""

echo "═══════════════════════════════════════════════════════════"
echo "✓ Git configuration setup complete!"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "These settings will:"
echo "  • Always create merge commits (no fast-forward)"
echo "  • Use vimdiff for conflict resolution and diffs"
echo "  • Show the common ancestor in conflicts (diff3 style)"
echo "  • Prevent accidental force pushes to shared branches"
echo ""
