from __future__ import annotations
from typing import Any
import pandas as pd
from backend.loans_analytics.logging_config import get_logger
logger = get_logger(__name__)
_THRESHOLDS: dict[str, dict[str, float]] = {'par30': {'excellent': 2.0, 'good': 5.0, 'warning': 10.0, 'critical': 20.0}, 'collection_rate': {'excellent': 95.0, 'good': 90.0, 'warning': 80.0, 'critical': 70.0}, 'npl': {'excellent': 2.0, 'good': 5.0, 'warning': 8.0, 'critical': 15.0}, 'cost_of_risk': {'excellent': 1.0, 'good': 3.0, 'warning': 6.0, 'critical': 10.0}, 'default_rate': {'excellent': 1.0, 'good': 2.0, 'warning': 5.0, 'critical': 10.0}}
_WEIGHTS: dict[str, float] = {'par30': 25.0, 'collection_rate': 25.0, 'npl': 20.0, 'cost_of_risk': 15.0, 'default_rate': 15.0}

def _score_lower_is_better(value: float, thresholds: dict[str, float], weight: float) -> tuple[float, str]:
    exc = thresholds['excellent']
    good = thresholds['good']
    warn = thresholds['warning']
    crit = thresholds['critical']
    if value <= exc:
        pts = weight
        status = 'healthy'
    elif value <= good:
        pts = weight * 0.8
        status = 'healthy'
    elif value <= warn:
        pts = weight * 0.55
        status = 'at_risk'
    elif value <= crit:
        pts = weight * 0.25
        status = 'warning'
    else:
        pts = 0.0
        status = 'critical'
    return (round(pts, 2), status)

def _score_higher_is_better(value: float, thresholds: dict[str, float], weight: float) -> tuple[float, str]:
    exc = thresholds['excellent']
    good = thresholds['good']
    warn = thresholds['warning']
    crit = thresholds['critical']
    if value >= exc:
        pts = weight
        status = 'healthy'
    elif value >= good:
        pts = weight * 0.8
        status = 'healthy'
    elif value >= warn:
        pts = weight * 0.55
        status = 'at_risk'
    elif value >= crit:
        pts = weight * 0.25
        status = 'warning'
    else:
        pts = 0.0
        status = 'critical'
    return (round(pts, 2), status)

def _traffic_light(score: float) -> str:
    if score >= 80:
        return 'healthy'
    if score >= 60:
        return 'at_risk'
    return 'warning' if score >= 40 else 'critical'

def calculate_portfolio_health_score(par30: float, collection_rate: float, npl: float, cost_of_risk: float, default_rate: float) -> dict[str, Any]:
    par30_pts, par30_status = _score_lower_is_better(par30, _THRESHOLDS['par30'], _WEIGHTS['par30'])
    cr_pts, cr_status = _score_higher_is_better(collection_rate, _THRESHOLDS['collection_rate'], _WEIGHTS['collection_rate'])
    npl_pts, npl_status = _score_lower_is_better(npl, _THRESHOLDS['npl'], _WEIGHTS['npl'])
    cor_pts, cor_status = _score_lower_is_better(cost_of_risk, _THRESHOLDS['cost_of_risk'], _WEIGHTS['cost_of_risk'])
    dr_pts, dr_status = _score_lower_is_better(default_rate, _THRESHOLDS['default_rate'], _WEIGHTS['default_rate'])
    score = round(par30_pts + cr_pts + npl_pts + cor_pts + dr_pts, 2)
    light = _traffic_light(score)
    components = [{'dimension': 'PAR30', 'value': round(par30, 4), 'unit': '%', 'weight': _WEIGHTS['par30'], 'points_earned': par30_pts, 'status': par30_status, 'thresholds': _THRESHOLDS['par30'], 'direction': 'lower_is_better'}, {'dimension': 'Collection Rate', 'value': round(collection_rate, 4), 'unit': '%', 'weight': _WEIGHTS['collection_rate'], 'points_earned': cr_pts, 'status': cr_status, 'thresholds': _THRESHOLDS['collection_rate'], 'direction': 'higher_is_better'}, {'dimension': 'NPL Ratio', 'value': round(npl, 4), 'unit': '%', 'weight': _WEIGHTS['npl'], 'points_earned': npl_pts, 'status': npl_status, 'thresholds': _THRESHOLDS['npl'], 'direction': 'lower_is_better'}, {'dimension': 'Cost of Risk', 'value': round(cost_of_risk, 4), 'unit': '%', 'weight': _WEIGHTS['cost_of_risk'], 'points_earned': cor_pts, 'status': cor_status, 'thresholds': _THRESHOLDS['cost_of_risk'], 'direction': 'lower_is_better'}, {'dimension': 'Default Rate', 'value': round(default_rate, 4), 'unit': '%', 'weight': _WEIGHTS['default_rate'], 'points_earned': dr_pts, 'status': dr_status, 'thresholds': _THRESHOLDS['default_rate'], 'direction': 'lower_is_better'}]
    critical_components = [str(c['dimension']) for c in components if c['status'] == 'critical']
    at_risk_components = [str(c['dimension']) for c in components if c['status'] in ('at_risk', 'warning')]
    if critical_components:
        interpretation = f"Portfolio is in CRITICAL condition. Immediate action required on: {', '.join(critical_components)}."
    elif at_risk_components:
        interpretation = f"Portfolio shows elevated risk. Monitor closely: {', '.join(at_risk_components)}."
    else:
        interpretation = 'Portfolio is performing within healthy parameters across all risk dimensions.'
    logger.debug('Portfolio Health Score=%.2f (%s), components=%s', score, light, {c['dimension']: c['points_earned'] for c in components})
    return {'score': score, 'traffic_light': light, 'components': components, 'formula': 'PAR30(25pts) + CollectionRate(25pts) + NPL(20pts) + CostOfRisk(15pts) + DefaultRate(15pts)', 'interpretation': interpretation}

def calculate_health_score_from_df(df: pd.DataFrame) -> dict[str, Any]:
    if df.empty:
        return calculate_portfolio_health_score(0.0, 100.0, 0.0, 0.0, 0.0)
    from backend.loans_analytics.kpis.advanced_risk import calculate_advanced_risk_metrics
    from backend.loans_analytics.kpis.unit_economics import calculate_cost_of_risk, calculate_npl_ratio
    adv = calculate_advanced_risk_metrics(df)
    npl_data = calculate_npl_ratio(df)
    cor_data = calculate_cost_of_risk(df)
    return calculate_portfolio_health_score(par30=adv['par30'], collection_rate=adv['collections_coverage'], npl=npl_data['npl_ratio'], cost_of_risk=cor_data['cost_of_risk_pct'], default_rate=adv['default_rate'])
