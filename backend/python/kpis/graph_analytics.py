"""
Graph Analytics & Advanced Fintech KPIs
========================================

Implements the graph strategy from the 2026 fintech thesis:

Section 3.1 — Graph Strategy Vectors
    build_transaction_graph()     Bipartite client↔emisor graph from INTERMEDIA
    pagerank_scores()             Financial PageRank: SME creditworthiness by debtor quality
    detect_communities()          Louvain community detection (fraud rings + clusters)
    detect_fraud_rings()          Flag communities with anomalous DPD or shared attributes

Section 4.1 — Unit Economics: CAC & LTV
    calc_unit_economics()         CAC, LTV, LTV:CAC ratio vs fintech B2B benchmarks
    viral_k_factor()              Viral coefficient K from referral / sales_channel data

Section 4.2 — Risk Metrics
    concentration_hhi()           HHI index at portfolio and emisor level
    npl_benchmarks()              NPL vs LatAm/OCDE benchmarks with loss-rate projection

Data sources used
-----------------
- INTERMEDIA snapshot  : CodCliente, Emisor, TotalSaldoVigente (active ops)
- Loan tape            : customer_id, pagador, tpv, sales_agent, sales_channel
- payments             : true_total_payment (for LTV)

Usage
-----
    from backend.python.kpis.graph_analytics import (
        build_transaction_graph,
        pagerank_scores,
        detect_communities,
        detect_fraud_rings,
        calc_unit_economics,
        viral_k_factor,
        concentration_hhi,
        build_graph_kpi_report,
    )

    graph   = build_transaction_graph(intermedia_df)
    pr      = pagerank_scores(graph)
    comms   = detect_communities(graph)
    rings   = detect_fraud_rings(graph, intermedia_df)
    ue      = calc_unit_economics(loans_df, payments_df)
    k       = viral_k_factor(loans_df)
    hhi     = concentration_hhi(intermedia_df)
    report  = build_graph_kpi_report(intermedia_df, loans_df, payments_df)
"""

from __future__ import annotations

import importlib
import logging
import warnings
from datetime import datetime, timezone
from typing import Any, cast

import numpy as np
import pandas as pd

from backend.python.kpis.ssot_asset_quality import calculate_asset_quality_metrics

logger = logging.getLogger(__name__)

# ── Optional heavy dependencies — degrade gracefully ─────────────────────────
try:
    nx = importlib.import_module("networkx")
    _NX = True
except ImportError:  # pragma: no cover
    nx = cast(Any, None)
    _NX = False
    logger.warning(
        "networkx not installed — graph modules will return empty results. "
        "Install with: pip install networkx"
    )

try:
    _community = importlib.import_module("community")
    _louvain_partition = getattr(_community, "best_partition")
    _LOUVAIN = True
except ImportError:
    _louvain_partition = cast(Any, None)
    _LOUVAIN = False  # fall back to greedy modularity in networkx


# ─────────────────────────────────────────────────────────────────────────────
# Shared helpers
# ─────────────────────────────────────────────────────────────────────────────


def _col(df: pd.DataFrame, candidates: list[str]) -> str | None:
    for c in candidates:
        if c in df.columns:
            return c
    return None


def _num(df: pd.DataFrame, col: str) -> pd.Series:
    return pd.to_numeric(df[col], errors="coerce").fillna(0.0)


def _calculate_ssot_npl_metrics(balance: pd.Series, dpd: pd.Series) -> tuple[float, float]:
    """Compute NPL-90 and NPL-180 percentages through SSOT formula execution."""
    values = calculate_asset_quality_metrics(
        balance,
        dpd,
        actor="graph_analytics",
        metric_aliases=("npl90", "npl180"),
    )
    npl_90 = values.get("npl90", 0.0)
    npl_180 = values.get("npl180", 0.0)
    return npl_90, npl_180


# ─────────────────────────────────────────────────────────────────────────────
# Module-level helpers (extracted for readability and SonarQube compliance)
# ─────────────────────────────────────────────────────────────────────────────


def _assign_client_tier(score: float, high_thresh: float, low_thresh: float) -> str:
    """Assign trust tier based on PageRank percentile thresholds."""
    if score >= high_thresh:
        return "HIGH_TRUST"
    if score <= low_thresh:
        return "LOW_TRUST"
    return "STANDARD"


def _concentration_level(hhi_val: float) -> str:
    """Classify HHI value per DOJ concentration thresholds."""
    if hhi_val > 2500:
        return "highly_concentrated"
    if hhi_val > 1500:
        return "moderately_concentrated"
    return "unconcentrated"


