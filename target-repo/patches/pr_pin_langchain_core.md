Title: chore(deps): pin langchain-core to >=0.3.34,<0.4.0 to avoid resolution conflicts

Summary
-------
This change constrains `langchain-core` to a range known to be compatible with our usage and downstream consumers:

  langchain-core>=0.3.34,<0.4.0

Why
---
CI observed `ResolutionImpossible` errors caused by conflicting `langchain` / `langchain-core` requirements in downstream repos. Adding a conservative constraint reduces the chance of cross-repo resolution conflicts.

Testing
-------
- `pip install -r requirements.txt && pip check`
- `pytest -q` (all tests should pass locally)

Rollback
------
Revert the change, or adjust the constraint to widen/narrow range based on tested compatibility.

Notes
-----
If this repo uses `pyproject.toml` or `poetry`, apply the equivalent constraint there instead of `requirements.txt`.
