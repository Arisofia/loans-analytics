
"""
Notion Metrics Importer
----------------------
Imports and processes metrics from a Notion database.
Security: All secrets and tokens are loaded from environment variables.
Error handling: Robust error handling and logging.
Config hygiene: No hardcoded secrets or headers.
"""

import os
import sys
import statistics
import logging
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path for python/ modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from python.notion_integration.client import NotionClient

# Configure logging
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)


def extraer_propiedades_fila(fila: Dict[str, Any]) -> Dict[str, Any]:
    """Extrae propiedades de una fila incluyendo métricas."""
    propiedades = fila.get('properties', {})
    
    datos = {
        'id': fila.get('id'),
        'titulo': None,
        'contenido': None,
        'visualizaciones': None,
        'alcance': None,
        'engagement': None,
        'ctr': None,
        'comparacion_actual': None
    }

    # Helper to safely extract text
    def get_text(prop):
        if prop and prop.get('type') in ['title', 'rich_text']:
            key = prop.get('type')
            items = prop.get(key, [])
            return ''.join(t.get('plain_text', '') for t in items) if items else None
        return None

    # Helper to safely extract number
    def get_number(prop):
        return prop.get('number') if prop and prop.get('type') == 'number' else None

    datos['titulo'] = get_text(propiedades.get('Titulo'))
    datos['contenido'] = get_text(propiedades.get('Contenido'))
    datos['visualizaciones'] = get_number(propiedades.get('Visualizaciones'))
    datos['alcance'] = get_number(propiedades.get('Alcance'))
    datos['engagement'] = get_number(propiedades.get('Engagement'))
    datos['ctr'] = get_number(propiedades.get('CTR'))
    datos['comparacion_actual'] = get_text(propiedades.get('Comparación de Rendimiento'))

    return datos

def calcular_estadisticas_metricas(todas_filas: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calcula estadísticas globales de las métricas."""
    metrics = ['visualizaciones', 'alcance', 'engagement']
    stats = {}

    for metric in metrics:
        values = [f[metric] for f in todas_filas if f.get(metric) is not None]
        
        if values:
            stats[metric] = {
                'promedio': statistics.mean(values),
                'mediana': statistics.median(values),
                'max': max(values),
                'min': min(values),
                'count': len(values)
            }
            if len(values) >= 2:
                quantiles = statistics.quantiles(values, n=4)
                stats[metric].update({
                    'p25': quantiles[0],
                    'p75': quantiles[2]
                })
        else:
            stats[metric] = None

    return stats

if __name__ == "__main__":
    """
    Example CLI usage: securely loads configs from environment.
    """
    db_id = os.getenv("NOTION_DATABASE_ID")
    if db_id:
        print(f"Starting import for DB: {db_id}")
        try:
            client = NotionClient()
            rows = client.query_database(db_id)
            processed = [extraer_propiedades_fila(r) for r in rows]
            stats = calcular_estadisticas_metricas(processed)
            print(stats)
        except Exception as e:
            logger.error(f"Failed to import Notion metrics: {e}")
    else:
        logger.error("Set NOTION_DATABASE_ID to run this script.")