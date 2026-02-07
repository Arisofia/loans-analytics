# ============================================

# 🚀 GUÍA RÁPIDA: PROMETHEUS + GRAFANA

# ============================================

## ✅ COMPLETADO: Supabase Metrics API

- Estado: ✅ Funcionando (520 métricas disponibles)
- Endpoint: https://goxdevkqozomyhsyxhte.supabase.co/customer/v1/privileged/metrics
- Autenticación: Basic Auth (service_role:SECRET_API_KEY)
- Test: `bash scripts/test_metrics_api.sh` → HTTP 200 ✅

## 📋 OPCIÓN 1: Grafana Cloud (Recomendado - 5 minutos)

### 1. Crear cuenta Grafana Cloud (FREE)

```bash
# Visita: https://grafana.com/auth/sign-up/create-user
# Free tier incluye:
# - 10,000 métricas
# - 14 días de retención
# - 50GB logs/mes
# - Alertas ilimitadas
```

### 2. Configurar Prometheus Agent

Grafana Cloud te dará un script de configuración automática. Alternativamente:

```yaml
# Añade este remote_write a tu prometheus.yml local:
remote_write:
  - url: https://prometheus-prod-XX-prod-XX-XX.grafana.net/api/prom/push
    basic_auth:
      username: 123456 # Tu Grafana Cloud instance ID
      password: glc_... # Tu API key de Grafana Cloud
```

### 3. Importar Dashboard de Supabase

```bash
# En Grafana Cloud UI:
# 1. Dashboards → Import
# 2. Usa dashboard ID: 19822 (Supabase Overview)
# 3. O importa desde: https://github.com/supabase/supabase-grafana
```

### 4. Configurar Alertas

```bash
# En Grafana Cloud:
# Alerting → Alert rules → Import from file
# Sube: config/rules/supabase_alerts.yml
```

## 📋 OPCIÓN 2: Self-Hosted Prometheus + Grafana (Docker)

### 1. Crear `docker-compose.monitoring.yml`

```yaml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus
    ports:
      - '9090:9090'
    volumes:
      - ./config/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - ./config/rules:/etc/prometheus/rules:ro
      - prometheus-data:/prometheus
    environment:
      - SUPABASE_PROJECT_REF=goxdevkqozomyhsyxhte
      - SUPABASE_SECRET_API_KEY=${SUPABASE_SECRET_API_KEY}
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--storage.tsdb.retention.time=30d'
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    container_name: grafana
    ports:
      - '3001:3000' # Puerto 3001 para no conflicto con Next.js
    volumes:
      - grafana-data:/var/lib/grafana
      - ./grafana/provisioning:/etc/grafana/provisioning:ro
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_ADMIN_PASSWORD:-admin123}
      - GF_SERVER_ROOT_URL=http://localhost:3001
    depends_on:
      - prometheus
    restart: unless-stopped

  alertmanager:
    image: prom/alertmanager:latest
    container_name: alertmanager
    ports:
      - '9093:9093'
    volumes:
      - ./config/alertmanager.yml:/etc/alertmanager/alertmanager.yml:ro
    restart: unless-stopped

volumes:
  prometheus-data:
  grafana-data:
```

### 2. Iniciar stack

```bash
# Cargar variables de entorno
source scripts/load_env.sh

# Exportar para docker-compose
export SUPABASE_SECRET_API_KEY
export GRAFANA_ADMIN_PASSWORD="tu_password_seguro"

# Iniciar servicios
docker-compose -f docker-compose.monitoring.yml up -d

# Ver logs
docker-compose -f docker-compose.monitoring.yml logs -f
```

### 3. Acceder a UIs

```bash
# Prometheus: http://localhost:9090
# - Targets status: http://localhost:9090/targets
# - Query explorer: http://localhost:9090/graph

# Grafana: http://localhost:3001
# - Usuario: admin
# - Password: (el que configuraste en GRAFANA_ADMIN_PASSWORD)
```

### 4. Configurar Datasource en Grafana

