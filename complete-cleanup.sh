#!/bin/bash
set -euo pipefail
DRY_RUN=false
LOG_FILE="cleanup.log"

while [[ $# -gt 0 ]]; do
  case $1 in
    --dry-run) DRY_RUN=true; shift ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

log() { echo "$@" | tee -a "$LOG_FILE"; }

if $DRY_RUN; then
  log "🧹 Dry-run mode: No changes will be made."
  RM_CMD="echo Would remove:"
else
  RM_CMD="rm -rf"
fi

log "🧹 Starting comprehensive repository cleanup..."

# 1. REMOVE EXTERNAL INTEGRATION SERVICES
log "📁 Removing external service integrations..."
$RM_CMD services/slack_bot/ services/figma_sync/ services/notion_integration/ services/hubspot_connector/
log "✅ Service directories removed"

# ============================================
# 2. REMOVE INTEGRATION SCRIPTS
# ============================================

log "📜 Removing integration scripts..."

if $DRY_RUN; then
    echo "Would remove: scripts/post_to_slack.py scripts/sync_to_notion.py scripts/export_to_figma.py scripts/hubspot_*.py scripts/cascade_*.py scripts/*slack*.py scripts/*notion*.py scripts/*figma*.py"
else
    rm -f scripts/post_to_slack.py
    rm -f scripts/sync_to_notion.py
    rm -f scripts/export_to_figma.py
    rm -f scripts/hubspot_*.py
    rm -f scripts/cascade_*.py
    rm -f scripts/*slack*.py
    rm -f scripts/*notion*.py
    rm -f scripts/*figma*.py
fi

log "✅ Integration scripts removed"

# ============================================
# 3. REMOVE HIDDEN CONFIGURATION FOLDERS
# ============================================

log "🔍 Removing suspicious hidden folders..."

$RM_CMD .rollback/ .zencoder/ .zenflow/ .sonarlint/ .sonarqube/

log "✅ Hidden folders removed"

# ============================================
# 4. REMOVE INTEGRATION-SPECIFIC FILES
# ============================================

log "🗂️  Removing integration-specific files..."

if $DRY_RUN; then
    echo "Would search and remove files matching *slack*, *notion*, *figma*, *hubspot*"
else
    # Find and remove all slack-related files
    find . -type f \( -name \"*slack*\" -o -name \"*Slack*\" \) \
      -not -path "./.git/*" \
      -not -path "./.venv/*" \
      -not -path "./node_modules/*" \
      -delete 2>/dev/null || true

    # Find and remove all notion-related files
    find . -type f \( -name \"*notion*\" -o -name \"*Notion*\" \) \
      -not -path "./.git/*" \
      -not -path "./.venv/*" \
      -not -path "./node_modules/*" \
      -delete 2>/dev/null || true

    # Find and remove all figma-related files (except git history)
    find . -type f \( -name \"*figma*\" -o -name \"*Figma*\" \) \
      -not -path "./.git/*" \
      -not -path "./.venv/*" \
      -not -path "./node_modules/*" \
      -delete 2>/dev/null || true

    # Find and remove hubspot files
    find . -type f \( -name \"*hubspot*\" -o -name \"*Hubspot*\" \) \
      -not -path "./.git/*" \
      -not -path "./.venv/*" \
      -not -path "./node_modules/*" \
      -delete 2>/dev/null || true
fi

log "✅ Integration-specific files removed"

# ============================================
# 5. CLEAN PYTHON CODE - Remove Functions
# ============================================

log "🐍 Cleaning Python integration code..."

if $DRY_RUN; then
    echo "Would clean Python files of integration logic"
else
    # Backup important files first
    cp src/agents/tools.py src/agents/tools.py.backup 2>/dev/null || true
    cp src/agents/outputs.py src/agents/outputs.py.backup 2>/dev/null || true

    # Use Python to surgically remove integration functions
    .venv/bin/python << 'PYTHON_CLEAN'
import re
import os

def clean_file(filepath, patterns_to_remove):
    if not os.path.exists(filepath):
        print(f"⚠️  {filepath} not found, skipping...")
        return
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    original_length = len(content)
    
    # Remove function definitions matching patterns
    for pattern in patterns_to_remove:
        content = re.sub(pattern, '', content, flags=re.DOTALL | re.IGNORECASE)
    
    # Remove import statements
    imports_to_remove = [
        r'from\s+.*slack.*\s+import.*\n',
        r'import\s+.*slack.*\n',
        r'from\s+.*notion.*\s+import.*\n',
        r'import\s+.*notion.*\n',
        r'from\s+.*figma.*\s+import.*\n',
        r'import\s+.*figma.*\n',
        r'from\s+.*hubspot.*\s+import.*\n',
        r'import\s+.*hubspot.*\n',
        r'from\s+.*cascade.*\s+import.*\n',
        r'import\s+.*cascade.*\n',
        r'from\s+.*.*\s+import.*\n',
        r'import\s+.*.*\n',
    ]
    
    for imp_pattern in imports_to_remove:
        content = re.sub(imp_pattern, '', content, flags=re.IGNORECASE)
    
    # Clean up multiple blank lines
    content = re.sub(r'\n{3,}', '\n\n', content)
    
    with open(filepath, 'w') as f:
        f.write(content)
    
    removed_chars = original_length - len(content)
    print(f"✅ {filepath}: removed {removed_chars} characters")

# Clean src/agents/tools.py
tools_patterns = [
    r' @registry\.register([^)]*slack[^)]*).*?(?=\n @registry\.register|\nclass |\ndef (?!send_slack)|\Z)',
    r'def send_slack_notification.*?(?=\ndef |\nclass |\Z)',
    r' @registry\.register([^)]*notion[^)]*).*?(?=\n @registry\.register|\nclass |\ndef (?!create_notion)|\Z)',
    r'def create_notion_page.*?(?=\ndef |\nclass |\Z)',
]
clean_file('src/agents/tools.py', tools_patterns)

# Clean src/agents/outputs.py
outputs_patterns = [
    r'class SlackOutput.*?(?=\nclass |\Z)',
    r'class NotionOutput.*?(?=\nclass |\Z)',
]
clean_file('src/agents/outputs.py', outputs_patterns)

print("✅ Python code cleaned")
PYTHON_CLEAN
fi

log "✅ Python integration code removed"

# ============================================
# 6. CLEAN CONFIGURATION FILES
# ============================================

log "⚙️  Cleaning configuration files..."

if $DRY_RUN; then
    echo "Would clean YAML config files"
else
    .venv/bin/python << 'PYTHON_CONFIG'
import yaml
import os
import json

def clean_yaml_config(filepath):
    if not os.path.exists(filepath):
        print(f"⚠️  {filepath} not found")
        return
    
    try:
        with open(filepath, 'r') as f:
            data = yaml.safe_load(f)
        
        if data is None:
            return
        
        # Keywords to remove
        keywords = ['slack', 'notion', 'figma', 'hubspot', 'cascade', '']
        
        def remove_matching_keys(obj):
            if isinstance(obj, dict):
                return {
                    k: remove_matching_keys(v)
                    for k, v in obj.items()
                    if not any(kw in k.lower() for kw in keywords)
                }
            elif isinstance(obj, list):
                return [remove_matching_keys(item) for item in obj]
            return obj
        
        cleaned = remove_matching_keys(data)
        
        with open(filepath, 'w') as f:
            yaml.dump(cleaned, f, default_flow_style=False, allow_unicode=True)
        
        print(f"✅ {filepath} cleaned")
    except Exception as e:
        print(f"⚠️  Error cleaning {filepath}: {e}")

# Clean all config files
config_files = [
    'config/pipeline.yml',
    'config/environments/staging.yml',
    'config/environments/production.yml',
    'config/environments/development.yml',
    'config/notifications.yml',
    'config/integrations.yml',
]

for config in config_files:
    clean_yaml_config(config)

print("✅ Configuration files cleaned")
PYTHON_CONFIG
fi

log "✅ Configuration files cleaned"

# ============================================
# 7. REMOVE GITHUB ACTIONS WORKFLOWS
# ============================================

log "🔄 Cleaning GitHub Actions workflows..."

if $DRY_RUN; then
    echo "Would remove integration workflows and clean remaining files"
else
    # Remove integration-specific workflows
    rm -f .github/workflows/*slack*.yml
    rm -f .github/workflows/*notion*.yml
    rm -f .github/workflows/*figma*.yml
    rm -f .github/workflows/*hubspot*.yml
    rm -f .github/workflows/*cascade*.yml
    rm -f .github/workflows/supabase-figma-scheduled.yml
    rm -f .github/workflows/meta-to-figma-dashboard.yml
    rm -f .github/workflows/kpi-csv-sync-to-figma.yml
    rm -f .github/workflows/export-figma-file-data.yml
    rm -f .github/workflows/comment-to-figma.yml

    # Clean remaining workflows of integration references
    for workflow in .github/workflows/*.yml; do
        if [ -f "$workflow" ]; then
            # Create backup
            cp "$workflow" "$workflow.cleanup-backup"
            
            # Remove lines containing integrations (case-insensitive)
            sed -i.tmp '/slack/Id' "$workflow"
            sed -i.tmp '/notion/Id' "$workflow"
            sed -i.tmp '/figma/Id' "$workflow"
            sed -i.tmp '/hubspot/Id' "$workflow"
            sed -i.tmp '/cascade/Id' "$workflow"
            sed -i.tmp '//Id' "$workflow"
            
            # Remove temp files
            rm -f "$workflow.tmp"
        fi
    done
fi

log "✅ GitHub Actions workflows cleaned"

# ============================================
# 8. CLEAN DEPENDENCIES
# ============================================

log "📦 Cleaning dependencies..."

if $DRY_RUN; then
    echo "Would remove npm and python dependencies"
else
    # Remove npm/pnpm dependencies
    pnpm remove \
      @slack/web-api \
      @slack/webhook \
      @notionhq/client \
      figma-api \
      @hubspot/api-client \
      @hubspot/cli \
      2>/dev/null || true

    npm uninstall \
      @slack/web-api \
      @slack/webhook \
      @notionhq/client \
      figma-api \
      @hubspot/api-client \
      @hubspot/cli \
      2>/dev/null || true

    log "✅ npm dependencies removed"

    # Clean Python requirements
    .venv/bin/python << 'PYTHON_REQS'
import os

req_files = [
    'requirements.txt',
    'python/requirements.txt',
    'requirements-dev.txt',
]

keywords = ['slack', 'notion', 'figma', 'hubspot', 'cascade', '']

for req_file in req_files:
    if not os.path.exists(req_file):
        continue
    
    with open(req_file, 'r') as f:
        lines = f.readlines()
    
    # Filter out lines with integration keywords
    filtered = [
        line for line in lines
        if not any(kw in line.lower() for kw in keywords)
    ]
    
    with open(req_file, 'w') as f:
        f.writelines(filtered)
    
    removed = len(lines) - len(filtered)
    print(f"✅ {req_file}: removed {removed} integration dependencies")
PYTHON_REQS
fi

log "✅ Python dependencies cleaned"

# ============================================
# 9. CLEAN ENVIRONMENT FILES
# ============================================

log "🔐 Cleaning environment files..."

if $DRY_RUN; then
    echo "Would clean .env files"
else
    for env_file in .env .env.local .env.production .env.staging .env.example; do
        if [ -f "$env_file" ]; then
            cp "$env_file" "$env_file.cleanup-backup"
            
            # Comment out integration variables instead of deleting
            sed -i.tmp 's/^\([^#]*SLACK.*\)/# REMOVED: \1/' "$env_file"
            sed -i.tmp 's/^\([^#]*NOTION.*\)/# REMOVED: \1/' "$env_file"
            sed -i.tmp 's/^\([^#]*FIGMA.*\)/# REMOVED: \1/' "$env_file"
            sed -i.tmp 's/^\([^#]*HUBSPOT.*\)/# REMOVED: \1/' "$env_file"
            sed -i.tmp 's/^\([^#]*CASCADE.*\)/# REMOVED: \1/' "$env_file"
            sed -i.tmp 's/^\([^#]*LOOKER.*\)/# REMOVED: \1/' "$env_file"
            
            rm -f "$env_file.tmp"
            log "✅ $env_file cleaned"
        fi
    done
fi

# ============================================
# 10. REMOVE INTEGRATION TESTS
# ============================================

log "🧪 Cleaning integration tests..."

if $DRY_RUN; then
    echo "Would remove integration test files"
else
    # Remove test files
    find tests/ -type f \( -name \"*slack*\" -o -name \"*notion*\" -o -name \"*figma*\" -o -name \"*hubspot*\" -o -name \"**\" \) -delete 2>/dev/null || true
fi

log "✅ Integration tests removed"

# ============================================
# 11. CLEAN DOCUMENTATION
# ============================================

log "📚 Cleaning documentation..."

if $DRY_RUN; then
    echo "Would remove integration documentation"
else
    # Remove or update integration docs
    rm -f docs/SLACK_INTEGRATION.md
    rm -f docs/NOTION_SETUP.md
    rm -f docs/FIGMA_GUIDE.md
    rm -f docs/HUBSPOT_CONNECTION.md
fi

log "✅ Integration documentation removed"

# ============================================
# 12. UPDATE .gitignore
# ============================================

log "📝 Updating .gitignore..."

if $DRY_RUN; then
    echo "Would update .gitignore"
else
    cat >> .gitignore << 'GITIGNORE'

# ============================================
# Temporary run data (should not be committed)
# ============================================
data/archives/raw/tmp*.csv
data/metrics/run_*.csv
data/metrics/run_*.parquet
data/metrics/run_*_metrics.json
data/metrics/timeseries/run_*.parquet
logs/runs/run_*/

# Integration backups (cleanup artifacts)
*.cleanup-backup
*.backup

# Hidden tool folders
.rollback/
.zencoder/
.zenflow/
GITIGNORE
fi

log "✅ .gitignore updated"

log "🗂️ Removing -specific files/references..."
if $DRY_RUN; then
    echo "Would remove  files and clean references"
else
    find . -type f \( -name \"**\" -o -name \"**\" \) -not -path "./.git/*" -not -path "./.venv/*" -not -path "./node_modules/*" -delete 2>/dev/null || true
    
    # Clean mentions using python to avoid xargs sed issues on different platforms
    .venv/bin/python << 'PYTHON_LOOKER_CLEAN'
import os
import re

def remove__references(root_dir):
    for root, dirs, files in os.walk(root_dir):
        # Skip git and venv directories
        if '.git' in dirs:
            dirs.remove('.git')
        if '.venv' in dirs:
            dirs.remove('.venv')
        if 'node_modules' in dirs:
            dirs.remove('node_modules')
            
        for file in files:
            file_path = os.path.join(root, file)
            # Only process text files
            if not file.endswith(('.py', '.yml', '.yaml', '.md', '.json', '.sh', '.js', '.ts', '.tsx')):
                continue
                
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                if '' in content.lower():
                    # Simple replacement of '' with nothing (case insensitive logic needed but simple replace is what sed did)
                    # The sed command was: sed -i 's///g' which is lowercase specific
                    new_content = content.replace('', '')
                    new_content = new_content.replace('', '')
                    
                    if content != new_content:
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(new_content)
                        print(f"Cleaned  from {file_path}")
            except Exception as e:
                print(f"Error processing {file_path}: {e}")

remove__references('.')
PYTHON_LOOKER_CLEAN
fi
log "✅  removed"

# 14. POST-CLEANUP: Unify configs (merge integrations.yml into pipeline.yml if exists)
if [ -f config/integrations.yml ]; then
  if $DRY_RUN; then
      echo "Would merge config/integrations.yml into config/pipeline.yml"
  else
      cat config/integrations.yml >> config/pipeline.yml
      rm config/integrations.yml
      log "✅ Unified integrations into pipeline.yml"
  fi
fi

# Final commit if not dry-run
if ! $DRY_RUN; then
  log "Creating final commit..."
  git add . || true
  git commit -m "Comprehensive cleanup for new implementation: Removed integrations" || echo "Nothing to commit"
fi

log "Cleanup complete. Review logs."