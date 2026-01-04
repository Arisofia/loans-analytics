Title: Loosen langchain pins in requirements.txt (replace strict pins with names)

Summary:
Replace strict version pins for langchain-related packages with unpinned package names to allow the downstream project's resolver to select compatible versions.

Files changed (patch):
- patches/loosen-langchain-pins.patch

Details / Rationale:
In some downstream repos (e.g., Talent Analytics / Growth Experiments) strict pins such as `langchain==0.3.13` and `langchain-core==0.3.28` cause pip's resolver to hit ResolutionImpossible errors when other libraries (openai / anthropic) require newer versions. Replacing strict pins with package names (e.g., `langchain`) makes the requirements more flexible and avoids immediate breakage across repositories.

How to apply:
- In the target repo (checkout target branch):
  git apply /path/to/patches/loosen-langchain-pins.patch
  git add requirements.txt
  git commit -m "chore: loosen langchain pin constraints in requirements.txt"
  git push -u origin <branch>
  gh pr create --title "chore: loosen langchain pins" --body-file patches/pr_loosen_langchain.md --base main --head <branch>

Optional: apply our OpenTelemetry constraints if you want to prevent similar dev-time conflicts:
- git apply /path/to/patches/constraints-opentelemetry.patch
- git add constraints/opentelemetry-constraints.txt
- git commit -m "chore: add OpenTelemetry constraints file"
- git push

Validation steps (after applying the patch):
1. Create a Python 3.11 venv and activate it:
   python3.11 -m venv .venv311 && source .venv311/bin/activate
2. Install and check (if you applied the constraints file, include it via -c or the requirements file may reference it):
   python -m pip install -r requirements.txt
   python -m pip check
3. Run tests:
   python -m pytest -q

Notes:
- If the target repo regularly requires fully pinned dependencies for reproducibility, consider using a constraints file or a lock file instead of hard pins in `requirements.txt`.
- I included a constraints patch (`patches/constraints-opentelemetry.patch`) and a dependency-validate workflow to help prevent dev-time conflicts.
- I also included a patch (`patches/add-fail-on-missing-to-reusable-secret-check.patch`) that adds a `fail_on_missing` boolean `workflow_call` input to the reusable secret-check workflow so downstream repos can opt-in to permissive mode (default: strict/fail).
