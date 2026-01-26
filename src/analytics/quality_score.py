from typing import Any, Mapping


def calculate_financial_quality_score(metrics: Mapping[str, Any]) -> float:
    """
    Compute a portfolio 'quality score' as a float.
    Penalizes high risk and concentration, rewards good replines.
    Clamped to 0..100.
    """
    dpd30 = float(metrics.get("dpd_30_plus_rate", 0.0))
    par90 = float(metrics.get("par_90_ratio", 0.0))
    replines = float(metrics.get("replines_pct", 0.0))
    concentration = float(metrics.get("top_10_concentration_pct", 0.0))

    score = 100.0
    score -= dpd30 * 200.0
    score -= par90 * 300.0
    score -= max(concentration - 0.3, 0.0) * 50.0
    score += replines * 50.0
    score = max(0.0, min(100.0, score))
    return round(score, 2)
