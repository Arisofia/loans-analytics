
def calculate_portfolio_health(par_30: float, collection_rate: float) -> float:
    """Portfolio Health Score (0-10 scale)
    Formula: (10 - PAR_30/10) * (CollectionRate * 10)
    """
    health_score = (10 - (par_30 / 10)) * (collection_rate / 10)
    health_score = max(0, min(10, health_score))
    return health_score
