"""Phase 5 — Decision Intelligence.

Bridges the existing 4-phase pipeline with the new decision agent
architecture.  Builds marts → features → metrics → scenarios → runs
all agents → produces ``DecisionCenterState``.

This phase is *non-blocking* — if it fails, the pipeline still
succeeds (Phases 1-4 already completed).
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict

import pandas as pd

logger = logging.getLogger(__name__)


class DecisionPhase:
    """Pipeline phase 5 — Decision Intelligence."""

    def execute(
        self,
        phase2_results: Dict[str, Any],
        phase3_results: Dict[str, Any],
        business_rules: Dict[str, Any],
        run_dir: Path,
    ) -> Dict[str, Any]:
        """Run the full decision intelligence stack.

        Parameters
        ----------
        phase2_results : output from transformation phase (contains output_path)
        phase3_results : output from calculation phase (contains KPIs)
        business_rules : loaded business_parameters.yml
        run_dir : directory for this pipeline run
        """
        try:
            # ── Load canonical DataFrame from Phase 2 ───────────────────
            clean_path = phase2_results.get("output_path")
            if not clean_path:
                return {"status": "skipped", "reason": "No clean data path from transformation phase."}

            clean = Path(clean_path)
            if not clean.exists():
                df = pd.DataFrame()
            elif clean.suffix == ".parquet":
                df = pd.read_parquet(clean)
            else:
                df = pd.read_csv(clean, encoding="utf-8", encoding_errors="replace")
            if df.empty:
                return {"status": "skipped", "reason": "Clean data is empty."}

            # ── Build marts (individual modules) ────────────────────────
            from backend.src.marts.build_all_marts import build_all_marts

            marts = build_all_marts({"df": df})
            logger.info("Built %d marts from %d rows", len(marts), len(df))

            # ── Data quality gate ───────────────────────────────────────
            from backend.src.data_quality.engine import run_quality_engine

            dq_results = run_quality_engine(df)
            blocking = any(
                getattr(r, "severity", None) == "blocking"
                or (hasattr(r, "severity") and str(r.severity).lower() == "blocking")
                for r in dq_results
            )
            logger.info(
                "Data quality: %d rules evaluated, blocking=%s",
                len(dq_results),
                blocking,
            )
            if blocking:
                return {
                    "status": "blocked",
                    "reason": "Data quality blocking rules failed",
                    "dq_result": [str(r) for r in dq_results],
                }

            # ── Build features ──────────────────────────────────────────
            from backend.python.multi_agent.feature_store.builder import build_feature_store

            features = build_feature_store(marts, phase3_results.get("kpis", {}))
            logger.info("Built features: %s", list(features.keys()))

            # ── Seed metrics from Phase 3 KPIs ──────────────────────────
            metrics_seed: Dict[str, Any] = {}
            kpis = phase3_results.get("kpis", {})
            if isinstance(kpis, dict):
                metrics_seed.update(kpis)

            # Also flatten any nested KPI structures
            for key in ("expected_loss", "roll_rates", "vintage_analysis", "concentration_hhi"):
                val = phase3_results.get(key)
                if isinstance(val, dict):
                    metrics_seed.update(val)

            # ── Run unified metric engine ───────────────────────────────
            from backend.src.kpi_engine.engine import run_metric_engine

            equity = business_rules.get("target_equity_ratio", 0.08)
            lgd = business_rules.get("lgd", 0.10)
            min_coll = business_rules.get("min_collection_rate", 0.985)
            engine_metrics = run_metric_engine(
                marts, equity=equity, lgd=lgd, min_collection_rate=min_coll,
            )
            metrics_seed.update(engine_metrics)
            logger.info("Metric engine produced %d metrics", len(engine_metrics))

            # ── Run scenario engine ─────────────────────────────────────
            from backend.src.scenario_engine.engine import ScenarioEngine

            scenario_engine = ScenarioEngine()
            scenario_results = scenario_engine.run_all(metrics_seed)
            scenarios_dicts = [sr.to_dict() for sr in scenario_results]
            logger.info("Projected %d scenarios", len(scenarios_dicts))

            # ── Run decision orchestrator (subpackage) ──────────────────
            from backend.python.multi_agent.orchestrator import DecisionOrchestrator

            orchestrator = DecisionOrchestrator()
            decision_state = orchestrator.run(
                marts=marts,
                metrics_seed=metrics_seed,
                features=features,
                scenarios=scenarios_dicts,
                business_params=business_rules,
            )

            # ── Persist decision state ──────────────────────────────────
            decision_dir = run_dir / "decision"
            decision_dir.mkdir(parents=True, exist_ok=True)

            state_path = decision_dir / "decision_center_state.json"
            with open(state_path, "w", encoding="utf-8") as fh:
                json.dump(decision_state.model_dump(), fh, indent=2, default=str)

            scenarios_path = decision_dir / "scenarios.json"
            with open(scenarios_path, "w", encoding="utf-8") as fh:
                json.dump(scenarios_dicts, fh, indent=2, default=str)

            dq_path = decision_dir / "data_quality.json"
            with open(dq_path, "w", encoding="utf-8") as fh:
                json.dump(dq_results, fh, indent=2, default=str)

            logger.info(
                "Decision phase complete — state=%s, alerts=%d, actions=%d",
                decision_state.business_state,
                len(decision_state.critical_alerts),
                len(decision_state.ranked_actions),
            )

            return {
                "status": "success",
                "business_state": decision_state.business_state,
                "critical_alerts_count": len(decision_state.critical_alerts),
                "ranked_actions_count": len(decision_state.ranked_actions),
                "opportunities_count": len(decision_state.opportunities),
                "agent_statuses": decision_state.agent_statuses,
                "decision_state_path": str(state_path),
                "scenarios_path": str(scenarios_path),
            }

        except Exception as exc:
            logger.error("Decision phase failed (non-blocking): %s", exc, exc_info=True)
            return {
                "status": "error",
                "error": str(exc),
            }
