#!/usr/bin/env bash
set -euo pipefail

# sync-changes-to-repo.sh
# Copy selected files from this repo to a target local repo, create a branch, commit, optionally push and open a PR.

usage() {
  cat <<EOF
Usage: $0 <TARGET_REPO_PATH> [--branch NAME] [--push] [--pr] [--dry-run]

Options:
  --branch NAME   Branch name to create in the target repo (default auto-generated)
  --push          Push the branch to origin
  --pr            Create a PR with gh (requires gh CLI and repo push privilege)
  --dry-run       Print actions without making changes

Example:
  $0 /Users/me/Documents/abaco-loans-analytics --branch chore/pr-21-sync --push --pr
EOF
  exit 1
}

if [ "$#" -lt 1 ]; then
  usage
fi

TARGET_REPO_PATH="$1"
shift || true

BRANCH=""
DO_PUSH=false
DO_PR=false
DRY_RUN=false

while [ "$#" -gt 0 ]; do
  case "$1" in
    --branch) BRANCH="$2"; shift 2 ;;
    --push) DO_PUSH=true; shift ;;
    --pr) DO_PR=true; shift ;;
    --dry-run) DRY_RUN=true; shift ;;
    -h|--help) usage ;;
    *) echo "Unknown option: $1"; usage ;;
  esac
done

SRC_REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || true)
if [ -z "$SRC_REPO_ROOT" ]; then
  echo "Error: script must be run from within a git repo (source)"
  exit 1
fi

if [ ! -d "$TARGET_REPO_PATH" ]; then
  echo "Error: target repo path does not exist: $TARGET_REPO_PATH"
  exit 1
fi

pushd "$TARGET_REPO_PATH" >/dev/null
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Error: target path is not a git repository: $TARGET_REPO_PATH"
  popd >/dev/null
  exit 1
fi
popd >/dev/null

if [ -z "$BRANCH" ]; then
  BRANCH="chore/pr-21-sync-$(date +%Y%m%d%H%M%S)"
fi

FILES_TO_COPY=(
  ".markdownlint.json"
  "docs/.markdownlint-disabled.md"
  "scripts/fix-workflows.sh"
  ".github/workflows/validate-workflows.yml"
  ".github/workflows/docker-images.yml"
  "CLAUDE.md"
  "README.md"
  "patches"
)

echo "Source repo: $SRC_REPO_ROOT"
echo "Target repo: $TARGET_REPO_PATH"
echo "Branch to create: $BRANCH"

if [ "$DRY_RUN" = true ]; then
  echo "DRY RUN: Will copy the following files if present:"
  for f in "${FILES_TO_COPY[@]}"; do
    echo " - $f"
  done
  echo "No changes will be made."
  exit 0
fi

# Confirm
read -r -p "Proceed to copy files into $TARGET_REPO_PATH and create branch $BRANCH? (y/N) " confirm
if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
  echo "Cancelled."
  exit 0
fi

# Create branch and copy files
pushd "$TARGET_REPO_PATH" >/dev/null

echo "Creating branch: $BRANCH"
git checkout -b "$BRANCH"

for f in "${FILES_TO_COPY[@]}"; do
  SRC_PATH="$SRC_REPO_ROOT/$f"
  if [ -e "$SRC_PATH" ]; then
    DST_DIR="$(dirname "$f")"
    if [ "$DST_DIR" != "." ]; then
      mkdir -p "$DST_DIR"
    fi
    echo "Copying $f"
    if [ -d "$SRC_PATH" ]; then
      # copy directory recursively
      rsync -a --delete "$SRC_PATH/" "$f/"
    else
      cp --parents -v "$SRC_PATH" . || cp -v "$SRC_PATH" "$f"
    fi
    # Ensure scripts are executable
    if [[ "$f" =~ ^scripts/.*\.sh$ ]]; then
      chmod +x "$f" || true
    fi
  else
    echo "Source not found, skipping: $SRC_PATH"
  fi
done

# Stage and commit
git add .
if git diff --staged --quiet; then
  echo "No changes to commit in target repo. Branch ready: $BRANCH"
else
  git commit -m "chore(docs): sync doc and workflow fixes from abaco-loans-analytics-prs"
  echo "Committed changes on branch $BRANCH"
fi

if [ "$DO_PUSH" = true ]; then
  git push --set-upstream origin "$BRANCH"
  echo "Pushed branch $BRANCH to origin"
  if [ "$DO_PR" = true ]; then
    if command -v gh >/dev/null 2>&1; then
      gh pr create --title "chore(docs): apply PR #21 formatting + add markdownlint config and secrets validation" --body "Sync of doc & workflow changes from abaco-loans-analytics-prs (formatting, markdownlint config, secrets validation job, and scripts)." --base main --head "$BRANCH"
    else
      echo "gh CLI not installed; cannot create PR automatically. Install gh to enable PR creation."
    fi
  fi
else
  echo "Branch created locally: $BRANCH (use --push to push and --pr to open a PR)"
fi

popd >/dev/null

echo "Done."