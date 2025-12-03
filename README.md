# ABACO — Loan Analytics Platform

## Arquitectura

- **apps/web**: Next.js dashboard corporativo.
- **apps/analytics**: pipelines de Python para riesgo, scoring y KPIs.
- **infra/azure**: scripts de despliegue Azure.
- **data_samples**: datasets anonimizados para desarrollo.
## Integraciones disponibles

- Azure SQL / Cosmos / Storage
- Supabase
- Vercel
- OpenAI / Gemini / Claude
- SonarCloud
- GitHub Actions
Consulta `docs/integration-readiness.md` para verificar el estado de cada integración y las comprobaciones previas que
debes ejecutar antes de usarlas.

## KPI catalog and runbooks

Consulta `docs/analytics/KPIs.md` para la taxonomía de KPIs, propietarios, orígenes de datos, umbrales y enlaces a dashboards, tablas de drill-down y runbooks (`docs/analytics/runbooks`). Usa `docs/analytics/dashboards.md` para la guía de visualizaciones y alertas.

## ContosoTeamStats

Este repositorio contiene ContosoTeamStats, una API Web de .NET 6 para gestionar equipos deportivos que incluye Docker,
scripts de despliegue en Azure, integraciones con SendGrid/Twilio y migraciones de SQL Server. Sigue
`docs/ContosoTeamStats-setup.md` para la configuración local, secretos, aprovisionamiento de base de datos y validación
de contenedores.

Consulta `docs/Analytics-Vision.md` para la visión analítica, el plano de Streamlit y la narrativa preparada para
agentes que mantiene cada KPI, escenario y prompt de IA alineados con nuestra entrega de nivel fintech.

Para gobernanza, trazabilidad y flujos de revisión GitHub-first en KPIs y dashboards, sigue
`docs/analytics/governance.md`.

## Catálogo de KPIs y runbooks

Consulta `docs/analytics/KPIs.md` para la taxonomía de KPIs, propietarios, orígenes de datos, umbrales y enlaces a
dashboards, tablas de drill-down y runbooks (`docs/analytics/runbooks`). Usa `docs/analytics/dashboards.md` como guía de
visualizaciones y alertas.

### Variables de entorno (alertas y drill-down)

- `NEXT_PUBLIC_ALERT_SLACK_WEBHOOK`: webhook de Slack para alertas (red/amber).
- `NEXT_PUBLIC_ALERT_EMAIL`: correo de alertas si Slack no está disponible.
- `NEXT_PUBLIC_DRILLDOWN_BASE_URL`: base URL para tablas de drill-down (cola de cobranzas, cohortes de mora, errores de ingesta).
Configura estas variables en tu despliegue (Vercel/Azure) y en `.env.local` durante desarrollo.

## Copilot Enterprise workflow

Usa `docs/Copilot-Team-Workflow.md` cuando invites a tu equipo a Copilot, documentes los flujos de validación y
seguridad, y mantengas alineada la checklist de Azure, GitHub Actions y KPIs durante tu prueba de 30 días de Enterprise
(App Service F1, ACR Basic y tiers de seguridad gratuitos de Azure). El documento incluye prompts reutilizables cuando
Copilot guíe los cambios.

Validation signal: refreshed on the validation/contoso-team-stats branch to trigger CI verification for the current release cycle.

## Fitten Code AI 编程助手

Para integrar Fitten Code AI en este monorepo (local y GitHub), consulta `docs/Fitten-Code-AI-Manual.md`, que cubre la
introducción al producto, instalación, integración, preguntas frecuentes y pruebas de inferencia local.

## MCP configuration

Usa `docs/MCP_CONFIGURATION.md` para agregar servidores MCP mediante la CLI de Codex o editando `config.toml`, con
ejemplos para Context7, Figma, Chrome DevTools y cómo ejecutar Codex como servidor MCP.

## Deno helper

The repository exposes a tiny Deno helper at `main.ts` that verifies the expected directories before you execute
tooling such as Fitten or analytics scripts. Run it with:

```sh
deno run --allow-all main.ts
```

`--unstable` ya no es necesario en Deno 2.0; solo incluye los flags `--unstable-*` cuando dependas de APIs inestables.

## VS Code Python terminals

If you rely on `.env` files while running the Python analytics scripts, enable the VS Code setting
`python.terminal.useEnvFile` so integrated terminals automatically load those variables. Add this to your user
`settings.json` via the Command Palette to avoid missing secrets during local runs.

## Troubleshooting VS Code Zencoder extension

Si observas `Failed to spawn Zencoder process: ... zencoder-cli ENOENT` en VS Code, sigue la checklist de remediación en
`docs/Zencoder-Troubleshooting.md` para reinstalar la extensión y restaurar el binario faltante.

## Java & Gradle

The Gradle build is configured for JDK **21** via the toolchain in `build.gradle`. Running Gradle with newer
early-access JDKs (e.g., JDK 25) is not supported by the current Gradle wrapper (8.10) and will fail during project
sync. If your IDE selects a newer JDK by default, switch the Gradle JVM to JDK 21 (or another supported LTS version)
and ensure your `JAVA_HOME` points to that installation. In IntelliJ IDEA, go to **Settings > Build, Execution,
Deployment > Build Tools > Gradle** and set **Gradle JVM** to JDK 21 to avoid the sync error. You can verify the
wrapper is using JDK 21 by running `./gradlew --version` and checking the `JVM` line.
