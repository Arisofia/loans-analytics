# Abaco Loans Analytics - Quickstart

This guide provides the essential first steps to verify that your local environment is correctly configured to run the project.

## Step 1: Verify API Key Configuration

Run the following command to ensure your environment variables are loaded correctly.

```bash
python scripts/test_hubspot_simple.py

C# Step 1: Create the main README.md file
cat > README.md << 'EOF'
# Abaco Loans Analytics - MVP

Este proyecto implementa un sistema multi-agente para análisis de préstamos, conectándose a servicios externos y utilizando un pipeline de datos definido.

### 🏗️ Arquitectura y Componentes

- **Agentes Disponibles**:
  - `scripts/agents/hubspot/segment_manager.py`: Para crear segmentos de contactos con filtros.
  - `scripts/agents/hubspot/list_manager.py`: Para gestionar listas de marketing.
- **Datos**:
  - `data/raw/looker_exports/`: Contiene 3 CSVs con más de 55,000 líneas de datos de "loan tape".
- **Orquestación**:
  - `orchestration/`: Lógica para coordinar la ejecución de agentes y pipelines.
- **Código Base**:
  - `python/`: Módulos principales de la aplicación.

### 🚀 Quickstart

Para configurar y verificar tu entorno local, por favor sigue la guía en `README_QUICKSTART.md`.

*Última actualización del MVP: 29 de Diciembre de 2025*
