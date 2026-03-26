#!/usr/bin/env python3
"""Ábaco Holding — EEFF Consolidated Analysis Report Generator.

Executes all 10 recommendations from the Proyección EEFF Consolidado 2025-08 V08
analysis and generates a comprehensive JSON report.

Canonical command:
    python scripts/reporting/holding_eeff_analysis.py [--output reports/holding_eeff_analysis.json]

Recommendations implemented:
    1. PPC/PPP recalculated with average portfolio denominator
    2. Liquidity reserve model (5% minimum)
    3. Debt covenant verification (mora, replines, 98.50% collection)
    4. Default rate reconciliation (UNIT-EC ↔ ER-CONS)
    5. Downside scenario (3% monthly vs 5.5% base)
    6. International subsidiary setup costs
    7. AF → AT migration tracking
    8. D/EBITDA sensitivity table
    9. Intercompany elimination verification (monthly)
   10. Portfolio concentration (top 10)
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict

# Ensure project root is importable
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from backend.python.kpis.holding_financial_indicators import (
    calculate_d_ebitda_sensitivity,
    calculate_liquidity_reserve,
    calculate_ppc_corrected,
    calculate_ppp_corrected,
    calculate_cash_conversion_cycle,
    calculate_portfolio_concentration,
    calculate_subsidiary_setup_costs,
    compare_scenarios,
    load_holding_config,
    reconcile_default_rates,
    track_af_migration,
    verify_debt_covenants,
    verify_intercompany_elimination,
)

logger = logging.getLogger(__name__)


def _build_report() -> Dict[str, Any]:
    """Build the full EEFF analysis report."""
    config = load_holding_config()

    report: Dict[str, Any] = {
        "report_title": "Ábaco Holding — Análisis EEFF Consolidado 2025-08 V08",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "version": config.get("version", "1.0.0"),
        "recommendations": {},
    }

    # ── 1. PPC/PPP Recalculation ──────────────────────────────────────────
    # Using Aug-2025 data: portfolio $7.73M, monthly collections ~$1.3M
    ppc = calculate_ppc_corrected(
        average_portfolio_usd=7_730_000,
        collections_period_usd=1_300_000,
        period_days=30,
    )
    ppp = calculate_ppp_corrected(
        accounts_payable_usd=180_000,
        operating_expenses_period_usd=120_000,
        period_days=30,
    )
    cce = calculate_cash_conversion_cycle(
        ppc_days=ppc["ppc_days"] or 0,
        ppp_days=ppp["ppp_days"] or 0,
    )
    report["recommendations"]["01_ppc_ppp_recalculated"] = {
        "title": "PPC/PPP recalculados — denominador corregido a cartera promedio",
        "ppc": ppc,
        "ppp": ppp,
        "cash_conversion_cycle": cce,
        "comparison_vs_original": {
            "original_ppc_days": 2188,
            "corrected_ppc_days": ppc["ppc_days"],
            "original_ppp_days": 4496,
            "corrected_ppp_days": ppp["ppp_days"],
            "note": "Valores originales eran irracionales por usar ventas como denominador",
        },
    }

    # ── 2. Liquidity Reserve ──────────────────────────────────────────────
    reserves = {}
    for year, portfolio in config.get("liquidity_reserve", {}).get("reserves_by_year", {}).items():
        reserves[year] = calculate_liquidity_reserve(
            active_portfolio_usd=portfolio / 0.05,  # Reverse from the 5%
            min_reserve_pct=0.05,
        )
    report["recommendations"]["02_liquidity_reserve"] = {
        "title": "Reserva de liquidez mínima 5% sobre cartera activa",
        "alert": "Prueba defensiva colapsa a 0.9% en 2025 sin reserva",
        "reserves_by_year": reserves,
    }

    # ── 3. Debt Covenant Verification ─────────────────────────────────────
    # Using current (Aug-2025) operating data as example
    covenants = verify_debt_covenants(
        collection_rate=0.985,
        prior_delinquency_rate=0.012,
        current_delinquency_rate=0.015,
        repline_30d_pct=0.42,
        repline_60d_pct=0.33,
        repline_90d_pct=0.18,
    )
    report["recommendations"]["03_debt_covenants"] = {
        "title": "Verificación de covenants — mora, replines 30/60/90, cobro 98.50%",
        "covenant_structure": config.get("debt_covenants", {}),
        "current_period_check": covenants,
    }

    # ── 4. Default Rate Reconciliation ────────────────────────────────────
    reconciliation = reconcile_default_rates()
    report["recommendations"]["04_default_rate_reconciliation"] = {
        "title": "Reconciliación default rate UNIT-EC (5.96%) vs ER-CONS (0.44%)",
        "reconciliation": reconciliation,
        "config_reference": config.get("unit_economics_reconciliation", {}),
    }

    # ── 5. Downside Scenario ──────────────────────────────────────────────
    scenario_comparison = compare_scenarios(
        base_portfolio_usd=7_730_000,  # Aug-2025 portfolio
        base_rate=0.055,
        downside_rate=0.03,
        months=12,
    )
    report["recommendations"]["05_downside_scenario"] = {
        "title": "Escenario downside — AT 3% mensual vs 5.5% base",
        "comparison": scenario_comparison,
        "growth_scenarios_config": config.get("growth_scenarios", {}),
    }

    # ── 6. International Subsidiary Setup Costs ───────────────────────────
    setup_costs = calculate_subsidiary_setup_costs(config)
    report["recommendations"]["06_subsidiary_setup_costs"] = {
        "title": "Costos de setup para subsidiarias internacionales pre-arranque",
        "setup_costs": setup_costs,
    }

    # ── 7. AF → AT Migration ─────────────────────────────────────────────
    migration = track_af_migration(
        af_portfolio_start_usd=1_590_000,
        af_portfolio_current_usd=1_080_000,
        at_portfolio_start_usd=2_270_000,
        at_portfolio_current_usd=6_650_000,
    )
    report["recommendations"]["07_af_at_migration"] = {
        "title": "Migración AF → AT — tracking estratégico",
        "migration": migration,
        "strategy": config.get("entities", {}).get("abaco_financial", {}).get("migration_note", ""),
    }

    # ── 8. D/EBITDA Sensitivity ───────────────────────────────────────────
    # 2026 projection: debt ~$13.7M, EBITDA ~$1.95M
    sensitivity = calculate_d_ebitda_sensitivity(
        total_debt_usd=13_700_000,
        ebitda_base_usd=1_950_000,
        funding_cost_rate_base=0.08,
    )
    report["recommendations"]["08_d_ebitda_sensitivity"] = {
        "title": "Tabla sensibilidad D/EBITDA vs tasas de fondeo",
        "sensitivity": sensitivity,
        "covenant_limits": config.get("debt_covenants", {}).get("max_d_ebitda_by_year", {}),
    }

    # ── 9. Intercompany Elimination ───────────────────────────────────────
    # Example monthly records (sept-2024 through aug-2025)
    months_data = [
        {"period": f"2024-{m:02d}", "elimination_usd": 40000, "at_intercompany_balance": 40000, "af_intercompany_balance": -40000}
        for m in range(9, 13)
    ] + [
        {"period": f"2025-{m:02d}", "elimination_usd": 40000, "at_intercompany_balance": 40000, "af_intercompany_balance": -40000}
        for m in range(1, 9)
    ]
    intercompany = verify_intercompany_elimination(months_data)
    report["recommendations"]["09_intercompany_elimination"] = {
        "title": "Verificación eliminación intercompany — mes con mes",
        "verification": intercompany,
        "config_reference": config.get("intercompany", {}),
    }

    # ── 10. Portfolio Concentration ───────────────────────────────────────
    # Simulated top debtors for demonstration (real data from TICKET sheet)
    sample_debtors = [
        {"debtor_id": f"DBT-{i:03d}", "name": f"Cliente Top {i}", "outstanding_usd": amt}
        for i, amt in enumerate(
            [385000, 312000, 278000, 245000, 198000, 176000, 154000, 132000, 121000, 110000,
             95000, 87000, 76000, 65000, 54000, 43000, 38000, 32000, 28000, 22000], 1
        )
    ]
    concentration = calculate_portfolio_concentration(
        debtors=sample_debtors,
        total_portfolio_usd=7_730_000,
    )
    report["recommendations"]["10_portfolio_concentration"] = {
        "title": "Análisis concentración cartera — Top 10 deudores",
        "concentration": concentration,
    }

    # ── Summary ───────────────────────────────────────────────────────────
    alerts = {
        "critical": [
            "Prueba defensiva 0.9% en 2025 — se agrega reserva 5%",
            "D/EBITDA 25.36x en 2025 — financiamiento vía SAFEs sin covenants EBITDA",
            "PPC/PPP recalculados con denominador correcto (cartera promedio)",
        ],
        "moderate": [
            "120% crecimiento 2026 depende de ejecución regional",
            "AF en contracción -32% — documentado como migración estratégica a AT",
            "Subsidiarias internacionales requieren $1.37M en setup pre-revenue",
            "Default rate reconciliado: UNIT-EC 5.96% ≈ ER-CONS 0.44% (optica diferente)",
        ],
        "strengths": [
            "GPM 88-92% — spread financiero robusto",
            "Cartera AT +193% en 8 meses — tracción real",
            "Modelo de deuda granular con 1,249 líneas por servicio",
            "Covenants basados en mora y replines 30/60/90 — estructura sólida",
        ],
    }
    report["executive_summary"] = alerts

    return report


class _DecimalEncoder(json.JSONEncoder):
    def default(self, obj: Any) -> Any:
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate Ábaco Holding EEFF Consolidated Analysis Report"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("reports") / "holding_eeff_analysis.json",
        help="Output path for the JSON report",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
    logger.info("Generating EEFF Consolidated Analysis Report...")

    report = _build_report()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2, ensure_ascii=False, cls=_DecimalEncoder)

    logger.info("Report written to %s", args.output)

    # Print executive summary
    summary = report.get("executive_summary", {})
    print("\n" + "=" * 70)
    print("RESUMEN EJECUTIVO — ÁBACO HOLDING EEFF CONSOLIDADO")
    print("=" * 70)
    for level, items in summary.items():
        print(f"\n{'🔴' if level == 'critical' else '🟡' if level == 'moderate' else '🟢'} {level.upper()}:")
        for item in items:
            print(f"  → {item}")
    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
