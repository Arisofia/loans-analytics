# Repository Cleanup Procedures and Merge Conflict Resolution

## Overview

This document provides guidelines for maintaining a clean repository and resolving merge conflicts in the `abaco-loans-analytics` project. Following these procedures helps prevent issues and ensures smooth collaboration.

---

## Table of Contents

1. [Repository Cleanup Procedures](#repository-cleanup-procedures)
2. [Merge Conflict Resolution Steps](#merge-conflict-resolution-steps)
3. [Best Practices](#best-practices)
4. [Troubleshooting](#troubleshooting)
5. [Git Configuration for Conflict Resolution](#git-configuration-for-conflict-resolution)
6. [References](#references)

---

## Repository Cleanup Procedures

### 1. Local Repository Cleanup

#### Remove Local Branches No Longer Needed

```bash
# List all local branches
git branch

# Delete a local branch (must be checked out from it)
git branch -d <branch-name>

# Force delete a local branch
git branch -D <branch-name>

# Delete multiple branches at once
git branch -d <branch-1> <branch-2> <branch-3>
```

#### Clean Up Tracking References

```bash
# Fetch and prune remote-tracking references
git fetch --prune

# Equivalent to: git fetch --all --prune
git fetch --all --prune
```

#### Remove Untracked Files

```bash
# List untracked files
git clean -n

# Remove untracked files (dry-run first recommended)
git clean -f

# Remove untracked files and directories
git clean -fd

# Remove untracked files, directories, and ignored files
git clean -fdx
```

#### Garbage Collection

```bash
# Run Git's built-in garbage collection
git gc

# Aggressive garbage collection
git gc --aggressive
```

### 2. Remote Repository Cleanup

#### Delete Remote Branches

```bash
# Delete a remote branch
git push origin --delete <branch-name>

# Alternative syntax
git push origin :<branch-name>

# Delete multiple remote branches
git push origin --delete <branch-1> <branch-2> <branch-3>
```

#### Clean Up Stale Remote Tracking Branches

```bash
# Remove stale remote-tracking branches
git remote prune origin

# Equivalent to: git fetch --prune
git fetch origin --prune
```

#### Delete GitHub Branches (Web Interface)

1. Navigate to the repository on GitHub
2. Click on "Branches" tab
3. Find the branch to delete
4. Click the trash icon next to the branch name

### 3. Commit History Cleanup

#### Rebase to Clean Up Commits

```bash
# Interactive rebase on the last N commits
git rebase -i HEAD~N

# Interactive rebase on a specific branch
git rebase -i <base-branch>
```

**In interactive rebase, use:**
- `pick` - Keep commit as-is
- `reword` - Keep commit but edit message
- `squash` - Combine with previous commit
- `fixup` - Combine with previous commit (discard message)
- `drop` - Remove commit entirely

#### Amend the Last Commit

```bash
# Modify the last commit message
git commit --amend -m "New commit message"

# Add changes to the last commit without changing message
git add <files>
git commit --amend --no-edit
```

### 4. Large File Cleanup

#### Identify Large Files

```bash
# Show largest files in the repository
git rev-list --all --objects | sort -k 2 | tail -20

# Using Git Large File Storage (LFS) for large files
git lfs install
git lfs track "*.{psd,zip,iso}"
git add .gitattributes
git commit -m "Track large files with Git LFS"
```

### 5. Regular Maintenance Schedule

- **Weekly**: Remove merged local branches and prune remote branches
- **Monthly**: Run garbage collection and review commit history
- **Quarterly**: Audit large files and consider archiving old branches
- **As Needed**: Clean up stale branches and perform targeted cleanups

---

## Merge Conflict Resolution Steps

### 1. Understanding Merge Conflicts

Merge conflicts occur when Git cannot automatically combine changes from different branches. Common scenarios include:
- Same file modified in different branches
- Same line edited in different ways
- File deleted in one branch but modified in another

### 2. Detecting Conflicts

When pulling or merging:

```bash
git pull origin <branch-name>
# or
git merge <branch-name>
```

Git will indicate conflicts with markers like:
```

```

### 3. Conflict Resolution Strategies

#### Strategy A: Accept Current Changes

```bash
# Keep all changes from the current branch
git checkout --ours <file-name>

# For all files in conflict
git checkout --ours .
```

#### Strategy B: Accept Incoming Changes

```bash
# Keep all changes from the incoming branch
git checkout --theirs <file-name>

# For all files in conflict
git checkout --theirs .
```

#### Strategy C: Manual Resolution

1. Open the conflicted file(s) in your editor
2. Locate the conflict markers (`<<<<<<<`, `=======`, `>>>>>>>`)
3. Edit the content to combine or select the desired changes
4. Remove the conflict markers
5. Save the file

Example:
```
def calculate_interest(principal, rate, time=1):
    return principal * rate * time * 0.01
```

**Resolved:**
```python
def calculate_interest(principal, rate, time=1):
    return principal * rate * time * 0.01
```

#### Strategy D: Use Merge Tool

```bash
# Configure merge tool
git config merge.tool <tool-name>
# Examples: vimdiff, meld, kdiff3, tortoisemerge

# Launch merge tool
git mergetool
```

### 4. Completing the Merge

```bash
# After resolving conflicts, add the resolved files
git add <resolved-file-names>

# Complete the merge
git commit -m "Merge <branch-name> and resolve conflicts"
```

### 5. Resolving Conflicts During Rebase

```bash
# Start an interactive rebase
git rebase -i <base-branch>

# After conflicts occur, edit the conflicted files
# Then stage the changes
git add <resolved-files>

# Continue the rebase
git rebase --continue

# If you want to abort the rebase
git rebase --abort
```

### 6. Handling Pull Request Conflicts

**On GitHub:**
1. Navigate to the pull request with conflicts
2. Click "Resolve conflicts" button
3. Edit the conflicted code directly in the GitHub web editor
4. Remove conflict markers
5. Click "Mark as resolved"
6. Click "Commit merge"

**From Command Line:**
```bash
# Fetch the latest changes from the base branch
git fetch origin

# Merge the base branch into your feature branch
git merge origin/main

# Resolve conflicts as described above
# Then push to update the PR
git push origin <feature-branch>
```

---

## Best Practices

### Preventing Conflicts

1. **Keep Branches Short-Lived**: Merge frequently to minimize divergence
2. **Communicate**: Discuss major changes with team members
3. **Work on Different Files**: When possible, edit different files
4. **Pull Before Push**: Always sync with remote before pushing
5. **Use Feature Branches**: Isolate work using descriptive branch names

### Conflict Resolution Best Practices

1. **Understand the Code**: Don't just resolve mechanically; understand what each change does
2. **Test After Resolution**: Run tests to ensure the resolved code works
3. **Discuss with Contributors**: If unsure, contact the person who made the other change
4. **Document Changes**: Explain in commit message why specific changes were chosen
5. **Review Carefully**: Have someone review the resolved merge

### General Repository Health

1. **Keep `.gitignore` Updated**: Prevent unnecessary files from being tracked
2. **Use Meaningful Commit Messages**: Follow conventional commits format
3. **Regular Rebasing**: Keep feature branches up-to-date with main
4. **Archive Old Branches**: Move completed work out of active branches
5. **Monitor Repository Size**: Track and manage repository growth

---

## Troubleshooting

### Common Issues and Solutions

#### Issue: "Already up to date" but expecting changes

```bash
# Verify remote branches
git branch -r

# Fetch latest remote changes
git fetch --all

# Merge explicitly
git merge origin/<branch-name>
```

#### Issue: Accidental Merge, Need to Undo

```bash
# Undo the last merge (if not pushed)
git merge --abort

# Undo a completed merge
git revert -m 1 <commit-hash>

# Reset to before the merge
git reset --hard HEAD~1
```

#### Issue: Conflicts in Too Many Files

```bash
# Start fresh with a clean merge
git merge --abort

# Rebase instead of merge (cleaner history)
git rebase origin/main

# Or cherry-pick specific commits
git cherry-pick <commit-hash>
```

#### Issue: Lost Commits After Merge Conflict

```bash
# Check the reflog to find lost commits
git reflog

# Recover a lost commit
git checkout <lost-commit-hash>

# Create a new branch from the recovered commit
git checkout -b recovered-branch
```

#### Issue: Stale Local Branches Tracking Deleted Remote Branches

```bash
# Prune all stale remote-tracking references
git fetch --all --prune

# Verify cleanup
git branch -r
```

---

## Git Configuration for Conflict Resolution

### Auto-Merge Configuration

```bash
# Set merge strategy preference
git config merge.ff only  # Fast-forward only

git config merge.ff true  # Allow fast-forward (default)

git config merge.ff false # Always create merge commit
```

### Configure Diff and Merge Tools

```bash
# Set default merge tool
git config --global merge.tool vimdiff
git config --global merge.conflictstyle diff3

# Set default diff tool
git config --global diff.tool vimdiff
```

---

## References

- [Git Documentation - Merging](https://git-scm.com/docs/git-merge)
- [Git Documentation - Rebase](https://git-scm.com/docs/git-rebase)
- [GitHub - Resolving Merge Conflicts](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/addressing-merge-conflicts)
- [Conventional Commits](https://www.conventionalcommits.org/)

---

**Last Updated**: 2026-01-11  
**Maintained By**: Repository Administrators  
**Version**: 1.0
