def calculate_portfolio_health(par_30: float, collection_rate: float) -> float:
    """
    Calculate portfolio health score (0-10).
    Logic based on test expectations: (10 - PAR30/10) * (CollectionRate/10)
    Capped at 10.
    """
    # Ensure inputs are treated as floats
    par_component = max(0.0, 10.0 - (float(par_30) / 10.0))
    coll_component = float(collection_rate) / 10.0

    score = par_component * coll_component
    return float(min(10.0, max(0.0, score)))
