import unittest
from scripts.import_notion_metrics import extraer_propiedades_fila, calcular_estadisticas_metricas

class TestImportNotionMetrics(unittest.TestCase):
    def test_extraer_propiedades_fila(self):
        """Test extraction of properties from a mocked Notion row."""
        mock_row = {
            "id": "123",
            "properties": {
                "Titulo": {"type": "title", "title": [{"plain_text": "Test Title"}]},
                "Contenido": {"type": "rich_text", "rich_text": [{"plain_text": "Content"}]},
                "Visualizaciones": {"type": "number", "number": 100},
                "Alcance": {"type": "number", "number": 50},
                "Engagement": {"type": "number", "number": 10},
                "CTR": {"type": "number", "number": 0.05},
                "Comparación de Rendimiento": {"type": "rich_text", "rich_text": [{"plain_text": "Up"}]}
            }
        }
        result = extraer_propiedades_fila(mock_row)
        
        self.assertEqual(result["id"], "123")
        self.assertEqual(result["titulo"], "Test Title")
        self.assertEqual(result["contenido"], "Content")
        self.assertEqual(result["visualizaciones"], 100)
        self.assertEqual(result["alcance"], 50)
        self.assertEqual(result["engagement"], 10)
        self.assertEqual(result["ctr"], 0.05)
        self.assertEqual(result["comparacion_actual"], "Up")

    def test_calcular_estadisticas_metricas(self):
        """Test calculation of statistics from a list of processed rows."""
        data = [
            {"visualizaciones": 100, "alcance": 50, "engagement": 10},
            {"visualizaciones": 200, "alcance": 100, "engagement": 20},
            {"visualizaciones": 300, "alcance": 150, "engagement": 30},
            {"visualizaciones": None, "alcance": None, "engagement": None}, # Should be ignored
        ]
        stats = calcular_estadisticas_metricas(data)
        
        self.assertEqual(stats["visualizaciones"]["promedio"], 200)
        self.assertEqual(stats["visualizaciones"]["max"], 300)
        self.assertEqual(stats["visualizaciones"]["min"], 100)
        self.assertEqual(stats["visualizaciones"]["count"], 3)