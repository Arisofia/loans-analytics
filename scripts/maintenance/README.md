# Maintenance Scripts

Scripts for repository maintenance, validation, and housekeeping.

## Scripts

**Repository Maintenance:**

- `repo-doctor.sh` - Comprehensive repository health check
- `repo_maintenance.sh` - Routine maintenance tasks
- `cleanup_workflow_runs_by_count.sh` - Clean up old workflow runs

**Validation:**

- `validate_structure.py` - Validate repository structure
- `validate_complete_stack.py` - Validate full application stack
- `validate_copilot_agents.py` - Validate AI agent configurations
- `validate_agent_checklist.py` - Validate agent checklist compliance

## Canonical Commands

For execution commands and approved variants, use:

- `docs/operations/SCRIPT_CANONICAL_MAP.md`
- `docs/REPOSITORY_MAINTENANCE.md`

## Maintenance Schedule

- **Daily**: CI/CD runs validation scripts automatically
- **Weekly**: Run repo-doctor.sh
- **Monthly**: Clean up workflow runs
- **Quarterly**: Full repository audit
