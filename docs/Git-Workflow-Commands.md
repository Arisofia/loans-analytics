# GitHub Workflow: Copy/Paste Commands

Use these commands to keep the `work` branch in sync, apply fixes, run quality gates, and deliver auditable merges. All commands are ready to paste into a terminal.

## 1) Sync the branch before you start
```bash
git checkout work
git fetch origin
git pull --ff-only origin work
```

## 2) Create or update your feature/fix branch
```bash
# Replace <feature-branch> with your branch name
git checkout -B <feature-branch>
```

## 3) Install and validate (quality gates)
```bash
# JS/TS lint + tests
npm install
npm run lint
npm test

# Python checks (if touching analytics/backends)
pip install -r requirements.txt
pytest

# SonarQube scan (honors sonar-project.properties)
sonar-scanner

# Optional: run Sourcery for automated refactors
sourcery review .
```

## 4) Apply fixes and stage changes
```bash
# After editing files
git status

# Stage tracked + new files
git add README.md docs/Git-Workflow-Commands.md
```

## 5) Commit with traceable message
```bash
git commit -m "Document GitHub workflow commands"
```

## 6) Push and open PR
```bash
git push --set-upstream origin <feature-branch>
```

## 7) Merge via GitHub (preserves audit trail)
Use the GitHub UI to run @coderabbit code review, @sonarqube quality gate, @sourcery automated suggestions, and @gemini reasoning prompts before clicking **Merge**.

If you must merge locally, fast-forward to keep history clean:
```bash
git checkout work
git pull --ff-only origin work
git merge --ff-only <feature-branch>
git push origin work
```

## 8) Post-merge cleanup
```bash
git branch -d <feature-branch>
```

## Notes
- Keep Docker/CI agents (@zencoder for media, @codex for codegen) scoped to dedicated pipelines; avoid running them with elevated credentials on developer machines.
- Always store credentials in `.env` or your platform secret store; never commit secrets.
- Capture test, lint, and SonarQube outputs in PR comments for traceability.
