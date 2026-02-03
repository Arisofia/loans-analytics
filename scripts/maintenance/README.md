# Maintenance Scripts

Scripts for repository maintenance, validation, and housekeeping.

## Scripts

**Repository Maintenance:**
- `repo-doctor.sh` - Comprehensive repository health check
- `repo_maintenance.sh` - Routine maintenance tasks
- `cleanup_workflow_runs_by_count.sh` - Clean up old workflow runs
- `merge_all_branches.sh` - Batch merge branches

**Validation:**
- `validate_structure.py` - Validate repository structure
- `validate_complete_stack.py` - Validate full application stack
- `validate_copilot_agents.py` - Validate AI agent configurations
- `validate_agent_checklist.py` - Validate agent checklist compliance

## Usage Examples

```bash
# Run repository health check
./scripts/maintenance/repo-doctor.sh

# Validate structure
python scripts/maintenance/validate_structure.py

# Cleanup old workflows
./scripts/maintenance/cleanup_workflow_runs_by_count.sh

# Validate agents
python scripts/maintenance/validate_copilot_agents.py
```

## Maintenance Schedule

- **Daily**: CI/CD runs validation scripts automatically
- **Weekly**: Run repo-doctor.sh
- **Monthly**: Clean up workflow runs
- **Quarterly**: Full repository audit
