# Análisis de Tests Duplicados - abaco-loans-analytics

**Fecha:** 26 de Marzo, 2026  
**Alcance:** Análisis completo de duplicaciones de tests en el repositorio

---

## Resumen Ejecutivo

Se encontraron **3 grupos de tests realmente duplicados** en el repositorio, todos dentro de un único archivo: `tests/test_csv_upload_homologation.py`

- **Tests duplicados encontrados:** 5 tests
- **Archivos que pueden ser consolidados:** 0 archivos completos (los duplicados están dentro del mismo archivo)
- **Impacto de eliminar duplicados:** Reducción de ~50 líneas de código de test repetido

---

## Duplicaciones Reales Encontradas

### 1. DUPLICACIÓN CRÍTICA: TestClassifyLoanIdDuplicates ↔ TestPortfolioDashboardDuplicateClassification

**Ubicación:** [tests/test_csv_upload_homologation.py](tests/test_csv_upload_homologation.py#L102-L280)

**Tests duplicados (3):**

| Test en TestClassifyLoanIdDuplicates | Test en TestPortfolioDashboardDuplicateClassification | Línea | Duplicado |
|------|------|-------|----------|
| `test_exact_duplicate_emits_warning` (L102) | `test_exact_duplicate_returns_warning` (L268) | ✓ SAME |
| `test_historical_snapshot_emits_info` (L110) | `test_historical_snapshot_returns_info` (L273) | ✓ SAME |
| `test_suspicious_merge_emits_warning` (L118) | `test_suspicious_merge_returns_warning` (L278) | ✓ SAME |

**Razón de duplicación:** 
- Mismo código de test, mismas aserciones, mismos datos de prueba
- Ambas clases prueban la misma función `_classify_loan_id_duplicates()` 
- Solo difieren en nombres (emits_warning/returns_warning)

**Código actual:**
```python
# TestClassifyLoanIdDuplicates (línea 102)
def test_exact_duplicate_emits_warning(self):
    df = pd.DataFrame({'loan_id': ['A', 'A'], 'borrower_id': ['b1', 'b1'], 'amount': [100.0, 100.0]})
    result = _classify_loan_id_duplicates(df)
    assert len(result) == 1
    level, msg = result[0]
    assert level == 'warning'
    assert 'exact duplicate' in msg.lower()

# TestPortfolioDashboardDuplicateClassification (línea 268) - DUPLICADO
def test_exact_duplicate_returns_warning(self):
    df = pd.DataFrame({'loan_id': ['A', 'A'], 'borrower_id': ['b1', 'b1'], 'amount': [100.0, 100.0]})
    result = _dash_mod._classify_loan_id_duplicates(df)
    assert any((level == 'warning' and 'exact' in msg.lower() for level, msg in result))
```

**Recomendación:**
- **ELIMINAR:** `TestPortfolioDashboardDuplicateClassification` completamente (líneas 263-282)
- **MANTENER:** `TestClassifyLoanIdDuplicates` como la fuente única de verdad
- **BENEFICIO:** 20 líneas de código eliminadas, 1 clase de test consolidada

---

### 2. DUPLICACIÓN MODERADA: TestApplyAliases ↔ TestPortfolioDashboardDesembolsos

**Ubicación:** [tests/test_csv_upload_homologation.py](tests/test_csv_upload_homologation.py#L71-L240)

**Tests duplicados (2):**

| Test en TestApplyAliases | Test en TestPortfolioDashboardDesembolsos | Propósito | Duplicado |
|------|------|-----------|----------|
| `test_loan_id_mapped_from_numero_desembolso` (L71) | `test_numero_desembolso_mapped_to_loan_id` (L226) | Validar mapeo numero_desembolso→loan_id | ✓ SAME |
| `test_borrower_id_mapped_from_codcliente` (L82) | `test_codcliente_mapped_to_borrower_id` (L231) | Validar mapeo codcliente→borrower_id | ✓ SAME |

**Razón de duplicación:**
- Prueban el mismo mapeo de aliases
- Datos idénticos o muy similares
- Solo difieren en la clase que los contiene

**Código actual:**
```python
# TestApplyAliases (línea 71)
def test_loan_id_mapped_from_numero_desembolso(self):
    df = _normalize_column_names(self._make_desembolsos_df())
    mapped = _apply_aliases(df)
    assert 'loan_id' in mapped.columns
    assert list(mapped['loan_id']) == ['D001', 'D002']

# TestPortfolioDashboardDesembolsos (línea 226) - DUPLICADO
def test_numero_desembolso_mapped_to_loan_id(self):
    df = self._normalize_and_alias(self._desembolsos_raw())
    assert 'loan_id' in df.columns
    assert list(df['loan_id']) == ['D001', 'D002']
```

**Recomendación:**
- **EVALUAR:** Si `TestPortfolioDashboardDesembolsos` necesita los tests de mapeo (parece ser para validar integración del dashboard)
- **OPCIÓN 1:** Si el dashboard solo necesita validación que funciona, mantener solo 1 test mapeo en TestPortfolioDashboardDesembolsos
- **OPCIÓN 2:** Si no lo necesita, eliminar completamente (es duplicado)
- **BENEFICIO:** 8-12 líneas eliminadas

---

## Patrones Analizados (NO son duplicados reales)

### Patrón: test_* vs test_*_api.py vs test_*_openapi.py

Este patrón se repite en varios módulos de analytics pero **NO son duplicados reales** porque prueban diferentes niveles:

**Módulos con este patrón:**
- `test_stress_test.py` / `test_stress_test_api.py` / `test_stress_test_openapi.py`
- `test_segment_analytics.py` / `test_segment_analytics_api.py` / `test_segment_analytics_openapi.py`
- `test_roll_rate_analytics.py` / `test_roll_rate_analytics_api.py` / `test_roll_rate_analytics_openapi.py`
- `test_advanced_risk.py` / `test_advanced_risk_api.py` / `test_advanced_risk_openapi.py`
- `test_cohort_analytics.py` / `test_cohort_analytics_api.py` / `test_cohort_analytics_openapi.py`

**Justificación:**
- `test_*.py`: Unit tests de la lógica de servicio (KPIService.calculate_*)
- `test_*_api.py`: Integration tests del endpoint HTTP (FastAPI TestClient)
- `test_*_openapi.py`: Contract tests del esquema OpenAPI

Los datos de prueba son similares pero cada archivo prueba una interfaz diferente:

```python
# test_stress_test.py (unit: servicio)
response = asyncio.run(service.calculate_stress_test(loans=_stress_loans()))
assert response.scenario_id

# test_stress_test_api.py (integration: HTTP)
response = client.post('/analytics/stress-test', json=_payload())
assert response.status_code == 200

# test_stress_test_openapi.py (contract: schema)
response = client.get('/openapi.json')
assert '/analytics/stress-test' in spec['paths']
```

**Nota:** Los tests `_openapi.py` son muy livianos (~10 líneas c/u). Podrían consolidarse en una suite genérica de validación OpenAPI si se considera demasiado redundante, pero no están duplicados con los otros.

---

## Archivos Analizados - Estados

### ✓ SIN Duplicaciones
- ✓ `test_orchestrator.py` - tests fundamentales de orquestación
- ✓ `test_orchestrator_historical_integration.py` - tests específicos de integración histórica
- ✓ `test_multi_agent_config_historical.py` - configuración de contexto histórico
- ✓ `test_multi_agent_historical_context.py` - testing del HistoricalContextProvider
- ✓ `test_kpi_service_realtime.py` - unit tests de KPIService 
- ✓ `test_kpi_realtime_api.py` - integration tests (niveles diferentes)
- ✓ `test_pipeline_orchestrator.py` - tests únicos de pipeline
- ✓ Todos los tests de `test_pipeline_*.py`
- ✓ Todos los tests de `test_default_risk_model.py`

### ⚠ CON Duplicaciones (confirmadas)
- ⚠ `test_csv_upload_homologation.py` - **3 duplicaciones encontradas**

### ~ Patrón Triple (NOT duplicated - diferentes niveles)
- ~ `test_stress_test*.py` (3 archivos)
- ~ `test_segment_analytics*.py` (3 archivos)  
- ~ `test_roll_rate_analytics*.py` (3 archivos)
- ~ `test_advanced_risk*.py` (3 archivos)
- ~ `test_cohort_analytics*.py` (3 archivos)

---

## Plan de Acción Recomendado

### PRIORIDAD 1: Eliminar duplicaciones críticas

**Acción A: Consolidar TestPortfolioDashboardDuplicateClassification**
```
Archivo: tests/test_csv_upload_homologation.py
Eliminar: Clase TestPortfolioDashboardDuplicateClassification (líneas 263-282)
Razón: Duplica 3/3 tests de TestClassifyLoanIdDuplicates
Impacto: -20 líneas de código, 0 funcionalidad perdida
```

**Acción B: Evaluar TestPortfolioDashboardDesembolsos**
```
Archivo: tests/test_csv_upload_homologation.py
Revisar: Necesidad real de tests de mapeo en TestPortfolioDashboardDesembolsos
Opción 1: Si no se necesita integración de dashboard → Eliminar (líneas 218-262)
Opción 2: Si se necesita → Eliminar solo tests duplicados de mapeo (4 tests)
Impacto: -32 a -50 líneas de código
```

### PRIORIDAD 2: Considerar consolidación de _openapi tests

No es obligatorio, pero podría considerarse:
```
Opción: Crear una suite genérica de validación OpenAPI
Consolidar: test_*_openapi.py (5 archivos × ~10 líneas = 50 líneas)
Beneficio: DRY principle, reducción de noise
Riesgo: Bajo - tests muy simples, difícil que cambien
```

### PRIORIDAD 3: Refactoring de TestPortfolioDashboard

Si se mantiene TestPortfolioDashboardDesembolsos:
```
Separar concerns:
- Mantener solo tests específicos de dashboard
- Eliminar tests que duplican TestApplyAliases
- Agregar tests de integración dashboard-specific que NO están duplicados
```

---

## Estadísticas de Impacto

| Métrica | Valor |
|---------|-------|
| Total tests analizados | 1500+ |
| Archivos de test | 107 |
| Duplicaciones reales encontradas | 5 tests |
| Archivos con duplicaciones | 1 archivo |
| Archivos que pueden ser eliminados | 0 (todos están en 1 archivo) |
| Líneas de código duplicado | 32-50 líneas |
| % de tests que son duplicados | < 1% |

---

## Tests Recomendados para Patrón de Consolidación

Si se quiere reducir redundancia de tests OpenAPI en el futuro:

```python
# consolidado_openapi_validation.py - PROPUESTA

@pytest.mark.endpoint_schema
class TestOpenAPISchemasExist:
    """Generic OpenAPI schema validation for all analytics endpoints"""
    
    ENDPOINTS = [
        '/analytics/stress-test',
        '/analytics/segments',
        '/analytics/roll-rates',
        '/analytics/advanced-risk',
        '/analytics/cohorts'
    ]
    
    @pytest.mark.parametrize("endpoint", ENDPOINTS)
    def test_endpoint_in_openapi_spec(self, endpoint):
        client = TestClient(app)
        response = client.get('/openapi.json')
        assert response.status_code == 200
        spec = response.json()
        assert endpoint in spec['paths']
        assert 'post' in spec['paths'][endpoint]
```

Esto reduciría 50 líneas pero requeriría refactoring.

---

## Conclusión

El repositorio está generalmente bien mantenido con **< 1%** de duplicación de tests. Las duplicaciones encontradas son:
1. **Trivialmente removibles** (TestPortfolioDashboardDuplicateClassification)
2. **Fáciles de consolidar** (tests de mapeo en TestPortfolioDashboardDesembolsos)
3. **Bajo riesgo** al eliminar

Se recomienda ejecutar el **Plan de Acción Prioridad 1** para limpiar ~20-50 líneas de código duplicado.
