#!/bin/bash

echo "=== Eliminando integraciones de Cascade, Slack y HubSpot ==="

# 1. ELIMINAR ARCHIVOS DE HUBSPOT
echo "Eliminando archivos de HubSpot..."
git rm -rf scripts/agents/hubspot/ 2>/dev/null
git rm -f scripts/fetch_hubspot_data.py 2>/dev/null
find . -type f -name "*hubspot*" -not -path "./.git/*" -not -path "./.venv/*" -not -path "./apps/web/.venv/*" -exec git rm -f {} \; 2>/dev/null

# 2. ELIMINAR ARCHIVOS DE SLACK
echo "Eliminando archivos de Slack..."
git rm -f scripts/post_to_slack.py 2>/dev/null
git rm -f .github/workflows/notify-slack.yml 2>/dev/null
find . -type f -name "*slack*" -not -path "./.git/*" -not -path "./.venv/*" -not -path "./apps/web/.venv/*" -exec git rm -f {} \; 2>/dev/null

# 3. ELIMINAR ARCHIVOS DE CASCADE
echo "Eliminando archivos de Cascade..."
find . -type f -name "*cascade*" -not -path "./.git/*" -not -path "./.venv/*" -not -path "./apps/web/.venv/*" -exec git rm -f {} \; 2>/dev/null

# 4. ELIMINAR REFERENCIAS EN ARCHIVOS DE CONFIGURACIÓN
echo "Eliminando referencias en archivos de configuración..."

# Nota: Las modificaciones a secrets.py, setup.py y __init__.py se han aplicado directamente
# a través del asistente de código, pero este paso asegura que se añadan al commit si hubo cambios manuales.
if [ -f "src/config/secrets.py" ]; then
    git add src/config/secrets.py
fi

if [ -f "config/agents/specs/python/setup.py" ]; then
    git add config/agents/specs/python/setup.py
fi

if [ -f "src/agents/__init__.py" ]; then
    git add src/agents/__init__.py
fi

# 5. ELIMINAR MENCIONES EN DOCUMENTACIÓN
echo "Eliminando menciones en documentación..."
find . -type f \( -name "*.md" -o -name "*.txt" -o -name "*.rst" \) \
    -not -path "./.git/*" \
    -not -path "./.venv/*" \
    -not -path "./apps/web/.venv/*" \
    -exec sed -i.bak -E '/[Hh]ubspot|[Ss]lack|[Cc]ascade/d' {} \;

# 6. LIMPIAR ARCHIVOS BACKUP
find . -name "*.bak" -delete

echo "=== ✅ Integrations removed successfully ==="
echo ""
echo "Recuerda hacer commit de los cambios:"
echo 'git commit -m "chore: remove Cascade, Slack, and HubSpot integrations"'