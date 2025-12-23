def calculate_portfolio_health(par_30: float, collection_rate: float) -> float:
    """
    Calculate portfolio health score (0-10).
    Score = (10 - PAR30/10) * (CollectionRate/10), capped at 10.
    Inputs must be non-negative. Returns 0.0 for invalid input.
    """
    try:
        par_30 = float(par_30)
        collection_rate = float(collection_rate)
        if par_30 < 0 or collection_rate < 0:
            return 0.0
        par_component = max(0.0, 10.0 - (par_30 / 10.0))
        coll_component = collection_rate / 10.0
        score = par_component * coll_component
        return round(float(min(10.0, max(0.0, score))), 2)
    except Exception:
        return 0.0