def _build_dpd_lookup(
    intermedia_df: pd.DataFrame,
) -> tuple[dict[str, float], dict[str, float]]:
    """Build per-client DPD and balance lookup dicts from an INTERMEDIA snapshot."""
    cod_col = _col(intermedia_df, ["CodCliente", "customer_id"])
    bal_col = _col(intermedia_df, ["TotalSaldoVigente"])
    dpd_col = _col(intermedia_df, ["dpd", "dias_mora", "DPD"])

    if not (cod_col and bal_col):
        return {}, {}

    df = intermedia_df.copy()
    df["_bal"] = _num(df, bal_col)
    df["_cod"] = df[cod_col].astype(str).str.strip()

    if dpd_col:
        df["_dpd"] = _num(df, dpd_col)
    else:
        fpp_col = _col(df, ["FechaPagoProgramado", "payment_due_date"])
        if fpp_col:
            df["_due"] = pd.to_datetime(df[fpp_col], errors="coerce")
            cutoff = pd.Timestamp("2026-03-13")
            df["_dpd"] = (cutoff - df["_due"]).dt.days.clip(lower=0).fillna(0)
        else:
            df["_dpd"] = 0.0

    active = df[df["_bal"] > 0]
    return (
        active.groupby("_cod")["_dpd"].mean().to_dict(),
        active.groupby("_cod")["_bal"].sum().to_dict(),
    )


def _compute_hhi(series: pd.Series, df: pd.DataFrame, total: float) -> dict:
    """Compute HHI concentration index for a grouping series."""
    grouped = df.groupby(series)["_bal"].sum()
    shares = grouped / total
    hhi_val = float((shares**2).sum() * 10000)
    top = grouped.sort_values(ascending=False)
    return {
        "hhi": round(hhi_val, 1),
        "equivalent_n": round(1 / (hhi_val / 10000), 1) if hhi_val > 0 else 0,
        "concentration_level": _concentration_level(hhi_val),
        "top1_pct": round(float(top.iloc[0] / total * 100), 1) if len(top) > 0 else 0,
        "top3_pct": round(float(top.head(3).sum() / total * 100), 1),
        "top10_pct": round(float(top.head(10).sum() / total * 100), 1),
        "top1_name": str(top.index[0]) if len(top) > 0 else "",
        "top1_balance_usd": round(float(top.iloc[0]), 2) if len(top) > 0 else 0,
    }


def _estimate_ltv(
    loans_df: pd.DataFrame,
    payments_df: pd.DataFrame,
    cust_col: str,
    disb_col: str,
    pay_date: str | None,
    pay_amt: str | None,
    window_start: Any,
    trailing_months: int,
) -> tuple[float, float]:
    """Estimate LTV and avg lifetime months from payment and loan data."""
    if not (pay_date and pay_amt):
        return 0.0, 0.0
    pay_dates = pd.to_datetime(payments_df[pay_date], errors="coerce")
    recent = payments_df[pay_dates >= window_start]
    total_rev = _num(recent, pay_amt).sum()
    n_clients = int(loans_df[cust_col].nunique())
    monthly_rev = float(total_rev / max(n_clients, 1) / trailing_months)
    avg_lifetime_months = 6.0
    if disb_col and disb_col in loans_df.columns:
        term_col = _col(loans_df, ["term", "Term"])
        if term_col:
            avg_term_days = float(_num(loans_df, term_col).median())
            avg_lifetime_months = avg_term_days / 30 * 3
    return monthly_rev * avg_lifetime_months, avg_lifetime_months


def _k_factor_from_channel(
    loans_df: pd.DataFrame,
    cust_col: str,
    ch_col: str,
    conversion_rate: float | None,
) -> dict:
    """Estimate viral K-factor from sales_channel referral data."""
    channels = loans_df.drop_duplicates(cust_col)[ch_col].astype(str).str.lower()
    organic_keywords = ["referral", "referido", "word", "organic", "viral", "invite"]
    organic_mask = channels.str.contains("|".join(organic_keywords), na=False)
    n_organic = int(organic_mask.sum())
    n_total = len(channels)
    referral_rate = n_organic / max(n_total, 1)
    avg_invitations = 1.0
    conv = referral_rate if referral_rate > 0 else 0.05
    if conversion_rate is not None:
        conv = conversion_rate
    k = avg_invitations * conv
    return {
        "k_factor": round(k, 3),
        "avg_invitations": avg_invitations,
        "conversion_rate": round(conv, 3),
        "organic_clients": n_organic,
        "total_clients": n_total,
        "organic_rate_pct": round(referral_rate * 100, 1),
        "confidence": "medium",
        "data_source": f"sales_channel column ({ch_col})",
        "growth_status": "exponential" if k >= 1.0 else "sub-viral",
        "to_reach_k1": (
            f"Need conversion rate >= {1/avg_invitations:.1%} OR "
            f"avg invites >= {1/max(conv, 0.001):.1f} per client"
        ),
    }


