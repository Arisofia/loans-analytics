#!/bin/bash

set -e  # Exit on error

echo "🧹 Starting comprehensive repository cleanup..."
echo ""

# ============================================ 
# 1. REMOVE EXTERNAL INTEGRATION SERVICES
# ============================================ 

echo "📁 Removing external service integrations..."

# Remove service directories
rm -rf services/slack_bot/ 2>/dev/null || true
rm -rf services/figma_sync/ 2>/dev/null || true
rm -rf services/notion_integration/ 2>/dev/null || true
rm -rf services/hubspot_connector/ 2>/dev/null || true

echo "✅ Service directories removed"

# ============================================ 
# 2. REMOVE INTEGRATION SCRIPTS
# ============================================ 

echo "📜 Removing integration scripts..."

# Remove individual scripts
rm -f scripts/post_to_slack.py
rm -f scripts/sync_to_notion.py
rm -f scripts/export_to_figma.py
rm -f scripts/hubspot_*.py
rm -f scripts/cascade_*.py
rm -f scripts/*slack*.py
rm -f scripts/*notion*.py
rm -f scripts/*figma*.py

echo "✅ Integration scripts removed"

# ============================================ 
# 3. REMOVE HIDDEN CONFIGURATION FOLDERS
# ============================================ 

echo "🔍 Removing suspicious hidden folders..."

# These folders don't appear to be essential
rm -rf .rollback/          # Figma-related rollback configs
rm -rf .zencoder/          # Video encoding tool (not needed)
rm -rf .zenflow/           # Gemini AI workflows (experimental)
rm -rf .sonarlint/         # SonarLint cache (regenerates)
rm -rf .sonarqube/         # SonarQube cache (regenerates)

echo "✅ Hidden folders removed"

# ============================================ 
# 4. REMOVE INTEGRATION-SPECIFIC FILES
# ============================================ 

echo "🗂️  Removing integration-specific files..."

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

echo "✅ Integration-specific files removed"

# ============================================ 
# 5. CLEAN PYTHON CODE - Remove Functions
# ============================================ 

echo "🐍 Cleaning Python integration code..."

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

echo "✅ Python integration code removed"

# ============================================ 
# 6. CLEAN CONFIGURATION FILES
# ============================================ 

echo "⚙️  Cleaning configuration files..."

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
        keywords = ['slack', 'notion', 'figma', 'hubspot', 'cascade']
        
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
    'config/notifications.yml',
    'config/integrations.yml',
]

for config in config_files:
    clean_yaml_config(config)

print("✅ Configuration files cleaned")
PYTHON_CONFIG

echo "✅ Configuration files cleaned"

# ============================================ 
# 7. REMOVE GITHUB ACTIONS WORKFLOWS
# ============================================ 

echo "🔄 Cleaning GitHub Actions workflows..."

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
        
        # Remove temp files
        rm -f "$workflow.tmp"
    fi
done

echo "✅ GitHub Actions workflows cleaned"

# ============================================ 
# 8. CLEAN DEPENDENCIES
# ============================================ 

echo "📦 Cleaning dependencies..."

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

echo "✅ npm dependencies removed"

# Clean Python requirements
.venv/bin/python << 'PYTHON_REQS'
import os

req_files = [
    'requirements.txt',
    'python/requirements.txt',
    'requirements-dev.txt',
]

keywords = ['slack', 'notion', 'figma', 'hubspot', 'cascade']

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

echo "✅ Python dependencies cleaned"

# ============================================ 
# 9. CLEAN ENVIRONMENT FILES
# ============================================ 

echo "🔐 Cleaning environment files..."

for env_file in .env .env.local .env.production .env.staging .env.example; do
    if [ -f "$env_file" ]; then
        cp "$env_file" "$env_file.cleanup-backup"
        
        # Comment out integration variables instead of deleting
        sed -i.tmp 's/^\([^#]*SLACK.*\)/# REMOVED: \1/' "$env_file"
        sed -i.tmp 's/^\([^#]*NOTION.*\)/# REMOVED: \1/' "$env_file"
        sed -i.tmp 's/^\([^#]*FIGMA.*\)/# REMOVED: \1/' "$env_file"
        sed -i.tmp 's/^\([^#]*HUBSPOT.*\)/# REMOVED: \1/' "$env_file"
        sed -i.tmp 's/^\([^#]*CASCADE.*\)/# REMOVED: \1/' "$env_file"
        
        rm -f "$env_file.tmp"
        echo "✅ $env_file cleaned"
    fi
done

# ============================================ 
# 10. REMOVE INTEGRATION TESTS
# ============================================ 

echo "🧪 Cleaning integration tests..."

# Remove test files
find tests/ -type f \( -name \"*slack*\" -o -name \"*notion*\" -o -name \"*figma*\" -o -name \"*hubspot*\" \) -delete 2>/dev/null || true

echo "✅ Integration tests removed"

# ============================================ 
# 11. CLEAN DOCUMENTATION
# ============================================ 

echo "📚 Cleaning documentation..."

# Remove or update integration docs
rm -f docs/SLACK_INTEGRATION.md
rm -f docs/NOTION_SETUP.md
rm -f docs/FIGMA_GUIDE.md
rm -f docs/HUBSPOT_CONNECTION.md

echo "✅ Integration documentation removed"

# ============================================ 
# 12. UPDATE .gitignore
# ============================================ 

echo "📝 Updating .gitignore..."

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

echo "✅ .gitignore updated"

# ============================================ 
# 13. VERIFICATION
# ============================================ 

echo ""

echo "🔍 Verification - Searching for remaining references..."

echo ""

echo "Slack references:"
grep -r "slack" --include="*.py" --include="*.yml" --include="*.yaml" src/ config/ .github/ 2>/dev/null | wc -l || echo "0"

echo "Notion references:"
grep -r "notion" --include="*.py" --include="*.yml" --include="*.yaml" src/ config/ .github/ 2>/dev/null | wc -l || echo "0"

echo "Figma references:"
grep -r "figma" --include="*.py" --include="*.yml" --include="*.yaml" src/ config/ .github/ 2>/dev/null | wc -l || echo "0"

echo "HubSpot references:"
grep -r "hubspot" --include="*.py" --include="*.yml" --include="*.yaml" src/ config/ .github/ 2>/dev/null | wc -l || echo "0"

echo "Cascade references:"
grep -r "cascade" --include="*.py" --include="*.yml" --include="*.yaml" src/ config/ .github/ 2>/dev/null | wc -l || echo "0"


echo ""

echo "✨ Cleanup COMPLETE!"
