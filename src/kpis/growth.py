"""KPI helpers for growth calculations."""

from typing import Dict, Tuple  # noqa: E402


def calculate_growth(current: float, previous: float) -> Tuple[float, Dict[str, float]]:
    """Return percent growth from previous to current and a context dict.

    Returns:
        (percent_growth, {"current": current, "previous": previous, "net_change": net})

    Percent growth is rounded to 4 decimal places; if previous is zero it returns 0.0.
    """
    net = current - previous
    if previous == 0:
        pct = 0.0
    else:
        pct = (net / previous) * 100.0
    return round(pct, 4), {"current": current, "previous": previous, "net_change": net}