def _score_community(
    comm: dict,
    dpd_by_client: dict[str, float],
    bal_by_client: dict[str, float],
    dpd_threshold: int,
    avg_density: float,
    graph: Any,
) -> dict | None:
    """Score one community for fraud ring flags; return ring dict or None if clean."""
    client_ids = [str(cid) for cid in comm["client_ids"]]
    flags: list[str] = []

    dpds = [dpd_by_client.get(cid, 0.0) for cid in client_ids]
    avg_dpd = float(np.mean(dpds)) if dpds else 0.0
    total_bal = sum(bal_by_client.get(cid, 0.0) for cid in client_ids)

    if avg_dpd > dpd_threshold:
        flags.append("HIGH_DPD_CLUSTER")

    sub_nodes = [f"C:{cid}" for cid in client_ids] + [
        f"D:{did}" for did in comm.get("debtor_ids", [])
    ]
    sub = graph.subgraph([n for n in sub_nodes if n in graph])
    if sub.number_of_nodes() > 1 and nx.density(sub) > 2 * avg_density:
        flags.append("DENSE_CLUSTER")

    if comm["client_count"] >= 4 and comm["debtor_count"] >= 2:
        flags.append("SHARED_DEBTOR_RING")

    if not flags:
        return None

    risk_score = min(100, len(flags) * 30 + int(avg_dpd))
    return {
        "community_id": comm["community_id"],
        "flag_types": flags,
        "size": comm["size"],
        "client_count": comm["client_count"],
        "client_ids": client_ids[:15],
        "avg_dpd": round(avg_dpd, 1),
        "total_balance_usd": round(total_bal, 2),
        "risk_score": risk_score,
    }


def _compute_loan_tape_hhi(loans_df: pd.DataFrame) -> dict | None:
    """Compute debtor-level HHI from the loan tape (pagador column)."""
    pag_col = _col(loans_df, ["pagador", "Pagador", "debtor_id"])
    tpv_col = _col(loans_df, ["tpv", "TPV", "disbursement_amount"])
    if not (pag_col and tpv_col):
        return None
    lt = loans_df.copy()
    lt["_bal"] = _num(lt, tpv_col)
    lt["_pag"] = lt[pag_col].astype(str).str.strip()
    total_lt = lt["_bal"].sum()
    if total_lt <= 0:
        return None
    grouped = lt.groupby("_pag")["_bal"].sum()
    top_lt = grouped.sort_values(ascending=False)
    hhi_lt = float(((grouped / total_lt) ** 2).sum() * 10000)
    return {
        "hhi": round(hhi_lt, 1),
        "top1_name": str(top_lt.index[0]) if len(top_lt) > 0 else "",
        "top1_pct": round(float(top_lt.iloc[0] / total_lt * 100), 1),
        "top10_pct": round(float(top_lt.head(10).sum() / total_lt * 100), 1),
    }


