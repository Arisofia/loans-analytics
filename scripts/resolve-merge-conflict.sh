#!/bin/bash

# Merge Conflict Resolution Script
# This script helps resolve git merge conflicts by:
# 1. Aborting the current merge
# 2. Cleaning up dangling git objects
# 3. Resetting to a clean state
# 4. Providing clear next steps

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Main script logic
main() {
    print_status "Starting merge conflict resolution process..."
    echo ""

    # Check if we're in a git repository
    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        print_error "Not a git repository. Exiting."
        exit 1
    fi

    # Check if there's an active merge
    if [ ! -f .git/MERGE_HEAD ]; then
        print_warning "No active merge detected. The repository appears to be in a clean state."
        echo ""
        print_status "Current git status:"
        git status
        exit 0
    fi

    echo ""
    print_status "Step 1: Aborting the current merge..."
    git merge --abort
    print_success "Merge aborted successfully"
    echo ""

    print_status "Step 2: Cleaning up dangling git objects..."
    # Remove unreachable objects
    git gc --aggressive --prune=now 2>/dev/null || git gc --prune=now
    print_success "Git garbage collection completed"
    echo ""

    print_status "Step 3: Resetting to a clean state..."
    # Reset any unstaged changes
    git reset --hard
    # Clean untracked files and directories
    git clean -fd
    print_success "Repository reset to a clean state"
    echo ""

    # Display current status
    print_status "Step 4: Current repository status"
    git status
    echo ""

    # Provide next steps
    print_success "Merge conflict resolution completed!"
    echo ""
    print_status "============================================"
    print_status "NEXT STEPS FOR THE USER:"
    print_status "============================================"
    echo ""
    echo "1. Review your current branch:"
    echo "   ${BLUE}git branch -v${NC}"
    echo ""
    echo "2. Check the commit history:"
    echo "   ${BLUE}git log --oneline -10${NC}"
    echo ""
    echo "3. Fetch the latest changes from remote:"
    echo "   ${BLUE}git fetch origin${NC}"
    echo ""
    echo "4. Review the branch you were trying to merge:"
    echo "   ${BLUE}git log --oneline origin/<branch-name> -10${NC}"
    echo ""
    echo "5. Manually resolve conflicts in your editor:"
    echo "   - Open conflicted files"
    echo "   - Remove conflict markers (<<<<<<, ======, >>>>>>)"
    echo "   - Keep the code you want to maintain"
    echo ""
    echo "6. Stage the resolved files:"
    echo "   ${BLUE}git add <resolved-file>${NC}"
    echo ""
    echo "7. Complete the merge:"
    echo "   ${BLUE}git merge <branch-name>${NC}"
    echo ""
    echo "8. If you decide not to merge, you can:"
    echo "   - Switch to another branch: ${BLUE}git checkout <branch-name>${NC}"
    echo "   - Delete the problematic branch: ${BLUE}git branch -D <branch-name>${NC}"
    echo ""
    print_status "============================================"
    echo ""
}

# Run main function
main