```bash
# En Grafana UI:
# Configuration → Data sources → Add data source → Prometheus
# URL: http://prometheus:9090
# Access: Server (default)
# Save & test
```

### 5. Importar Dashboards

```bash
# Dashboard oficial de Supabase:
# - ID: 19822 (Supabase Overview)
# - O desde: https://grafana.com/grafana/dashboards/19822

# Dashboard personalizado para Abaco:
# - Importa: grafana/dashboards/abaco-overview.json (crear este archivo)
```

## 📊 MÉTRICAS CLAVE PARA MONITOREAR

### Base de Datos (Supabase)

```promql
# Conexiones activas
pgbouncer_stats_server_active_connections

# CPU usage
node_cpu_seconds_total

# Memoria disponible
node_memory_MemAvailable_bytes

# Disco I/O
rate(node_disk_io_time_seconds_total[5m])

# Query duration (percentil 95)
histogram_quantile(0.95, rate(pg_stat_statements_total_exec_time_bucket[5m]))
```

### Pipeline (cuando implementes metrics_exporter.py)

```promql
# Runs exitosos vs fallidos
rate(pipeline_runs_total{status="success"}[5m])
rate(pipeline_runs_total{status="error"}[5m])

# Duración promedio
avg(pipeline_duration_seconds)

# KPIs calculados
rate(kpi_calculations_total{status="success"}[5m])

# Pool de conexiones
connection_pool_size{state="active"}
```

## 🔔 ALERTAS CRÍTICAS YA CONFIGURADAS

Ver archivos:

- `config/rules/supabase_alerts.yml` (15 reglas)
- `config/rules/pipeline_alerts.yml` (12 reglas)

Ejemplos de alertas:

- **Crítico**: CPU > 80%, Conexiones > 90%, Disco > 90%
- **Advertencia**: Cache hit rate < 95%, Queries lentas
- **Info**: Crecimiento de datos, cambios en tráfico

## 🔒 SEGURIDAD

### Variables de Entorno Requeridas

```bash
# Ya configuradas en .env.local:
SUPABASE_PROJECT_REF=goxdevkqozomyhsyxhte
SUPABASE_SECRET_API_KEY=<your-supabase-secret-api-key>

# Adicionales para Grafana:
GRAFANA_ADMIN_PASSWORD=tu_password_seguro_aqui
```

### ⚠️ NUNCA HAGAS ESTO:

- ❌ Expongas SUPABASE*SECRET_API_KEY en frontend (NEXT_PUBLIC*\*)
- ❌ Commites credenciales a Git
- ❌ Uses secret keys en URLs de navegador
- ❌ Compartas dashboards públicos con métricas sensibles

### ✅ BUENAS PRÁCTICAS:

- ✅ Usa variables de entorno para todas las credenciales
- ✅ Rota SECRET_API_KEY cada 90 días
- ✅ Limita acceso a Grafana con autenticación
- ✅ Usa HTTPS para todas las conexiones
- ✅ Configura IP allowlist si es posible

## 🎯 PRÓXIMOS PASOS

1. **Elegir opción de deployment** (Grafana Cloud o Self-hosted)
2. **Configurar alertas** en Slack/PagerDuty/Email
3. **Implementar metrics_exporter.py** para métricas del pipeline
4. **Crear dashboards personalizados** para KPIs de negocio
5. **Configurar retención de datos** según necesidades (30d recomendado)

## 📚 RECURSOS

- Grafana Cloud Free: https://grafana.com/auth/sign-up/create-user
- Supabase Dashboard (ID 19822): https://grafana.com/grafana/dashboards/19822
- Prometheus Docs: https://prometheus.io/docs/
- PromQL Query Examples: https://prometheus.io/docs/prometheus/latest/querying/examples/

## ❓ TROUBLESHOOTING

```bash
# Ver targets en Prometheus
curl http://localhost:9090/api/v1/targets | jq

# Probar query desde CLI
curl -G http://localhost:9090/api/v1/query --data-urlencode 'query=up'

# Ver logs de Prometheus
docker logs prometheus -f

# Verificar conectividad a Supabase
bash scripts/test_metrics_api.sh
```