def _k_factor_from_repeat(
    loans_df: pd.DataFrame,
    cust_col: str,
    conversion_rate: float | None,
) -> dict:
    """Estimate viral K-factor via repeat-borrower proxy when referral data is absent."""
    loans_per = loans_df[cust_col].value_counts()
    repeat = int((loans_per > 1).sum())
    total = int(len(loans_per))
    proxy_k = (repeat / max(total, 1)) * 0.3
    conv = conversion_rate if conversion_rate is not None else 0.05
    return {
        "k_factor": round(proxy_k, 3),
        "conversion_rate": conv,
        "repeat_clients": repeat,
        "total_clients": total,
        "confidence": "low",
        "data_source": "repeat_borrower_rate proxy (no referral col)",
        "growth_status": "exponential" if proxy_k >= 1.0 else "sub-viral",
        "note": (
            "Low confidence — add referral/invite tracking to CRM to get accurate K. "
            "Recommended: tag sales_channel='referral' in HubSpot for organic clients."
        ),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Build transaction graph (bipartite: clients ↔ emisores/pagadores)
# ─────────────────────────────────────────────────────────────────────────────


def _build_intermedia_edges(
    graph: Any,
    intermedia_df: pd.DataFrame,
    active_only: bool = True,
) -> None:
    """Extract and add INTERMEDIA client-debtor edges to graph."""
    bal_col = _col(intermedia_df, ["TotalSaldoVigente", "outstanding_balance"])
    cod_col = _col(intermedia_df, ["CodCliente", "customer_id", "cod_cliente"])
    emi_col = _col(intermedia_df, ["Emisor", "emisor", "debtor", "pagador"])

    if not (cod_col and emi_col):
        return

    df = intermedia_df.copy()
    if active_only and bal_col:
        df["_bal"] = _num(df, bal_col)
        df = df[df["_bal"] > 0]

    df["_cod"] = df[cod_col].astype(str).str.strip()
    df["_emi"] = df[emi_col].astype(str).str.strip()
    df["_w"] = _num(df, bal_col) if bal_col else pd.Series(1.0, index=df.index)

    # Add nodes with type attribute
    for cod in df["_cod"].unique():
        graph.add_node(f"C:{cod}", node_type="client", id=cod)
    for emi in df["_emi"].unique():
        graph.add_node(f"D:{emi}", node_type="debtor", id=emi)

    # Add edges, accumulating weight
    for (cod, emi), grp in df.groupby(["_cod", "_emi"]):
        w = float(grp["_w"].sum())
        src, dst = f"C:{cod}", f"D:{emi}"
        if graph.has_edge(src, dst):
            graph[src][dst]["weight"] += w
        else:
            graph.add_edge(src, dst, weight=w)


def _build_loan_edges(
    graph: Any,
    loans_df: pd.DataFrame,
) -> None:
    """Extract and add loan-based client-debtor edges to graph."""
    lc = _col(loans_df, ["customer_id", "Customer ID", "borrower_id"])
    pag = _col(loans_df, ["pagador", "Pagador", "debtor_id", "payer"])
    tpv = _col(loans_df, ["tpv", "TPV", "disbursement_amount"])

    if not (lc and pag):
        return

    lt = loans_df[[lc, pag]].copy()
    lt["_w"] = _num(loans_df, tpv) if tpv else pd.Series(1.0, index=loans_df.index)
    lt["_cod"] = lt[lc].astype(str).str.strip()
    lt["_pag"] = lt[pag].astype(str).str.strip()

    for cod in lt["_cod"].unique():
        if f"C:{cod}" not in graph:
            graph.add_node(f"C:{cod}", node_type="client", id=cod)
    for pag_id in lt["_pag"].unique():
        if f"D:{pag_id}" not in graph:
            graph.add_node(f"D:{pag_id}", node_type="debtor", id=pag_id)

    for (cod, pag_id), grp in lt.groupby(["_cod", "_pag"]):
        w = float(grp["_w"].sum())
        src, dst = f"C:{cod}", f"D:{pag_id}"
        if graph.has_edge(src, dst):
            graph[src][dst]["weight"] += w
        else:
            graph.add_edge(src, dst, weight=w)


def build_transaction_graph(
    intermedia_df: pd.DataFrame,
    loans_df: pd.DataFrame | None = None,
    active_only: bool = True,
) -> Any | None:
    """
    Build a bipartite graph where:
        - Client nodes (prefix 'C:')  = CodCliente / customer_id
        - Debtor nodes (prefix 'D:')  = Emisor / pagador

    Edge weight = sum of TotalSaldoVigente (or TPV from loan tape).

    Two clients sharing a debtor are implicitly connected, enabling:
        - PageRank: debtors with many high-quality clients boost client scores
        - Community detection: clusters of clients serving the same debtors
        - Fraud detection: unusual subgraphs with concentrated DPD

    Returns a NetworkX Graph or None if networkx is unavailable.
    """
    if not _NX:
        return None

    graph = nx.Graph()

    # ── INTERMEDIA edges: CodCliente ↔ Emisor ─────────────────────────
    _build_intermedia_edges(graph, intermedia_df, active_only)

    # ── Loan tape edges: customer_id ↔ pagador ────────────────────────
    if loans_df is not None:
        _build_loan_edges(graph, loans_df)

    logger.info(
        "build_transaction_graph: %d nodes (%d clients, %d debtors), %d edges",
        graph.number_of_nodes(),
        sum(1 for n, d in graph.nodes(data=True) if d.get("node_type") == "client"),
        sum(1 for n, d in graph.nodes(data=True) if d.get("node_type") == "debtor"),
        graph.number_of_edges(),
    )
    return graph


# ─────────────────────────────────────────────────────────────────────────────
# PageRank Financial Score
# ─────────────────────────────────────────────────────────────────────────────


def pagerank_scores(
    graph: Any | None,
    alpha: float = 0.85,
    weight: str = "weight",
) -> dict[str, Any]:
    """
    Financial PageRank: creditworthiness proxy based on network position.

    Logic:
    - A client connected to large, high-quality debtors scores higher.
    - A debtor that many reputable clients invoice scores higher.
    - High PageRank client → bonus in credit scoring (×1.10 per doc).
    - Low PageRank client connected to high-risk community → penalty (×0.50).

    Returns
    -------
    {
        "client_scores":  [{id, pagerank, degree, total_exposure_usd, tier}],
        "debtor_scores":  [{id, pagerank, client_count, total_exposure_usd}],
        "graph_stats":    {nodes, edges, density, avg_clustering},
        "high_trust_threshold": float,  # PageRank cutoff for 10% bonus
        "top_clients":    [{id, pagerank, tier}],
        "top_debtors":    [{id, pagerank}],
    }
    """
    if graph is None or not _NX or graph.number_of_nodes() == 0:
        return {"status": "unavailable", "reason": "networkx not installed or empty graph"}

    pr = nx.pagerank(graph, alpha=alpha, weight=weight)

    # Separate client and debtor scores
    client_rows, debtor_rows = [], []

    for node, score in pr.items():
        ndata = graph.nodes[node]
        ntype = ndata.get("node_type")
        nid = ndata.get("id", node)
        deg = graph.degree(node)
        exp = sum(d.get("weight", 1) for _, _, d in graph.edges(node, data=True))

        if ntype == "client":
            client_rows.append(
                {
                    "id": nid,
                    "pagerank": round(score, 6),
                    "degree": deg,
                    "total_exposure_usd": round(exp, 2),
                }
            )
        elif ntype == "debtor":
            debtor_rows.append(
                {
                    "id": nid,
                    "pagerank": round(score, 6),
                    "client_count": deg,
                    "total_exposure_usd": round(exp, 2),
                }
            )

    # Tier assignment (top 15% = HIGH_TRUST, bottom 20% = LOW_TRUST)
    if client_rows:
        scores = sorted([r["pagerank"] for r in client_rows])
        high_thresh = float(np.percentile(scores, 85))
        low_thresh = float(np.percentile(scores, 20))
        for r in client_rows:
            r["tier"] = _assign_client_tier(r["pagerank"], high_thresh, low_thresh)
    else:
        high_thresh = 0.0

    client_rows.sort(key=lambda x: x["pagerank"], reverse=True)
    debtor_rows.sort(key=lambda x: x["pagerank"], reverse=True)

    return {
        "status": "ok",
        "client_scores": client_rows,
        "debtor_scores": debtor_rows[:50],
        "high_trust_threshold": high_thresh,
        "graph_stats": {
            "nodes": graph.number_of_nodes(),
            "edges": graph.number_of_edges(),
            "density": round(nx.density(graph), 6),
            "avg_degree": round(
                sum(d for _, d in graph.degree()) / max(graph.number_of_nodes(), 1), 2
            ),
        },
        "top_clients": client_rows[:10],
        "top_debtors": debtor_rows[:10],
    }


# ─────────────────────────────────────────────────────────────────────────────
# Community Detection (Louvain / greedy modularity fallback)
# ─────────────────────────────────────────────────────────────────────────────


def detect_communities(
    graph: Any | None,
) -> dict[str, Any]:
    """
    Detect communities in the transaction graph using Louvain algorithm
    (or greedy modularity if python-louvain is not installed).

    Community ID is assigned to each node. Communities with ≥3 clients
    sharing ≥2 debtors are flagged for manual review (potential collusion cluster).

    Returns
    -------
    {
        "status": "ok"|"unavailable",
        "num_communities": int,
        "modularity": float,
        "communities": [{id, size, client_count, debtor_count, nodes}],
        "algorithm": "louvain"|"greedy_modularity",
    }
    """
    if graph is None or not _NX or graph.number_of_nodes() == 0:
        return {"status": "unavailable", "reason": "networkx not installed or empty graph"}

    # Run detection
    if _LOUVAIN:
        partition = _louvain_partition(graph, weight="weight", random_state=42)
        algo = "louvain"
        community_map: dict[int, set] = {}
        for node, comm_id in partition.items():
            community_map.setdefault(comm_id, set()).add(node)
    else:
        # networkx greedy modularity
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            comms_gen = nx.community.greedy_modularity_communities(graph, weight="weight")
        community_map = {i: set(c) for i, c in enumerate(comms_gen)}
        algo = "greedy_modularity"

    # Compute modularity
    try:
        communities_list_sets = list(community_map.values())
        modularity = nx.community.modularity(graph, communities_list_sets, weight="weight")
    except Exception:
        modularity = None

    # Build community summaries
    rows = []
    for comm_id, nodes in community_map.items():
        clients = [n for n in nodes if graph.nodes[n].get("node_type") == "client"]
        debtors = [n for n in nodes if graph.nodes[n].get("node_type") == "debtor"]
        rows.append(
            {
                "community_id": comm_id,
                "size": len(nodes),
                "client_count": len(clients),
                "debtor_count": len(debtors),
                "client_ids": [graph.nodes[n].get("id", n) for n in clients][:20],
                "debtor_ids": [graph.nodes[n].get("id", n) for n in debtors][:10],
                "flag_review": len(clients) >= 3 and len(debtors) >= 2,
            }
        )

    rows.sort(key=lambda x: int(cast(int, x["size"])), reverse=True)

    return {
        "status": "ok",
        "num_communities": len(rows),
        "modularity": round(modularity, 4) if modularity is not None else None,
        "algorithm": algo,
        "communities": rows[:50],
        "flagged_for_review": sum(1 for r in rows if r["flag_review"]),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Fraud Ring Detection
# ─────────────────────────────────────────────────────────────────────────────


def detect_fraud_rings(
    graph: Any | None,
    intermedia_df: pd.DataFrame | None = None,
    dpd_threshold: int = 30,
    min_community_size: int = 3,
) -> dict[str, Any]:
    """
    Identify communities that exhibit concentrated delinquency or unusual
    structural patterns (dense subgraphs with multiple clients sharing debtors).

    Flags:
    1. HIGH_DPD_CLUSTER:   community where avg DPD > dpd_threshold
    2. DENSE_CLUSTER:      community density > 2× network average
    3. SHARED_DEBTOR_RING: ≥4 clients sharing ≥2 debtors

    Returns
    -------
    {
        "status": "ok"|"unavailable",
        "fraud_rings": [{community_id, flag_type, size, client_ids, avg_dpd, risk_score}],
        "total_rings_flagged": int,
        "flagged_balance_usd": float,
    }
    """
    if graph is None or not _NX:
        return {"status": "unavailable", "reason": "networkx not installed"}

    comm_result = detect_communities(graph)
    if comm_result.get("status") != "ok":
        return {"status": "unavailable", "reason": "community detection failed"}

    # Build DPD lookup from INTERMEDIA
    dpd_by_client: dict[str, float] = {}
    bal_by_client: dict[str, float] = {}
    if intermedia_df is not None:
        dpd_by_client, bal_by_client = _build_dpd_lookup(intermedia_df)

    avg_density = nx.density(graph)
    rings: list[dict] = []

    for comm in comm_result["communities"]:
        if comm["size"] < min_community_size:
            continue
        ring = _score_community(
            comm, dpd_by_client, bal_by_client, dpd_threshold, avg_density, graph
        )
        if ring is not None:
            rings.append(ring)

    rings.sort(key=lambda x: x["risk_score"], reverse=True)
    flagged_bal = sum(r["total_balance_usd"] for r in rings)

    return {
        "status": "ok",
        "fraud_rings": rings,
        "total_rings_flagged": len(rings),
        "flagged_balance_usd": round(flagged_bal, 2),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Concentration HHI
# ─────────────────────────────────────────────────────────────────────────────


def concentration_hhi(
    intermedia_df: pd.DataFrame,
    loans_df: pd.DataFrame | None = None,
) -> dict[str, Any]:
    """
    Herfindahl-Hirschman Index for portfolio concentration.

    HHI = Σ(market_share_i²) × 10,000
    Range: 0 (perfect competition) → 10,000 (monopoly)
    DOJ thresholds: <1,500 unconcentrated, 1,500–2,500 moderate, >2,500 highly concentrated.

    Computed at three levels:
    - Debtor (emisor) concentration  — key guardrail
    - Client concentration
    - Industry concentration (if available)
    """
    bal_col = _col(intermedia_df, ["TotalSaldoVigente", "outstanding_balance"])
    emi_col = _col(intermedia_df, ["Emisor", "emisor", "CodEmisor"])
    cod_col = _col(intermedia_df, ["CodCliente", "customer_id"])
    ind_col = _col(intermedia_df, ["industry", "industria"])

    df = intermedia_df.copy()
    if bal_col:
        df["_bal"] = _num(df, bal_col)
        df = df[df["_bal"] > 0]
    else:
        df["_bal"] = 1.0

    total = df["_bal"].sum()
    if total == 0:
        return {"status": "no_data"}

    result: dict[str, Any] = {"status": "ok", "total_aum_usd": round(float(total), 2)}

    if emi_col:
        df["_emi"] = df[emi_col].astype(str).str.strip()
        result["debtor_hhi"] = _compute_hhi(df["_emi"], df, total)

    if cod_col:
        df["_cod"] = df[cod_col].astype(str).str.strip()
        result["client_hhi"] = _compute_hhi(df["_cod"], df, total)

    if ind_col:
        df["_ind"] = df[ind_col].astype(str).str.strip()
        result["industry_hhi"] = _compute_hhi(df["_ind"], df, total)

    # Loan tape debtor (pagador)
    if loans_df is not None:
        lt_hhi = _compute_loan_tape_hhi(loans_df)
        if lt_hhi is not None:
            result["loan_tape_debtor_hhi"] = lt_hhi

    return result


# ─────────────────────────────────────────────────────────────────────────────
# Unit Economics: CAC, LTV, LTV:CAC with Benchmarks
# ─────────────────────────────────────────────────────────────────────────────

# Fintech B2B benchmarks from the strategy document (section 4.1)
_BENCHMARKS = {
    "cac_fintech_b2b_usd": 1450,
    "cac_saas_b2b_usd": 702,
    "cac_target_abaco_usd": 500,
    "ltv_cac_healthy_ratio": 3.0,
    "npl_latam_pct": 4.8,
    "npl_oecd_pct": 2.2,
    "npl_target_abaco_pct": 3.5,
    "loss_rate_abs_pct": 9.9,  # KBRA ABS small business mature vintage
}


def calc_unit_economics(
    loans_df: pd.DataFrame,
    payments_df: pd.DataFrame,
    marketing_spend_usd: float | None = None,
    trailing_months: int = 12,
) -> dict[str, Any]:
    """
    CAC, LTV, LTV:CAC ratio vs fintech B2B benchmarks (section 4.1).

    CAC = total marketing / new clients acquired.
    LTV = (avg monthly revenue per client) × avg client lifetime months.
    LTV:CAC ratio benchmark: ≥3.0x (healthy fintech standard).

    When marketing_spend_usd is None, estimates via disbursement_amount × assumed_cost_rate.
    """
    disb_col = _col(loans_df, ["disbursement_date", "FechaDesembolso"])
    amt_col = _col(loans_df, ["disbursement_amount", "MontoDesembolsado"])
    cust_col = _col(loans_df, ["customer_id", "CodCliente"])
    pay_date = _col(payments_df, ["true_payment_date", "payment_date"])
    pay_amt = _col(payments_df, ["true_total_payment", "payment_amount"])

    if disb_col is None or cust_col is None:
        return {"status": "error", "message": "Missing disbursement_date or customer_id"}

    dates = pd.to_datetime(loans_df[disb_col], errors="coerce")
    cutoff = dates.max()
    window_start = cutoff - pd.DateOffset(months=trailing_months)

    # New clients in window (first-ever operation in window)
    all_first = loans_df.groupby(cust_col).apply(
        lambda g: pd.to_datetime(g[disb_col], errors="coerce").min()
    )
    new_clients = int((all_first >= window_start).sum())

    # Marketing spend estimate
    marketing_val = marketing_spend_usd
    if marketing_val is None:
        if amt_col:
            total_disb = _num(loans_df[dates >= window_start], amt_col).sum()
            marketing_val = float(total_disb * 0.01)  # ~1% cost-of-acquisition proxy
        else:
            marketing_val = 0.0

    cac = marketing_val / max(new_clients, 1)

    # LTV: total payment revenue / total active clients × avg lifetime months
    ltv, avg_lifetime_months = _estimate_ltv(
        loans_df,
        payments_df,
        cust_col,
        disb_col,
        pay_date,
        pay_amt,
        window_start,
        trailing_months,
    )

    ltv_cac = ltv / cac if cac > 0 else 0.0

    # Graph-adjusted CAC (if hub client brings 10 organics, effective CAC ÷10)
    hub_multiplier_assumption = 10  # from strategy doc
    effective_cac_if_hub = cac / hub_multiplier_assumption

    return {
        "status": "ok",
        "trailing_months": trailing_months,
        "new_clients_acquired": new_clients,
        "total_clients": int(loans_df[cust_col].nunique()),
        "marketing_spend_est_usd": round(float(marketing_val), 2),
        "cac_usd": round(float(cac), 2),
        "ltv_usd": round(float(ltv), 2),
        "ltv_cac_ratio": round(float(ltv_cac), 2),
        "avg_lifetime_months": round(float(avg_lifetime_months), 1),
        # Benchmarks
        "benchmarks": _BENCHMARKS,
        "vs_benchmark": {
            "cac_vs_fintech_b2b": round(_BENCHMARKS["cac_fintech_b2b_usd"] / max(cac, 1), 1),
            "cac_vs_target": "ok" if cac <= _BENCHMARKS["cac_target_abaco_usd"] else "above_target",
            "ltv_cac_vs_3x": "ok" if ltv_cac >= 3.0 else f"below_3x ({ltv_cac:.2f}x)",
        },
        "graph_strategy": {
            "effective_cac_via_hub_usd": round(effective_cac_if_hub, 2),
            "hub_client_multiplier": hub_multiplier_assumption,
            "explanation": (
                f"If a hub client (centrality top 15%) refers {hub_multiplier_assumption} organics, "
                f"effective CAC drops from ${cac:,.0f} to ${effective_cac_if_hub:,.0f}"
            ),
        },
    }


# ─────────────────────────────────────────────────────────────────────────────
# Viral K-Factor
# ─────────────────────────────────────────────────────────────────────────────


def viral_k_factor(
    loans_df: pd.DataFrame,
    conversion_rate: float | None = None,
) -> dict[str, Any]:
    """
    Viral coefficient K = avg_invitations_sent × conversion_rate.

    K > 1 → exponential self-sustaining growth.
    K < 1 → growth decays without paid acquisition.

    Uses:
    - sales_channel column to identify organically acquired clients (referred)
    - sales_agent column to compute KAM-sourced vs organic ratio
    - If referral data unavailable, estimates from repeat_borrower_rate as proxy

    Returns K estimate with confidence level (high/medium/low).
    """
    cust_col = _col(loans_df, ["customer_id", "CodCliente"])
    ch_col = _col(loans_df, ["sales_channel", "Sales Channel", "canal"])

    result: dict[str, Any] = {
        "status": "ok",
        "k_target": 1.0,
        "interpretation": "K > 1 = exponential growth; K < 1 = decays without paid acquisition",
    }

    if ch_col and cust_col:
        result.update(_k_factor_from_channel(loans_df, cust_col, ch_col, conversion_rate))
    elif cust_col:
        if cust_col in loans_df.columns:
            result.update(_k_factor_from_repeat(loans_df, cust_col, conversion_rate))
    else:
        result["status"] = "insufficient_data"
        result["message"] = "No customer_id or sales_channel column found"

    return result


# ─────────────────────────────────────────────────────────────────────────────
# NPL Benchmarks
# ─────────────────────────────────────────────────────────────────────────────


def npl_benchmarks(
    intermedia_df: pd.DataFrame,
) -> dict[str, Any]:
    """
    NPL ratio vs LatAm/OCDE benchmarks (section 4.2).
    Also computes Loss Rate estimate using LGD from business_parameters.yml.
    """
    bal_col = _col(intermedia_df, ["TotalSaldoVigente"])
    fpp_col = _col(intermedia_df, ["FechaPagoProgramado"])

    df = intermedia_df.copy()
    if bal_col:
        df["_bal"] = _num(df, bal_col)
        active = df[df["_bal"] > 0]
    else:
        return {"status": "no_data"}

    total = float(active["_bal"].sum())
    if total == 0:
        return {"status": "no_data"}

    # Compute DPD
    if fpp_col:
        cutoff = pd.Timestamp("2026-03-13")
        active = active.copy()
        active["_due"] = pd.to_datetime(active[fpp_col], errors="coerce")
        active["_dpd"] = (cutoff - active["_due"]).dt.days.clip(lower=0).fillna(0)
    else:
        active["_dpd"] = 0.0

    try:
        npl_90, npl_180 = _calculate_ssot_npl_metrics(active["_bal"], active["_dpd"])
    except Exception:
        npl_90 = float(active[active["_dpd"] >= 90]["_bal"].sum() / total * 100)
        npl_180 = float(active[active["_dpd"] >= 180]["_bal"].sum() / total * 100)

    # Loss rate estimate: NPL × LGD
    try:
        from backend.python.config import settings

        lgd = settings.risk.loss_given_default
    except Exception:
        lgd = 0.10

    loss_rate = npl_180 * lgd

    return {
        "status": "ok",
        "npl_180_pct": round(npl_180, 2),
        "npl_90_pct": round(npl_90, 2),
        "loss_rate_est_pct": round(loss_rate, 2),
        "lgd_assumption": lgd,
        "benchmarks": {
            "npl_latam_pct": _BENCHMARKS["npl_latam_pct"],
            "npl_oecd_pct": _BENCHMARKS["npl_oecd_pct"],
            "npl_target_abaco_pct": _BENCHMARKS["npl_target_abaco_pct"],
            "loss_rate_abs_kbra_pct": _BENCHMARKS["loss_rate_abs_pct"],
        },
        "vs_benchmark": {
            "vs_latam": "better" if npl_180 < _BENCHMARKS["npl_latam_pct"] else "worse",
            "vs_oecd": "better" if npl_180 < _BENCHMARKS["npl_oecd_pct"] else "worse",
            "vs_target": "ok" if npl_180 < _BENCHMARKS["npl_target_abaco_pct"] else "breach",
        },
    }


# ─────────────────────────────────────────────────────────────────────────────
# Master Report
# ─────────────────────────────────────────────────────────────────────────────


def build_graph_kpi_report(
    intermedia_df: pd.DataFrame,
    loans_df: pd.DataFrame,
    payments_df: pd.DataFrame,
) -> dict[str, Any]:
    """
    Run all graph analytics + fintech KPIs and return a single consolidated report.
    This is the entry point for Copilot / pipeline integration.

    Merges into exports/complete_kpi_dashboard.json under key "graph_analytics".
    """
    # Normalise numeric fields
    for col in ["TotalSaldoVigente", "MontoDesembolsado", "ValorAprobado"]:
        if col in intermedia_df.columns:
            intermedia_df[col] = pd.to_numeric(
                intermedia_df[col].astype(str).str.replace(r"[\$,]", "", regex=True),
                errors="coerce",
            ).fillna(0)

    G = build_transaction_graph(intermedia_df, loans_df)
    pr = pagerank_scores(G)
    comms = detect_communities(G)
    rings = detect_fraud_rings(G, intermedia_df)
    hhi = concentration_hhi(intermedia_df, loans_df)
    ue = calc_unit_economics(loans_df, payments_df)
    k_factor = viral_k_factor(loans_df)
    npl = npl_benchmarks(intermedia_df)

    # Decision logic example from strategy doc
    def graph_adjusted_score(base_score: float, pagerank: float, community_risk: str) -> dict:
        adjusted = base_score
        if pagerank > 0.85:
            adjusted *= 1.10
        if community_risk == "HIGH":
            adjusted *= 0.50
        return {
            "base_score": base_score,
            "pagerank": pagerank,
            "community_risk": community_risk,
            "adjusted_score": round(adjusted, 1),
            "decision": "APPROVE" if adjusted > 700 else "REVIEW",
        }

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "graph": {
            "nodes": G.number_of_nodes() if G else 0,
            "edges": G.number_of_edges() if G else 0,
            "networkx_available": _NX,
        },
        "pagerank": pr,
        "communities": comms,
        "fraud_rings": rings,
        "concentration_hhi": hhi,
        "unit_economics": ue,
        "viral_k_factor": k_factor,
        "npl_benchmarks": npl,
        "decision_logic_example": graph_adjusted_score(750, 0.90, "LOW"),
        "copilot_instructions": {
            "to_add_referral_data": "Add 'sales_channel=referral' in HubSpot → export to customer.csv",
            "to_improve_pd_auc": "Join Equifax score + payment cadence features to build_pd_model()",
            "to_activate_graph_score": "Use pagerank['client_scores'] in decision_logic() above",
            "to_connect_neo4j": "Replace build_transaction_graph() with Neo4j GDS PageRank query",
        },
    }
