# PR Sync Helper Workflow

This workflow keeps pull request branches aligned with their base branch's latest changes without having to sync locally.

## How it works
- Triggers manually via **Run workflow** with a `pr_number` input or from an issue comment containing `/pr-sync` on an open pull request.
- Looks up the PR metadata, skips forks (the default token cannot push to forked branches), and checks out the head branch.
- Merges the current base branch into the PR branch and pushes the update back to the same branch.

## Usage
1. Open the **Actions** tab and select **PR Sync Helper**.
2. Choose **Run workflow**, supply the pull request number, and start the run. Alternatively, comment `/pr-sync` on the PR to trigger the same process.
3. If merge conflicts exist the workflow will fail, mirroring the conflict you would see locally.

## Permissions
The workflow uses the default `GITHUB_TOKEN` with `contents` and `pull-requests` write permissions. Branch protection rules still apply, so the push will be blocked if required checks or approvals prevent it.
