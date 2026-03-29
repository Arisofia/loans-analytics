from __future__ import annotations
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Literal, cast
import uuid
import pandas as pd
from starlette.concurrency import run_in_threadpool
from backend.python.apps.analytics.api.models import (
    AdvancedRiskResponse,
    AnalysisLayer,
    CohortAnalyticsResponse,
    CohortAnalyticsSummary,
    CohortMetrics,
    CostOfRiskMetrics,
    CureRateMetrics,
    DataQualityResponse,
    DecisionDashboardResponse,
    DPDBucketWithAction,
    DecisionFlag,
    KpiContext,
    KpiSingleResponse,
    LgdMetrics,
    LoanRecord,
    NimMetrics,
    NplMetrics,
    NSMPeriodMetrics,
    NSMRecurrentTPVResponse,
    PaybackMetrics,
    PortfolioHealthComponent,
    PortfolioHealthScore,
    RiskHeatmapResponse,
    RiskStratificationResponse,
    RollRateAnalyticsResponse,
    RollRateAnalyticsSummary,
    RollRateBucketSummary,
    RollRateTransition,
    SegmentAnalyticsResponse,
    SegmentAnalyticsSummary,
    SegmentMetrics,
    StressTestAssumptions,
    StressTestMetrics,
    StressTestResponse,
    UnitEconomicsResponse,
    ValidationResponse,
    VintageCurvePoint,
    VintageCurveResponse,
)
from backend.python.config import settings
from backend.python.kpis.advanced_risk import calculate_advanced_risk_metrics
from backend.python.kpis.catalog_processor import KPICatalogProcessor
from backend.python.kpis.health_score import calculate_portfolio_health_score
from backend.python.kpis.ssot_asset_quality import calculate_asset_quality_metrics
from backend.python.kpis.unit_economics import (
    calculate_all_unit_economics,
    calculate_cost_of_risk,
    calculate_lgd,
    calculate_nim,
    calculate_npl_ratio,
)
from backend.python.logging_config import get_logger
from backend.python.supabase_pool import get_pool

logger = get_logger(__name__)
DATA_MISSING_SCORE = 0.0
DATA_MISSING_INTERPRETATION = (
    "No loan data available. Score cannot be computed. Investigate data pipeline."
)
_PORTFOLIO_HEALTH_FORMULA = (
    "PAR30(25pts) + CollectionRate(25pts) + NPL(20pts) + "
    + "CostOfRisk(15pts) + DefaultRate(15pts)"
)
try:
    import yaml as _yaml

    yaml: Any = _yaml
except ImportError:
    yaml = None
KPI_DEFINITIONS_PATH = (
    Path(__file__).resolve().parents[4] / "config" / "kpis" / "kpi_definitions.yaml"
)
KPI_API_TO_CATALOG_ID = {
    "PAR30": "par_30",
    "PAR_30": "par_30",
    "PAR60": "par_60",
    "PAR_60": "par_60",
    "PAR90": "par_90",
    "PAR_90": "par_90",
    "DPD_1_30": "dpd_1_30",
    "DPD_31_60": "dpd_31_60",
    "DPD_61_90": "dpd_61_90",
    "DPD_90_PLUS": "dpd_90_plus",
    "COLLECTION_RATE": "collections_rate",
    "DEFAULT_RATE": "default_rate",
    "TOTAL_LOANS_COUNT": "total_loans_count",
    "LOSS_RATE": "loss_rate",
    "RECOVERY_RATE": "recovery_rate",
    "CASH_ON_HAND": "cash_on_hand",
    "PORTFOLIO_YIELD": "portfolio_yield",
    "AVERAGE_LOAN_SIZE": "average_loan_size",
    "DISBURSEMENT_VOLUME_MTD": "disbursement_volume_mtd",
    "NEW_LOANS_COUNT_MTD": "new_loans_count_mtd",
    "PORTFOLIO_HEALTH": "portfolio_growth_rate",
    "CUSTOMER_LIFETIME_VALUE": "customer_lifetime_value",
    "ACTIVE_BORROWERS": "active_borrowers",
    "REPEAT_BORROWER_RATE": "repeat_borrower_rate",
    "AUTOMATION_RATE": "automation_rate",
    "PROCESSING_TIME_AVG": "processing_time_avg",
    "AUM": "total_outstanding_balance",
    "CAC": "cac",
    "GROSS_MARGIN_PCT": "gross_margin_pct",
    "REVENUE_FORECAST_6M": "revenue_forecast_6m",
    "CHURN_90D": "churn_90d",
}
STATUS_PATTERN_90_PLUS = "90\\+|default|charged"
STATUS_PATTERN_60_89 = "60-89|60\\+"
STATUS_PATTERN_30_59 = "30-59|30\\+"
STATUS_PATTERN_DEFAULT = "default|charged"
DEFAULT_KPI_METADATA: dict[str, dict[str, Any]] = {
    "PAR30": {
        "formula": "SUM(principal_balance WHERE dpd >= 30) / SUM(principal_balance) * 100",
        "definition": "Portfolio at Risk with more than 30 days past due.",
        "implications": "Higher PAR30 indicates deteriorating portfolio quality and collections pressure.",
    },
    "PAR90": {
        "formula": "SUM(principal_balance WHERE dpd >= 90) / SUM(principal_balance) * 100",
        "definition": "Portfolio at Risk with more than 90 days past due.",
        "implications": "Higher PAR90 signals severe delinquency and elevated expected credit losses.",
    },
    "PAR60": {
        "formula": "SUM(principal_balance WHERE dpd >= 60) / SUM(principal_balance) * 100",
        "definition": "Portfolio at Risk with more than 60 days past due.",
        "implications": "Rising PAR60 is an early warning for migration into severe delinquency buckets.",
        "thresholds": {"warning": 2.0, "critical": 4.0},
    },
    "DPD_1_30": {
        "formula": "SUM(principal_balance WHERE 0 < dpd <= 30) / SUM(principal_balance) * 100",
        "definition": "Outstanding balance share in the 1-30 days past due bucket.",
        "implications": "A rising 1-30 DPD bucket indicates early collections pressure building.",
    },
    "DPD_31_60": {
        "formula": "SUM(principal_balance WHERE 30 < dpd <= 60) / SUM(principal_balance) * 100",
        "definition": "Outstanding balance share in the 31-60 days past due bucket.",
        "implications": "A rising 31-60 DPD bucket is an early warning of roll-forward risk into severe delinquency.",
    },
    "DPD_61_90": {
        "formula": "SUM(principal_balance WHERE 60 < dpd <= 90) / SUM(principal_balance) * 100",
        "definition": "Outstanding balance share in the 61-90 days past due bucket.",
        "implications": "Growth in 61-90 DPD points to elevated near-term loss and recovery workload.",
    },
    "DPD_90_PLUS": {
        "formula": "SUM(principal_balance WHERE dpd > 90) / SUM(principal_balance) * 100",
        "definition": "Outstanding balance share in the 90+ days past due bucket.",
        "implications": "A higher 90+ DPD bucket signals severe delinquency and higher expected credit losses.",
    },
    "COLLECTION_RATE": {
        "formula": "SUM(collected_amount) / SUM(scheduled_amount) * 100",
        "definition": "Collection efficiency against scheduled amounts.",
        "implications": "Lower collection rate reduces cash conversion and may indicate process weaknesses.",
        "thresholds": {"warning": 85.0, "target": 95.0, "critical": 80.0},
        "benchmark": 95.0,
    },
    "LOSS_RATE": {
        "formula": "SUM(principal_balance WHERE status = defaulted) / SUM(loan_amount) * 100",
        "definition": "Defaulted outstanding exposure as a share of total originated principal.",
        "implications": "Higher loss rate increases provisioning needs and can pressure capital ratios.",
    },
    "RECOVERY_RATE": {
        "formula": "SUM(last_payment_amount WHERE status = defaulted) / SUM(principal_balance WHERE status = defaulted) * 100",
        "definition": "Recovery performance over defaulted exposure.",
        "implications": "Improving recoveries lowers loss-given-default and supports earnings resilience.",
    },
    "CASH_ON_HAND": {
        "formula": "SUM(current_balance)",
        "definition": "Total current balance available across the provided portfolio records.",
        "implications": "Lower liquidity buffer can constrain disbursement capacity and debt service flexibility.",
    },
    "PORTFOLIO_YIELD": {
        "formula": "SUM(interest_rate * principal_balance) / SUM(principal_balance) * 100",
        "definition": "Weighted average annualized portfolio yield.",
        "implications": "Yield below risk-adjusted cost thresholds can compress margins.",
    },
    "AUM": {
        "formula": "SUM(principal_balance)",
        "definition": "Assets under management based on outstanding principal.",
        "implications": "AUM growth improves scale, but must be balanced against delinquency and loss rates.",
    },
    "AVG_LTV": {
        "formula": "AVG(loan_amount / appraised_value * 100)",
        "definition": "Average loan-to-value ratio across the analyzed population.",
        "implications": "Higher LTV reduces collateral buffer and increases loss-given-default sensitivity.",
    },
    "AVG_DTI": {
        "formula": "AVG(monthly_debt / borrower_income * 100)",
        "definition": "Average debt-to-income ratio across the analyzed population.",
        "implications": "Higher DTI indicates repayment stress and potential delinquency pressure.",
    },
    "DEFAULT_RATE": {
        "formula": "COUNT(loans WHERE status = defaulted) / COUNT(loans) * 100",
        "definition": "Share of loans in default status.",
        "implications": "Rising default rate typically requires underwriting and collections adjustments.",
        "thresholds": {"warning": 2.0, "critical": 5.0},
    },
    "COLLECTIONS_COVERAGE": {
        "formula": "SUM(last_payment_amount) / SUM(total_scheduled) * 100",
        "definition": "Collections coverage ratio using observed payment versus scheduled amounts.",
        "implications": "Low coverage indicates cash conversion pressure and potential liquidity stress.",
    },
    "FEE_YIELD": {
        "formula": "SUM(origination_fee + origination_fee_taxes) / SUM(principal_amount) * 100",
        "definition": "Fee contribution as a percentage of principal originated.",
        "implications": "Fee yield helps quantify non-interest revenue sustainability.",
    },
    "TOTAL_YIELD": {
        "formula": "Interest Yield + Fee Yield",
        "definition": "Combined yield from interest and fee streams.",
        "implications": "Total yield should be evaluated against funding costs and credit losses.",
    },
    "CONCENTRATION_HHI": {
        "formula": "SUM((borrower_exposure / total_exposure)^2) * 10000",
        "definition": "Herfindahl-Hirschman index for borrower concentration risk.",
        "implications": "Higher HHI indicates concentration and lower diversification resilience.",
    },
    "CREDIT_QUALITY_INDEX": {
        "formula": "((AVG(credit_score) - 300) / 550) * 100",
        "definition": "Normalized credit quality index from bureau score distribution.",
        "implications": "Lower index values indicate weaker borrower credit quality mix.",
    },
    "PORTFOLIO_GROWTH_RATE": {
        "formula": "(current_period_balance - prior_period_balance) / prior_period_balance * 100",
        "definition": "Period-over-period portfolio balance growth.",
        "implications": "Growth is positive only if accompanied by stable asset-quality and collections KPIs.",
    },
    "AVERAGE_LOAN_SIZE": {
        "formula": "AVG(loan_amount)",
        "definition": "Average original principal amount for loans in the current sample.",
        "implications": "Ticket-size changes alter risk concentration and operational servicing cost profile.",
    },
    "DISBURSEMENT_VOLUME_MTD": {
        "formula": "SUM(loan_amount WHERE origination_date >= MONTH_START)",
        "definition": "Total disbursed principal during the current calendar month.",
        "implications": "MTD disbursement momentum signals growth pace and funding utilization.",
    },
    "NEW_LOANS_COUNT_MTD": {
        "formula": "COUNT(loans WHERE origination_date >= MONTH_START)",
        "definition": "Number of originated loans in the current calendar month.",
        "implications": "Origination count trends help separate growth from average ticket-size effects.",
    },
    "TOTAL_LOANS_COUNT": {
        "formula": "COUNT(DISTINCT loan_id WHERE status != closed)",
        "definition": "Total number of loans represented in the analyzed population.",
        "implications": "Loan-count growth changes operational load and may require capacity planning.",
    },
    "ACTIVE_BORROWERS": {
        "formula": "COUNT(DISTINCT borrower_id WHERE status != closed)",
        "definition": "Distinct borrower count for loans still active in the portfolio context.",
        "implications": "Borrower base concentration and engagement should be monitored with this KPI.",
    },
    "REPEAT_BORROWER_RATE": {
        "formula": "COUNT(DISTINCT borrower_id with loan_count > 1) / COUNT(DISTINCT borrower_id) * 100",
        "definition": "Share of borrowers with multiple loans in the analyzed sample.",
        "implications": "Higher repeat usage can indicate retention strength and/or concentration build-up.",
    },
    "AUTOMATION_RATE": {
        "formula": "COUNT(loans WHERE payment_frequency in ['bullet','auto']) / COUNT(loans) * 100",
        "definition": "Share of loans with automated or bullet payment scheduling.",
        "implications": "Higher automation can reduce servicing overhead and collection friction.",
    },
    "PROCESSING_TIME_AVG": {
        "formula": "AVG(term_months)",
        "definition": "Average term length in months for the provided loan sample.",
        "implications": "Longer average tenor increases duration risk and prolongs exposure lifecycle.",
    },
    "CUSTOMER_LIFETIME_VALUE": {
        "formula": "SUM(tpv) / COUNT(DISTINCT borrower_id)",
        "definition": "Average total processed value per borrower in the provided loan sample.",
        "implications": "Higher CLV can improve unit economics if loss and servicing costs remain controlled.",
    },
    "CAC": {
        "formula": "SUM(marketing_spend) / COUNT(new_customers)",
        "definition": "Customer acquisition cost estimated from catalog processor unit economics.",
        "implications": "Lower CAC improves payback and growth efficiency.",
    },
    "GROSS_MARGIN_PCT": {
        "formula": "(revenue - direct_costs - risk_cost_proxy) / revenue * 100",
        "definition": "Gross margin from strategic unit-economics model.",
        "implications": "Declining gross margin can indicate pricing or risk-cost pressure.",
    },
    "REVENUE_FORECAST_6M": {
        "formula": "SUM(forecast_revenue_usd for next 6 months)",
        "definition": "Total projected revenue across the next six forecasted months.",
        "implications": "Forecast deterioration can signal slowing growth or margin compression ahead.",
    },
    "CHURN_90D": {
        "formula": "inactive_90d / known_customers * 100",
        "definition": "90-day churn estimate from customer activity windows.",
        "implications": "Higher churn weakens portfolio durability and can elevate CAC requirements.",
    },
    "NPL": {
        "formula": "SUM(principal_balance WHERE dpd >= 90 OR status = defaulted) / SUM(principal_balance) * 100",
        "definition": "Non-Performing Loan ratio (strict): balance-weighted 90+ DPD or defaulted exposure.",
        "implications": "Tracks severe delinquency/default exposure and should align with NPL_90 and PAR90 governance.",
    },
    "LGD": {
        "formula": "(1 - Recovery Rate / 100) * 100",
        "definition": "Loss Given Default - share of defaulted exposure not expected to be recovered.",
        "implications": "Determines the severity of losses once a default occurs.",
    },
    "COR": {
        "formula": "Loss Rate (provisioning proxy)",
        "definition": "Cost of Risk - annualized credit losses over total portfolio principal.",
        "implications": "Direct hit to profitability; must be covered by net interest margin.",
    },
    "NIM": {
        "formula": "(Interest Income - Interest Expense) / Average Earning Assets",
        "definition": "Net Interest Margin - spread between lending yield and funding cost.",
        "implications": "Primary driver of banking-model profitability.",
    },
    "CURERATE": {
        "formula": "Migration from Delinquent to Current",
        "definition": "Share of delinquent loans that return to current status in the next observation.",
        "implications": "Higher cure rates indicate effective collections and healthy borrower behavior.",
    },
}

KPI_DEFINITIONS_PATH = Path(__file__).resolve().parents[4] / 'config' / 'kpis' / 'kpi_definitions.yaml'
KPI_API_TO_CATALOG_ID = {'PAR30': 'par_30', 'PAR_30': 'par_30', 'PAR60': 'par_60', 'PAR_60': 'par_60', 'PAR90': 'par_90', 'PAR_90': 'par_90', 'DPD_1_30': 'dpd_1_30', 'DPD_31_60': 'dpd_31_60', 'DPD_61_90': 'dpd_61_90', 'DPD_90_PLUS': 'dpd_90_plus', 'COLLECTION_RATE': 'collections_rate', 'DEFAULT_RATE': 'default_rate', 'TOTAL_LOANS_COUNT': 'total_loans_count', 'LOSS_RATE': 'loss_rate', 'RECOVERY_RATE': 'recovery_rate', 'CASH_ON_HAND': 'cash_on_hand', 'PORTFOLIO_YIELD': 'portfolio_yield', 'AVERAGE_LOAN_SIZE': 'average_loan_size', 'DISBURSEMENT_VOLUME_MTD': 'disbursement_volume_mtd', 'NEW_LOANS_COUNT_MTD': 'new_loans_count_mtd', 'PORTFOLIO_HEALTH': 'portfolio_growth_rate', 'CUSTOMER_LIFETIME_VALUE': 'customer_lifetime_value', 'ACTIVE_BORROWERS': 'active_borrowers', 'REPEAT_BORROWER_RATE': 'repeat_borrower_rate', 'AUTOMATION_RATE': 'automation_rate', 'PROCESSING_TIME_AVG': 'processing_time_avg', 'AUM': 'total_outstanding_balance', 'CAC': 'cac', 'GROSS_MARGIN_PCT': 'gross_margin_pct', 'REVENUE_FORECAST_6M': 'revenue_forecast_6m', 'CHURN_90D': 'churn_90d'}
STATUS_PATTERN_90_PLUS = '90\\+|default|charged'
STATUS_PATTERN_60_89 = '60-89|60\\+'
STATUS_PATTERN_30_59 = '30-59|30\\+'
STATUS_PATTERN_DEFAULT = 'default|charged'
DEFAULT_KPI_METADATA: dict[str, dict[str, Any]] = {'PAR30': {'formula': 'SUM(principal_balance WHERE dpd >= 30) / SUM(principal_balance) * 100', 'definition': 'Portfolio at Risk with more than 30 days past due.', 'implications': 'Higher PAR30 indicates deteriorating portfolio quality and collections pressure.'}, 'PAR90': {'formula': 'SUM(principal_balance WHERE dpd >= 90) / SUM(principal_balance) * 100', 'definition': 'Portfolio at Risk with more than 90 days past due.', 'implications': 'Higher PAR90 signals severe delinquency and elevated expected credit losses.'}, 'PAR60': {'formula': 'SUM(principal_balance WHERE dpd >= 60) / SUM(principal_balance) * 100', 'definition': 'Portfolio at Risk with more than 60 days past due.', 'implications': 'Rising PAR60 is an early warning for migration into severe delinquency buckets.', 'thresholds': {'warning': 2.0, 'critical': 4.0}}, 'DPD_1_30': {'formula': 'SUM(principal_balance WHERE 0 < dpd <= 30) / SUM(principal_balance) * 100', 'definition': 'Outstanding balance share in the 1-30 days past due bucket.', 'implications': 'A rising 1-30 DPD bucket indicates early collections pressure building.'}, 'DPD_31_60': {'formula': 'SUM(principal_balance WHERE 30 < dpd <= 60) / SUM(principal_balance) * 100', 'definition': 'Outstanding balance share in the 31-60 days past due bucket.', 'implications': 'A rising 31-60 DPD bucket is an early warning of roll-forward risk into severe delinquency.'}, 'DPD_61_90': {'formula': 'SUM(principal_balance WHERE 60 < dpd <= 90) / SUM(principal_balance) * 100', 'definition': 'Outstanding balance share in the 61-90 days past due bucket.', 'implications': 'Growth in 61-90 DPD points to elevated near-term loss and recovery workload.'}, 'DPD_90_PLUS': {'formula': 'SUM(principal_balance WHERE dpd > 90) / SUM(principal_balance) * 100', 'definition': 'Outstanding balance share in the 90+ days past due bucket.', 'implications': 'A higher 90+ DPD bucket signals severe delinquency and higher expected credit losses.'}, 'COLLECTION_RATE': {'formula': 'SUM(collected_amount) / SUM(scheduled_amount) * 100', 'definition': 'Collection efficiency against scheduled amounts.', 'implications': 'Lower collection rate reduces cash conversion and may indicate process weaknesses.', 'thresholds': {'warning': 85.0, 'target': 95.0, 'critical': 80.0}, 'benchmark': 95.0}, 'LOSS_RATE': {'formula': 'SUM(principal_balance WHERE status = defaulted) / SUM(loan_amount) * 100', 'definition': 'Defaulted outstanding exposure as a share of total originated principal.', 'implications': 'Higher loss rate increases provisioning needs and can pressure capital ratios.'}, 'RECOVERY_RATE': {'formula': 'SUM(last_payment_amount WHERE status = defaulted) / SUM(principal_balance WHERE status = defaulted) * 100', 'definition': 'Recovery performance over defaulted exposure.', 'implications': 'Improving recoveries lowers loss-given-default and supports earnings resilience.'}, 'CASH_ON_HAND': {'formula': 'SUM(current_balance)', 'definition': 'Total current balance available across the provided portfolio records.', 'implications': 'Lower liquidity buffer can constrain disbursement capacity and debt service flexibility.'}, 'PORTFOLIO_YIELD': {'formula': 'SUM(interest_rate * principal_balance) / SUM(principal_balance) * 100', 'definition': 'Weighted average annualized portfolio yield.', 'implications': 'Yield below risk-adjusted cost thresholds can compress margins.'}, 'AUM': {'formula': 'SUM(principal_balance)', 'definition': 'Assets under management based on outstanding principal.', 'implications': 'AUM growth improves scale, but must be balanced against delinquency and loss rates.'}, 'AVG_LTV': {'formula': 'AVG(loan_amount / appraised_value * 100)', 'definition': 'Average loan-to-value ratio across the analyzed population.', 'implications': 'Higher LTV reduces collateral buffer and increases loss-given-default sensitivity.'}, 'AVG_DTI': {'formula': 'AVG(monthly_debt / borrower_income * 100)', 'definition': 'Average debt-to-income ratio across the analyzed population.', 'implications': 'Higher DTI indicates repayment stress and potential delinquency pressure.'}, 'DEFAULT_RATE': {'formula': 'COUNT(loans WHERE status = defaulted) / COUNT(loans) * 100', 'definition': 'Share of loans in default status.', 'implications': 'Rising default rate typically requires underwriting and collections adjustments.', 'thresholds': {'warning': 2.0, 'critical': 5.0}}, 'COLLECTIONS_COVERAGE': {'formula': 'SUM(last_payment_amount) / SUM(total_scheduled) * 100', 'definition': 'Collections coverage ratio using observed payment versus scheduled amounts.', 'implications': 'Low coverage indicates cash conversion pressure and potential liquidity stress.'}, 'FEE_YIELD': {'formula': 'SUM(origination_fee + origination_fee_taxes) / SUM(principal_amount) * 100', 'definition': 'Fee contribution as a percentage of principal originated.', 'implications': 'Fee yield helps quantify non-interest revenue sustainability.'}, 'TOTAL_YIELD': {'formula': 'Interest Yield + Fee Yield', 'definition': 'Combined yield from interest and fee streams.', 'implications': 'Total yield should be evaluated against funding costs and credit losses.'}, 'CONCENTRATION_HHI': {'formula': 'SUM((borrower_exposure / total_exposure)^2) * 10000', 'definition': 'Herfindahl-Hirschman index for borrower concentration risk.', 'implications': 'Higher HHI indicates concentration and lower diversification resilience.'}, 'CREDIT_QUALITY_INDEX': {'formula': '((AVG(credit_score) - 300) / 550) * 100', 'definition': 'Normalized credit quality index from bureau score distribution.', 'implications': 'Lower index values indicate weaker borrower credit quality mix.'}, 'PORTFOLIO_GROWTH_RATE': {'formula': '(current_period_balance - prior_period_balance) / prior_period_balance * 100', 'definition': 'Period-over-period portfolio balance growth.', 'implications': 'Growth is positive only if accompanied by stable asset-quality and collections KPIs.'}, 'AVERAGE_LOAN_SIZE': {'formula': 'AVG(loan_amount)', 'definition': 'Average original principal amount for loans in the current sample.', 'implications': 'Ticket-size changes alter risk concentration and operational servicing cost profile.'}, 'DISBURSEMENT_VOLUME_MTD': {'formula': 'SUM(loan_amount WHERE origination_date >= MONTH_START)', 'definition': 'Total disbursed principal during the current calendar month.', 'implications': 'MTD disbursement momentum signals growth pace and funding utilization.'}, 'NEW_LOANS_COUNT_MTD': {'formula': 'COUNT(loans WHERE origination_date >= MONTH_START)', 'definition': 'Number of originated loans in the current calendar month.', 'implications': 'Origination count trends help separate growth from average ticket-size effects.'}, 'TOTAL_LOANS_COUNT': {'formula': 'COUNT(DISTINCT loan_id WHERE status != closed)', 'definition': 'Total number of loans represented in the analyzed population.', 'implications': 'Loan-count growth changes operational load and may require capacity planning.'}, 'ACTIVE_BORROWERS': {'formula': 'COUNT(DISTINCT borrower_id WHERE status != closed)', 'definition': 'Distinct borrower count for loans still active in the portfolio context.', 'implications': 'Borrower base concentration and engagement should be monitored with this KPI.'}, 'REPEAT_BORROWER_RATE': {'formula': 'COUNT(DISTINCT borrower_id with loan_count > 1) / COUNT(DISTINCT borrower_id) * 100', 'definition': 'Share of borrowers with multiple loans in the analyzed sample.', 'implications': 'Higher repeat usage can indicate retention strength and/or concentration build-up.'}, 'AUTOMATION_RATE': {'formula': "COUNT(loans WHERE payment_frequency in ['bullet','auto']) / COUNT(loans) * 100", 'definition': 'Share of loans with automated or bullet payment scheduling.', 'implications': 'Higher automation can reduce servicing overhead and collection friction.'}, 'PROCESSING_TIME_AVG': {'formula': 'AVG(term_months)', 'definition': 'Average term length in months for the provided loan sample.', 'implications': 'Longer average tenor increases duration risk and prolongs exposure lifecycle.'}, 'CUSTOMER_LIFETIME_VALUE': {'formula': 'SUM(tpv) / COUNT(DISTINCT borrower_id)', 'definition': 'Average total processed value per borrower in the provided loan sample.', 'implications': 'Higher CLV can improve unit economics if loss and servicing costs remain controlled.'}, 'CAC': {'formula': 'SUM(marketing_spend) / COUNT(new_customers)', 'definition': 'Customer acquisition cost estimated from catalog processor unit economics.', 'implications': 'Lower CAC improves payback and growth efficiency.'}, 'GROSS_MARGIN_PCT': {'formula': '(revenue - direct_costs - risk_cost_proxy) / revenue * 100', 'definition': 'Gross margin from strategic unit-economics model.', 'implications': 'Declining gross margin can indicate pricing or risk-cost pressure.'}, 'REVENUE_FORECAST_6M': {'formula': 'SUM(forecast_revenue_usd for next 6 months)', 'definition': 'Total projected revenue across the next six forecasted months.', 'implications': 'Forecast deterioration can signal slowing growth or margin compression ahead.'}, 'CHURN_90D': {'formula': 'inactive_90d / known_customers * 100', 'definition': '90-day churn estimate from customer activity windows.', 'implications': 'Higher churn weakens portfolio durability and can elevate CAC requirements.'}, 'NPL': {'formula': "SUM(principal_balance WHERE dpd >= 90 OR status = defaulted) / SUM(principal_balance) * 100", 'definition': 'Non-Performing Loans ratio (strict) - balance-weighted 90+ DPD or defaulted exposure.', 'implications': 'Early-warning asset-quality metric; track alongside NPL_90 for severe delinquency.'}, 'LGD': {'formula': '(1 - Recovery Rate / 100) * 100', 'definition': 'Loss Given Default - share of defaulted exposure not expected to be recovered.', 'implications': 'Determines the severity of losses once a default occurs.'}, 'COR': {'formula': 'Loss Rate (provisioning proxy)', 'definition': 'Cost of Risk - annualized credit losses over total portfolio principal.', 'implications': 'Direct hit to profitability; must be covered by net interest margin.'}, 'NIM': {'formula': '(Interest Income - Interest Expense) / Average Earning Assets', 'definition': 'Net Interest Margin - spread between lending yield and funding cost.', 'implications': 'Primary driver of banking-model profitability.'}, 'CURERATE': {'formula': 'Migration from Delinquent to Current', 'definition': 'Share of delinquent loans that return to current status in the next observation.', 'implications': 'Higher cure rates indicate effective collections and healthy borrower behavior.'}}

def _normalize_kpi_key(kpi_id: str) -> str:
    return (kpi_id or "").strip().replace("-", "_").replace(" ", "_").upper()


def _extract_kpi_metadata(kpi_def: dict[str, Any]) -> dict[str, Any]:
    raw_thresholds = kpi_def.get("thresholds")
    thresholds: dict[str, float] = {}
    if isinstance(raw_thresholds, dict):
        for key, value in raw_thresholds.items():
            try:
                thresholds[str(key)] = float(value)
            except (TypeError, ValueError):
                continue
    threshold_note = ""
    if thresholds:
        threshold_pairs = ", ".join((f"{k}={v}" for k, v in thresholds.items()))
        threshold_note = f" Compare against configured thresholds ({threshold_pairs})."
    return {
        "formula": str(kpi_def.get("formula", "")),
        "definition": str(kpi_def.get("description", "")),
        "implications": f"Use trend and segment context when interpreting this KPI.{threshold_note}",
        "thresholds": thresholds,
        "benchmark": thresholds.get("target"),
    }


_CATALOG_STATE: dict[str, Any] = {"cache": {}, "file_hash": ""}


def _load_catalog_kpi_metadata() -> dict[str, dict[str, Any]]:
    if yaml is None or not KPI_DEFINITIONS_PATH.exists():
        return {}
    try:
        import hashlib

        with open(KPI_DEFINITIONS_PATH, "rb") as f:
            current_hash = hashlib.md5(f.read(), usedforsecurity=False).hexdigest()
        if current_hash == _CATALOG_STATE["file_hash"]:
            return _CATALOG_STATE["cache"]
        with open(KPI_DEFINITIONS_PATH, encoding="utf-8") as handle:
            payload = yaml.safe_load(handle)
            if payload is None:
                raise ValueError(
                    f"KPI definitions file {KPI_DEFINITIONS_PATH} is empty or invalid."
                )
        _CATALOG_STATE["file_hash"] = current_hash
    except Exception as exc:
        logger.error("Failed to load KPI catalog metadata: %s", exc, exc_info=True)
        raise ValueError(f"CRITICAL: Failed to load KPI catalog metadata: {exc}") from exc
    metadata: dict[str, dict[str, Any]] = {}
    for top_key, section in payload.items():
        if not top_key.endswith("_kpis") or not isinstance(section, dict):
            continue
        for kpi_id, kpi_def in section.items():
            if isinstance(kpi_def, dict):
                metadata[kpi_id.lower()] = _extract_kpi_metadata(kpi_def)
    _CATALOG_STATE["cache"] = metadata
    return metadata


class KPIService:

    def __init__(self, actor: str = "api_user"):
        self.actor = actor

    def get_catalog_kpi_ids(self) -> list[str]:
        return sorted(_load_catalog_kpi_metadata().keys())

    def get_supported_catalog_kpi_ids(self) -> list[str]:
        supported = {KPI_API_TO_CATALOG_ID.get(k, "").lower() for k in KPI_API_TO_CATALOG_ID}
        supported = {k for k in supported if k}
        return sorted(supported)

    def get_exposed_aliases(self) -> dict[str, list[str]]:
        return {
            "PAR30": ["PAR30", "par_30"],
            "PAR60": ["PAR60", "par_60"],
            "PAR90": ["PAR90", "par_90"],
            "DPD1_30": ["DPD_1_30", "dpd_1_30"],
            "DPD31_60": ["DPD_31_60", "dpd_31_60"],
            "DPD61_90": ["DPD_61_90", "dpd_61_90"],
            "DPD90Plus": ["DPD_90_PLUS", "dpd_90_plus"],
            "CollectionRate": ["COLLECTION_RATE", "collections_rate"],
            "DefaultRate": ["DEFAULT_RATE", "default_rate"],
            "TotalLoansCount": ["TOTAL_LOANS_COUNT", "total_loans_count"],
            "LossRate": ["LOSS_RATE", "loss_rate"],
            "RecoveryRate": ["RECOVERY_RATE", "recovery_rate"],
            "CashOnHand": ["CASH_ON_HAND", "cash_on_hand"],
            "PortfolioHealth": ["AUM", "portfolio_growth_rate"],
            "CustomerLifetimeValue": ["CUSTOMER_LIFETIME_VALUE", "customer_lifetime_value"],
            "ActiveBorrowers": ["ACTIVE_BORROWERS", "active_borrowers"],
            "RepeatBorrowerRate": ["REPEAT_BORROWER_RATE", "repeat_borrower_rate"],
            "AutomationRate": ["AUTOMATION_RATE", "automation_rate"],
            "AverageLoanSize": ["AVERAGE_LOAN_SIZE", "average_loan_size"],
            "ProcessingTimeAvg": ["PROCESSING_TIME_AVG", "processing_time_avg"],
            "DisbursementVolumeMTD": ["DISBURSEMENT_VOLUME_MTD", "disbursement_volume_mtd"],
            "NewLoansCountMTD": ["NEW_LOANS_COUNT_MTD", "new_loans_count_mtd"],
            "CAC": ["CAC", "cac"],
            "GrossMarginPct": ["GROSS_MARGIN_PCT", "gross_margin_pct"],
            "RevenueForecast6M": ["REVENUE_FORECAST_6M", "revenue_forecast_6m"],
            "Churn90D": ["CHURN_90D", "churn_90d"],
            "LTV": ["AVG_LTV", "avg_ltv"],
            "DTI": ["AVG_DTI", "avg_dti"],
            "PortfolioYield": ["PORTFOLIO_YIELD", "portfolio_yield"],
            "NPL": ["NPL", "npl_ratio"],
            "LGD": ["LGD", "lgd_pct"],
            "CoR": ["COR", "cost_of_risk_pct"],
            "NIM": ["NIM", "nim_pct"],
            "CureRate": ["CURERATE", "cure_rate_pct"],
        }

    def _get_kpi_metadata(self, kpi_id: str, kpi_name: str | None = None) -> dict[str, Any]:
        normalized = _normalize_kpi_key(kpi_id)
        catalog_key = KPI_API_TO_CATALOG_ID.get(normalized, kpi_id.lower())
        catalog_metadata = _load_catalog_kpi_metadata().get(catalog_key, {})
        default_metadata: dict[str, Any] = DEFAULT_KPI_METADATA.get(normalized, {})
        definition_fallback = kpi_name or kpi_id
        thresholds = catalog_metadata.get("thresholds")
        if not isinstance(thresholds, dict):
            thresholds = {}
        if not thresholds:
            default_thresholds = default_metadata.get("thresholds")
            if isinstance(default_thresholds, dict):
                thresholds = {str(key): float(value) for key, value in default_thresholds.items()}
        benchmark = catalog_metadata.get("benchmark")
        if benchmark is None:
            benchmark = default_metadata.get("benchmark")
        if benchmark is None and "target" in thresholds:
            benchmark = thresholds.get("target")
        return {
            "formula": default_metadata.get("formula")
            or catalog_metadata.get("formula")
            or "Not available",
            "definition": default_metadata.get("definition")
            or catalog_metadata.get("definition")
            or f"KPI metric for {definition_fallback}",
            "implications": default_metadata.get("implications")
            or catalog_metadata.get("implications")
            or "Interpret with trend, segmentation, and risk appetite context.",
            "thresholds": thresholds,
            "benchmark": benchmark,
        }

    @staticmethod
    def _eval_higher_is_riskier(
        value: float, critical: float, warning: float, target: float | None
    ) -> Literal["below_target", "on_target", "warning", "critical"]:
        if value >= critical:
            return "critical"
        if value >= warning:
            return "warning"
        return "on_target" if target is None or value <= target else "below_target"

    @staticmethod
    def _eval_lower_is_riskier(
        value: float, critical: float, warning: float, target: float | None
    ) -> Literal["below_target", "on_target", "warning", "critical"]:
        if value <= critical:
            return "critical"
        if value <= warning:
            return "warning"
        return "on_target" if target is None or value >= target else "below_target"

    @staticmethod
    def _evaluate_kpi_status(
        value: float, thresholds: dict[str, float]
    ) -> Literal["below_target", "on_target", "warning", "critical", "unknown"]:
        if not thresholds:
            return "unknown"
        critical = thresholds.get("critical")
        warning = thresholds.get("warning")
        target = thresholds.get("target")
        if critical is not None and warning is not None:
            if critical > warning:
                return KPIService._eval_higher_is_riskier(value, critical, warning, target)
            if critical < warning:
                return KPIService._eval_lower_is_riskier(value, critical, warning, target)
        if target is not None:
            return "on_target" if value >= target else "below_target"
        return "unknown"

    def _build_kpi_single_response(
        self,
        *,
        kpi_id: str,
        name: str,
        value: float,
        unit: str,
        timestamp: datetime,
        sample_size: int,
        period: str,
        filters: dict[str, Any],
    ) -> KpiSingleResponse:
        metadata = self._get_kpi_metadata(kpi_id, name)
        formula = metadata["formula"]
        thresholds = metadata.get("thresholds")
        thresholds = thresholds if isinstance(thresholds, dict) else {}
        benchmark = metadata.get("benchmark")
        benchmark_value = float(benchmark) if isinstance(benchmark, (int, float)) else None
        rounded_value = round(value, 2)
        status = self._evaluate_kpi_status(rounded_value, thresholds)
        return KpiSingleResponse(
            id=kpi_id,
            name=name,
            value=rounded_value,
            unit=unit,
            status=status,
            threshold_status=self._to_threshold_status(status),
            benchmark=benchmark_value,
            thresholds=thresholds or None,
            formula=formula,
            definition=metadata["definition"],
            implications=metadata["implications"],
            context=KpiContext(
                metric=name,
                timestamp=timestamp,
                formula=formula,
                sample_size=sample_size,
                period=period,
                calculation_date=timestamp,
                filters=filters,
            ),
        )

    @staticmethod
    def _to_threshold_status(
        status: Literal["below_target", "on_target", "warning", "critical", "unknown"],
    ) -> Literal["normal", "warning", "critical", "not_configured"]:
        if status == "critical":
            return "critical"
        if status == "warning":
            return "warning"
        if status in {"on_target", "below_target"}:
            return "normal"
        return "not_configured"

    async def get_latest_kpis(self, kpi_keys: list[str] | None = None) -> list[KpiSingleResponse]:
        pool = await get_pool(settings.database_url)
        query = "\n            SELECT\n                v.kpi_name as id,\n                v.kpi_name as name,\n                v.kpi_value as value,\n                '%' as unit,\n                v.run_date as as_of_date,\n                v.timestamp as created_at\n            FROM public.kpi_timeseries_daily v\n            WHERE v.id IN (\n                SELECT MAX(id)\n                FROM public.kpi_timeseries_daily\n                GROUP BY kpi_name\n            )\n        "
        params = []
        if kpi_keys:
            query += " AND v.kpi_name = ANY($1)"
            params.append(kpi_keys)
        try:
            records = await pool.fetch(query, *params)
            responses = []
            for rec in records:
                kpi_id = str(rec["id"])
                kpi_name = str(rec["name"])
                as_of_date = rec["as_of_date"]
                if hasattr(as_of_date, "isoformat"):
                    as_of_date_str = as_of_date.isoformat()
                else:
                    as_of_date_str = str(as_of_date)
                responses.append(
                    self._build_kpi_single_response(
                        kpi_id=kpi_id,
                        name=kpi_name,
                        value=float(rec["value"]),
                        unit=rec["unit"],
                        timestamp=rec["created_at"],
                        sample_size=0,
                        period="latest",
                        filters={"as_of_date": as_of_date_str},
                    )
                )
            return responses
        except Exception as e:
            logger.error("Error fetching KPIs for actor %s: %s", self.actor, e, exc_info=True)
            raise

    async def get_kpi_by_id(self, kpi_id: str) -> KpiSingleResponse | None:
        kpis = await self.get_latest_kpis(kpi_keys=[kpi_id])
        return kpis[0] if kpis else None

    async def get_risk_alerts(
        self,
        loans: list[LoanRecord] | None,
        ltv_threshold: float = 80.0,
        dti_threshold: float = 50.0,
    ) -> list[dict]:
        try:
            if loans is None:
                return []
            df = await run_in_threadpool(self._convert_loan_records_to_dataframe, loans)
            if df.empty:
                return []
            df = self._calculate_loan_risk_metrics(df)
            high_risk_df = df[
                (df["ltv"] > ltv_threshold)
                | (df["dti"] > dti_threshold)
                | (df["days_past_due"] > 30)
                | df["ltv_insufficient"]
                | df["dti_insufficient"]
            ]
            return [
                self._build_loan_risk_alert(rec, ltv_threshold, dti_threshold)
                for _, rec in high_risk_df.iterrows()
            ]
        except Exception as e:
            logger.error(
                "Error calculating risk alerts for actor %s: %s", self.actor, e, exc_info=True
            )
            raise

    @staticmethod
    def _dpd_from_status(status: str) -> int:
        if "30-59" in status:
            return 45
        if "60-89" in status:
            return 75
        return 100 if "90+" in status else 0

    @staticmethod
    def _normalize_default_status(status_series: pd.Series) -> pd.Series:
        status = status_series.astype(str).str.strip().str.lower()
        return status.mask(
            status.str.contains(STATUS_PATTERN_DEFAULT, regex=True, na=False), "defaulted"
        )

    def _calculate_loan_risk_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        if "appraised_value" in df.columns and df["appraised_value"].notna().any():
            df["ltv"] = df["principal_balance"] / df["appraised_value"] * 100
            df["ltv_insufficient"] = False
        else:
            df["ltv"] = float("nan")
            df["ltv_insufficient"] = True
        if (
            "monthly_debt" in df.columns
            and "borrower_income" in df.columns
            and df["borrower_income"].notna().any()
        ):
            df["dti"] = df["monthly_debt"] / df["borrower_income"] * 100
            df["dti_insufficient"] = False
        else:
            df["dti"] = float("nan")
            df["dti_insufficient"] = True
        if "days_past_due" not in df.columns:
            df["days_past_due"] = df["loan_status"].apply(self._dpd_from_status)
        else:
            null_mask = df["days_past_due"].isna()
            if null_mask.any():
                df.loc[null_mask, "days_past_due"] = df.loc[null_mask, "loan_status"].apply(
                    self._dpd_from_status
                )
        return df

    def _build_loan_risk_alert(
        self, rec: pd.Series, ltv_threshold: float, dti_threshold: float
    ) -> dict:
        ltv = rec["ltv"]
        dti = rec["dti"]
        dpd = rec["days_past_due"]
        ltv_valid = not (pd.isna(ltv) or rec.get("ltv_insufficient", False))
        dti_valid = not (pd.isna(dti) or rec.get("dti_insufficient", False))
        ltv_score = (ltv / 100 * 0.3) if ltv_valid else 0.0
        dti_score = (dti / 100 * 0.3) if dti_valid else 0.0
        risk_score = ltv_score + dti_score + dpd / 100 * 0.4
        risk_score = min(100.0, risk_score * 100)
        alerts = []
        if not ltv_valid:
            alerts.append("LTV data insufficient — collateral valuation unavailable")
        elif ltv > ltv_threshold:
            alerts.append(f"LTV {ltv:.1f}% exceeds threshold {ltv_threshold}%")
        if not dti_valid:
            alerts.append("DTI data insufficient — income data unavailable")
        elif dti > dti_threshold:
            alerts.append(f"DTI {dti:.1f}% exceeds threshold {dti_threshold}%")
        if dpd > 30:
            alerts.append(f"DPD {dpd} indicates high credit risk")
        return {"loan_id": rec["id"], "risk_score": round(float(risk_score), 2), "alerts": alerts}

    def _convert_loan_records_to_dataframe(self, loans: list[LoanRecord]) -> pd.DataFrame:
        return pd.DataFrame([loan.model_dump() for loan in loans])

    def _convert_dict_records_to_dataframe(self, rows: list[dict] | None) -> pd.DataFrame:
        return pd.DataFrame(rows) if rows else pd.DataFrame()

    async def get_executive_analytics(
        self,
        loans: list[LoanRecord],
        payments: list[dict] | None = None,
        customers: list[dict] | None = None,
        schedule: list[dict] | None = None,
    ) -> dict:
        try:
            return await run_in_threadpool(
                self._calculate_executive_analytics_sync, loans, payments, customers, schedule
            )
        except Exception as e:
            logger.error(
                "Error generating executive analytics for actor %s: %s",
                self.actor,
                e,
                exc_info=True,
            )
            raise

    async def calculate_guardrails(
        self,
        loans: list[LoanRecord],
        payments: list[dict] | None = None,
        customers: list[dict] | None = None,
        schedule: list[dict] | None = None,
    ) -> dict:
        try:
            return await run_in_threadpool(
                self._calculate_guardrails_sync, loans, payments, customers, schedule
            )
        except Exception as e:
            logger.error(
                "Error calculating guardrails for actor %s: %s", self.actor, e, exc_info=True
            )
            raise

    def _calculate_guardrails_sync(
        self,
        loans: list[LoanRecord],
        payments: list[dict] | None = None,
        customers: list[dict] | None = None,
        schedule: list[dict] | None = None,
    ) -> dict:
        from datetime import timezone

        loans_df = self._convert_loan_records_to_dataframe(loans)
        payments_df = self._convert_dict_records_to_dataframe(payments)
        customers_df = self._convert_dict_records_to_dataframe(customers)
        schedule_df = self._convert_dict_records_to_dataframe(schedule)
        loans_df = self._normalize_loans_for_catalog(loans_df, payments_df, customers_df)
        processor = KPICatalogProcessor(
            loans_df=loans_df,
            payments_df=payments_df,
            customers_df=customers_df,
            schedule_df=schedule_df,
        )
        checks = processor.check_guardrails()
        any_breach = any(c.get("breach", False) for c in checks)
        breach_count = sum(1 for c in checks if c.get("breach", False))
        return {
            "generated_at": datetime.now(timezone.utc),
            "any_breach": any_breach,
            "breach_count": breach_count,
            "checks": checks,
        }

    def _calculate_executive_analytics_sync(
        self,
        loans: list[LoanRecord],
        payments: list[dict] | None = None,
        customers: list[dict] | None = None,
        schedule: list[dict] | None = None,
    ) -> dict:
        loans_df = self._convert_loan_records_to_dataframe(loans)
        payments_df = self._convert_dict_records_to_dataframe(payments)
        customers_df = self._convert_dict_records_to_dataframe(customers)
        schedule_df = self._convert_dict_records_to_dataframe(schedule)
        loans_df = self._normalize_loans_for_catalog(loans_df, payments_df, customers_df)
        processor = KPICatalogProcessor(
            loans_df=loans_df,
            payments_df=payments_df,
            customers_df=customers_df,
            schedule_df=schedule_df,
        )
        extended_kpis = processor.get_all_kpis()
        now = datetime.now()
        if loans_df.empty:
            risk_kpis: list[KpiSingleResponse] = []
            portfolio_health = PortfolioHealthScore(
                score=DATA_MISSING_SCORE,
                traffic_light="critical",
                components=[],
                formula=_PORTFOLIO_HEALTH_FORMULA,
                interpretation=DATA_MISSING_INTERPRETATION,
            )
        else:
            metrics = self._calculate_portfolio_performance_metrics(loans_df.copy())
            risk_kpis = self._build_risk_kpi_snapshot_from_metrics(
                metrics, sample_size=len(loans_df), timestamp=now
            )
            portfolio_health = self._build_portfolio_health_score_from_metrics(metrics)
        return {
            "strategic_confirmations": extended_kpis.get("strategic_confirmations", {}),
            "executive_strip": extended_kpis.get("executive_strip", {}),
            "nsm_customer_types": extended_kpis.get("nsm_customer_types", {}),
            "dpd_buckets": extended_kpis.get("dpd_buckets", {}),
            "concentration": extended_kpis.get("concentration", {}),
            "portfolio_rotation": extended_kpis.get("portfolio_rotation", {}),
            "monthly_pricing": extended_kpis.get("monthly_pricing", {}),
            "weighted_apr": float(extended_kpis.get("weighted_apr", 0.0) or 0.0),
            "weighted_fee_rate": float(extended_kpis.get("weighted_fee_rate", 0.0) or 0.0),
            "churn_90d_metrics": extended_kpis.get("churn_90d_metrics", []),
            "unit_economics": extended_kpis.get("unit_economics", []),
            "pricing_analytics": extended_kpis.get("pricing_analytics", {}),
            "revenue_forecast_6m": extended_kpis.get("revenue_forecast_6m", []),
            "opportunity_prioritization": extended_kpis.get("opportunity_prioritization", []),
            "data_governance": extended_kpis.get("data_governance", {}),
            "graph_analytics": extended_kpis.get("graph_analytics", {}),
            "portfolio_analytics": extended_kpis.get("portfolio_analytics", {}),
            "lending_kpis": extended_kpis.get("lending_kpis", {}),
            "risk_kpis": risk_kpis,
            "portfolio_health": portfolio_health,
        }

    @staticmethod
    def _empty_portfolio_health_score() -> PortfolioHealthScore:
        return PortfolioHealthScore(
            score=DATA_MISSING_SCORE,
            traffic_light="critical",
            components=[],
            formula=_PORTFOLIO_HEALTH_FORMULA,
            interpretation=DATA_MISSING_INTERPRETATION,
        )

    def _build_risk_kpi_snapshot_from_metrics(
        self, metrics: dict[str, float], *, sample_size: int, timestamp: datetime
    ) -> list[KpiSingleResponse]:
        snapshot_defs = [
            ("PAR30", "Portfolio at Risk (30+ days)", metrics["par30"], "%"),
            ("PAR60", "Portfolio at Risk (60+ days)", metrics["par60"], "%"),
            ("PAR90", "Portfolio at Risk (90+ days)", metrics["par90"], "%"),
            ("DEFAULT_RATE", "Default Rate", metrics["default_rate"], "%"),
            ("NPL", "Non-Performing Loans", metrics["npl"], "%"),
            ("LGD", "Loss Given Default", metrics["lgd"], "%"),
            ("COR", "Cost of Risk", metrics["cor"], "%"),
            ("COLLECTION_RATE", "Collection Rate", metrics["collection_rate"], "%"),
        ]
        return [
            self._build_kpi_single_response(
                kpi_id=kpi_id,
                name=name,
                value=value,
                unit=unit,
                timestamp=timestamp,
                sample_size=sample_size,
                period="on-demand",
                filters={"loan_count": sample_size},
            )
            for kpi_id, name, value, unit in snapshot_defs
        ]

    def _build_portfolio_health_score_from_metrics(
        self, metrics: dict[str, float]
    ) -> PortfolioHealthScore:
        required_metrics = ("par30", "collection_rate", "npl", "cor", "default_rate")
        if missing := ", ".join((name for name in required_metrics if name not in metrics)):
            raise ValueError(f"Missing required portfolio health metrics: {missing}")
        payload = calculate_portfolio_health_score(
            par30=float(metrics["par30"]),
            collection_rate=float(metrics["collection_rate"]),
            npl=float(metrics["npl"]),
            cost_of_risk=float(metrics["cor"]),
            default_rate=float(metrics["default_rate"]),
        )
        components = [PortfolioHealthComponent(**item) for item in payload.get("components", [])]
        traffic_light_value = str(payload.get("traffic_light", "critical"))
        if traffic_light_value not in {"healthy", "at_risk", "warning", "critical"}:
            traffic_light_value = "critical"
        return PortfolioHealthScore(
            score=float(payload.get("score", 0.0)),
            traffic_light=cast(
                Literal["healthy", "at_risk", "warning", "critical"], traffic_light_value
            ),
            components=components,
            formula=str(payload.get("formula", "")),
            interpretation=str(payload.get("interpretation", "")),
        )

    async def get_portfolio_health_score(
        self, loans: list[LoanRecord] | None
    ) -> PortfolioHealthScore:
        if not loans:
            return self._empty_portfolio_health_score()
        df = await run_in_threadpool(self._convert_loan_records_to_dataframe, loans)
        if df.empty:
            return self._empty_portfolio_health_score()
        metrics = self._calculate_portfolio_performance_metrics(df)
        return self._build_portfolio_health_score_from_metrics(metrics)

    async def get_decision_dashboard(
        self, loans: list[LoanRecord] | None
    ) -> DecisionDashboardResponse:
        if not loans:
            raise ValueError("Decision dashboard requires loan data.")
        health = await self.get_portfolio_health_score(loans)
        risk_stratification = await self.get_risk_stratification(loans)
        heatmap_raw = await self.get_risk_heatmap_summary(loans)
        risk_heatmap = RiskHeatmapResponse(**heatmap_raw)
        unit_economics = await self.calculate_unit_economics(loans)
        kpis = await self.calculate_kpis_for_portfolio(loans)
        recommendations: list[str] = []
        if health.traffic_light in {"critical", "warning"}:
            recommendations.append(
                "Prioritize remediation on the weakest health-score components this week."
            )
        if red_flags := [
            flag.flag for flag in risk_stratification.decision_flags if flag.status == "red"
        ]:
            recommendations.append(f"Escalate red risk flags to committee: {', '.join(red_flags)}.")
        if not recommendations:
            recommendations.append(
                "Maintain current strategy and monitor trend deltas in PAR and collections."
            )
        return DecisionDashboardResponse(
            generated_at=datetime.now(),
            portfolio_health=health,
            risk_stratification=risk_stratification,
            risk_heatmap=risk_heatmap,
            unit_economics=unit_economics,
            kpis=kpis,
            recommendations=recommendations,
        )

    def _normalize_loans_for_catalog(
        self, loans_df: pd.DataFrame, payments_df: pd.DataFrame, customers_df: pd.DataFrame
    ) -> pd.DataFrame:
        if loans_df.empty:
            return loans_df
        normalized = loans_df.copy()
        normalized = self._apply_balance_aliases(normalized)
        normalized = self._apply_entity_identifiers(normalized)
        normalized = self._apply_segment_date_defaults(normalized)
        normalized = self._apply_customer_mapping(normalized, payments_df, customers_df)
        return normalized

    def _apply_balance_aliases(self, df: pd.DataFrame) -> pd.DataFrame:
        if "principal_balance" in df.columns and "outstanding_balance" not in df.columns:
            df["outstanding_balance"] = pd.to_numeric(
                df["principal_balance"], errors="coerce"
            ).fillna(0)
        if "loan_amount" in df.columns and "principal_amount" not in df.columns:
            df["principal_amount"] = pd.to_numeric(df["loan_amount"], errors="coerce").fillna(0)
        if "interest_rate" in df.columns and "interest_rate_apr" not in df.columns:
            df["interest_rate_apr"] = pd.to_numeric(df["interest_rate"], errors="coerce").fillna(0)
        return df

    def _apply_entity_identifiers(self, df: pd.DataFrame) -> pd.DataFrame:
        if "id" in df.columns and "loan_id" not in df.columns:
            df["loan_id"] = df["id"].fillna("")
        if "loan_id" not in df.columns:
            df["loan_id"] = [f"loan-{idx + 1}" for idx in range(len(df))]
        return df

    def _apply_segment_date_defaults(self, df: pd.DataFrame) -> pd.DataFrame:
        if "client_segment" not in df.columns:
            df["client_segment"] = "general"
        if "origination_date" not in df.columns:
            df["origination_date"] = pd.Timestamp.now().floor("D")
        return df

    def _apply_customer_mapping(
        self, df: pd.DataFrame, payments_df: pd.DataFrame, customers_df: pd.DataFrame
    ) -> pd.DataFrame:
        if "customer_id" in df.columns:
            return df
        customer_ids: list[str] = []
        if not customers_df.empty and "customer_id" in customers_df.columns:
            customer_ids = customers_df["customer_id"].astype(str).dropna().unique().tolist()
        elif not payments_df.empty and "customer_id" in payments_df.columns:
            customer_ids = payments_df["customer_id"].astype(str).dropna().unique().tolist()
        if customer_ids:
            df["customer_id"] = [customer_ids[idx % len(customer_ids)] for idx in range(len(df))]
        else:
            df["customer_id"] = [f"cust-{idx + 1}" for idx in range(len(df))]
        return df

    async def get_data_quality_profile(self, loans: list[LoanRecord] | None) -> DataQualityResponse:
        try:
            if loans is None:
                return DataQualityResponse(
                    duplicate_ratio=0.0,
                    average_null_ratio=0.0,
                    invalid_numeric_ratio=0.0,
                    data_quality_score=0.0,
                    issues=["No data provided for real-time profiling. Quality score unavailable."],
                )
            df = await run_in_threadpool(self._convert_loan_records_to_dataframe, loans)
            if df.empty:
                return DataQualityResponse(
                    duplicate_ratio=0.0,
                    average_null_ratio=0.0,
                    invalid_numeric_ratio=0.0,
                    data_quality_score=0.0,
                    issues=["Input dataset is empty. Quality score unavailable."],
                )
            metrics = self._calculate_data_quality_metrics(df)
            return DataQualityResponse(**metrics)
        except Exception as e:
            logger.error(
                "Error calculating data quality profile for actor %s: %s",
                self.actor,
                e,
                exc_info=True,
            )
            raise

    def _calculate_data_quality_metrics(self, df: pd.DataFrame) -> dict:
        total_records = len(df)
        duplicate_ratio = df.duplicated().sum() / total_records * 100.0
        all_loan_record_columns = LoanRecord.model_fields.keys()
        null_counts = df[list(all_loan_record_columns)].isnull().sum()
        average_null_ratio = (
            null_counts.sum() / (total_records * len(all_loan_record_columns)) * 100.0
        )
        invalid_numeric_ratio = 0.0
        data_quality_score = max(0.0, 100.0 - (duplicate_ratio * 0.5 + average_null_ratio * 0.5))
        issues = []
        if duplicate_ratio > 0:
            issues.append(f"Duplicate records found: {duplicate_ratio:.2f}%")
        if average_null_ratio > 0:
            issues.append(f"Average null values across columns: {average_null_ratio:.2f}%")
        return {
            "duplicate_ratio": round(duplicate_ratio, 2),
            "average_null_ratio": round(average_null_ratio, 2),
            "invalid_numeric_ratio": round(invalid_numeric_ratio, 2),
            "data_quality_score": round(data_quality_score, 2),
            "issues": issues,
        }

    @staticmethod
    def _float_field_error(field_name: str, series: pd.Series) -> str | None:
        return (
            None
            if pd.api.types.is_numeric_dtype(series)
            else f"Column '{field_name}' is not numeric."
        )

    @staticmethod
    def _str_field_error(field_name: str, series: pd.Series) -> str | None:
        return (
            None
            if pd.api.types.is_string_dtype(series)
            else f"Column '{field_name}' is not string type."
        )

    @staticmethod
    def _datetime_field_error(field_name: str, series: pd.Series) -> str | None:
        try:
            pd.to_datetime(series, errors="raise")
            return None
        except Exception:
            return f"Column '{field_name}' contains invalid datetime format."

    @staticmethod
    def _field_type_error(field_name: str, field_info: Any, series: pd.Series) -> str | None:
        validators = {
            float: KPIService._float_field_error,
            str: KPIService._str_field_error,
            datetime: KPIService._datetime_field_error,
        }
        validator = validators.get(field_info.annotation)
        return validator(field_name, series) if validator is not None else None

    @staticmethod
    def _collect_field_type_errors(df: pd.DataFrame) -> list[str]:
        errors: list[str] = []
        for field_name, field_info in LoanRecord.model_fields.items():
            if field_name not in df.columns:
                continue
            if error := KPIService._field_type_error(field_name, field_info, df[field_name]):
                errors.append(error)
        return errors

    async def validate_loan_portfolio_schema(
        self, loans: list[LoanRecord] | None
    ) -> ValidationResponse:
        try:
            if loans is None:
                return ValidationResponse(valid=True, message="No loans provided to validate.")
            df = await run_in_threadpool(self._convert_loan_records_to_dataframe, loans)
            errors: list[str] = []
            required_columns = list(LoanRecord.model_fields.keys())
            missing_cols = [col for col in required_columns if col not in df.columns]
            if missing_cols:
                errors.append(f"Missing required columns: {', '.join(missing_cols)}")
            errors.extend(self._collect_field_type_errors(df))
            if errors:
                return ValidationResponse(valid=False, errors=errors)
            return ValidationResponse(valid=True)
        except Exception as e:
            logger.error(
                "Error validating loan portfolio schema for actor %s: %s",
                self.actor,
                e,
                exc_info=True,
            )
            raise

    async def calculate_kpis_for_portfolio(
        self, loans: list[LoanRecord] | None
    ) -> list[KpiSingleResponse]:
        try:
            if loans is None:
                return []
            df = await run_in_threadpool(self._convert_loan_records_to_dataframe, loans)
            if df.empty:
                return []
            numeric_cols = ["loan_amount", "principal_balance", "interest_rate"]
            for col in numeric_cols:
                df[col] = pd.to_numeric(df[col], errors="coerce")
            df.dropna(subset=numeric_cols, inplace=True)
            if df.empty:
                return []
            results = self._calculate_portfolio_performance_metrics(df)
            roll_rates = await self.calculate_roll_rate_analytics(loans)
            cure_rate = roll_rates.summary.portfolio_cure_rate_pct
            lgd_data = calculate_lgd(df)
            cor_data = calculate_cost_of_risk(df)
            nim_data = calculate_nim(df)
            now = datetime.now()

            def build_kpi_response(
                kpi_id: str, name: str, value: float, unit: str
            ) -> KpiSingleResponse:
                return self._build_kpi_single_response(
                    kpi_id=kpi_id,
                    name=name,
                    value=value,
                    unit=unit,
                    timestamp=now,
                    sample_size=len(loans),
                    period="on-demand",
                    filters={"loan_count": len(loans)},
                )

            return [
                build_kpi_response("PAR30", "Portfolio at Risk (30+ days)", results["par30"], "%"),
                build_kpi_response("PAR60", "Portfolio at Risk (60+ days)", results["par60"], "%"),
                build_kpi_response("PAR90", "Portfolio at Risk (90+ days)", results["par90"], "%"),
                build_kpi_response("DPD_1_30", "DPD Bucket (1-30 days)", results["dpd_1_30"], "%"),
                build_kpi_response(
                    "DPD_31_60", "DPD Bucket (31-60 days)", results["dpd_31_60"], "%"
                ),
                build_kpi_response(
                    "DPD_61_90", "DPD Bucket (61-90 days)", results["dpd_61_90"], "%"
                ),
                build_kpi_response(
                    "DPD_90_PLUS", "DPD Bucket (90+ days)", results["dpd_90_plus"], "%"
                ),
                build_kpi_response(
                    "COLLECTION_RATE", "Collection Rate", results["collection_rate"], "%"
                ),
                build_kpi_response("LOSS_RATE", "Loss Rate", results["loss_rate"], "%"),
                build_kpi_response("RECOVERY_RATE", "Recovery Rate", results["recovery_rate"], "%"),
                build_kpi_response("NPL", "Non-Performing Loans", results["npl"], "%"),
                build_kpi_response("NPL_90", "Non-Performing Loans (90+ DPD)", results["npl_90"], "%"),
                build_kpi_response("LGD", "Loss Given Default", lgd_data["lgd_pct"], "%"),
                build_kpi_response("COR", "Cost of Risk", cor_data["cost_of_risk_pct"], "%"),
                build_kpi_response("CURERATE", "Cure Rate", cure_rate, "%"),
                build_kpi_response("NIM", "Net Interest Margin", nim_data["nim_pct"], "%"),
                build_kpi_response(
                    "collections_eligible_rate",
                    "Collections Eligible Rate",
                    results["collections_eligible_rate"],
                    "%",
                ),
                build_kpi_response(
                    "government_sector_exposure_rate",
                    "Government Sector Exposure Rate",
                    results["government_sector_exposure_rate"],
                    "%",
                ),
                build_kpi_response(
                    "avg_credit_line_utilization",
                    "Average Credit Line Utilization",
                    results["avg_credit_line_utilization"],
                    "%",
                ),
                build_kpi_response(
                    "capital_collection_rate",
                    "Capital Collection Rate",
                    results["capital_collection_rate"],
                    "%",
                ),
                build_kpi_response(
                    "mdsc_posted_rate", "MDSC Posted Rate", results["mdsc_posted_rate"], "%"
                ),
                build_kpi_response("CASH_ON_HAND", "Cash on Hand", results["cash_on_hand"], "USD"),
                build_kpi_response(
                    "PORTFOLIO_YIELD", "Weighted Average Interest Rate", results["yield"] * 100, "%"
                ),
                build_kpi_response("AUM", "Assets Under Management", results["aum"], "USD"),
                build_kpi_response(
                    "AVERAGE_LOAN_SIZE", "Average Loan Size", results["average_loan_size"], "USD"
                ),
                build_kpi_response(
                    "DISBURSEMENT_VOLUME_MTD",
                    "Disbursement Volume MTD",
                    results["disbursement_volume_mtd"],
                    "USD",
                ),
                build_kpi_response(
                    "NEW_LOANS_COUNT_MTD",
                    "New Loans Count MTD",
                    results["new_loans_count_mtd"],
                    "count",
                ),
                build_kpi_response(
                    "CUSTOMER_LIFETIME_VALUE",
                    "Customer Lifetime Value",
                    results["customer_lifetime_value"],
                    "USD",
                ),
                build_kpi_response("CAC", "Customer Acquisition Cost", results["cac"], "USD"),
                build_kpi_response(
                    "GROSS_MARGIN_PCT", "Gross Margin %", results["gross_margin_pct"], "%"
                ),
                build_kpi_response(
                    "REVENUE_FORECAST_6M",
                    "Revenue Forecast (6M)",
                    results["revenue_forecast_6m"],
                    "USD",
                ),
                build_kpi_response("CHURN_90D", "90-Day Churn Rate", results["churn_90d"], "%"),
                build_kpi_response("AVG_LTV", "Average Loan-to-Value", results["avg_ltv"], "%"),
                build_kpi_response("AVG_DTI", "Average Debt-to-Income", results["avg_dti"], "%"),
                build_kpi_response("DEFAULT_RATE", "Default Rate", results["default_rate"], "%"),
                build_kpi_response(
                    "ACTIVE_BORROWERS", "Active Borrowers", results["active_borrowers"], "count"
                ),
                build_kpi_response(
                    "REPEAT_BORROWER_RATE",
                    "Repeat Borrower Rate",
                    results["repeat_borrower_rate"],
                    "%",
                ),
                build_kpi_response(
                    "AUTOMATION_RATE", "Automation Rate", results["automation_rate"], "%"
                ),
                build_kpi_response(
                    "PROCESSING_TIME_AVG",
                    "Average Processing Time",
                    results["processing_time_avg"],
                    "months",
                ),
                build_kpi_response(
                    "TOTAL_LOANS_COUNT", "Total Loans Count", results["count"], "count"
                ),
            ]
        except Exception as e:
            logger.error(
                "Error calculating real-time KPIs for actor %s: %s", self.actor, e, exc_info=True
            )
            raise

    async def calculate_advanced_risk(self, loans: list[LoanRecord] | None) -> AdvancedRiskResponse:
        try:
            if loans is None:
                return AdvancedRiskResponse(**calculate_advanced_risk_metrics(pd.DataFrame()))
            df = await run_in_threadpool(self._convert_loan_records_to_dataframe, loans)
            metrics = await run_in_threadpool(calculate_advanced_risk_metrics, df)
            return AdvancedRiskResponse(**metrics)
        except Exception as e:
            logger.error(
                "Error calculating advanced risk metrics for actor %s: %s",
                self.actor,
                e,
                exc_info=True,
            )
            raise

    async def calculate_unit_economics(
        self,
        loans: list[LoanRecord] | None,
        funding_cost_rate: float = 0.08,
        cac: float = 0.0,
        monthly_arpu: float = 0.0,
    ) -> UnitEconomicsResponse:
        try:
            if loans is None:
                loans = []
            return await run_in_threadpool(
                self._calculate_unit_economics_sync, loans, funding_cost_rate, cac, monthly_arpu
            )
        except Exception as e:
            logger.error(
                "Error calculating unit economics for actor %s: %s", self.actor, e, exc_info=True
            )
            raise

    def _calculate_unit_economics_sync(
        self, loans: list[LoanRecord], funding_cost_rate: float, cac: float, monthly_arpu: float
    ) -> UnitEconomicsResponse:
        df = self._convert_loan_records_to_dataframe(loans)
        raw = calculate_all_unit_economics(df, funding_cost_rate, cac, monthly_arpu)

        def _normalize_dpd_bucket_dict(bucket: Dict[str, Any]) -> Dict[str, Any]:
            normalized = dict(bucket)
            for key in ("dpd_bucket", "bucket"):
                value = normalized.get(key)
                if isinstance(value, str) and value.startswith("dpd_"):
                    normalized[key] = value[len("dpd_") :]
            return normalized

        dpd_migration = [
            DPDBucketWithAction(**_normalize_dpd_bucket_dict(bucket))
            for bucket in raw["dpd_migration"]
        ]
        logger.info(
            "Unit economics calculated for actor=%s, loans=%d, npl=%.4f%%",
            self.actor,
            len(loans),
            raw["npl"].get("npl_ratio", 0.0),
        )
        return UnitEconomicsResponse(
            generated_at=datetime.now(),
            npl=NplMetrics(**raw["npl"]),
            lgd=LgdMetrics(**raw["lgd"]),
            cost_of_risk=CostOfRiskMetrics(**raw["cost_of_risk"]),
            nim=NimMetrics(**raw["nim"]),
            payback=PaybackMetrics(**raw["payback"]),
            cure_rate=CureRateMetrics(**raw["cure_rate"]),
            dpd_migration=dpd_migration,
        )

    async def calculate_cohort_analytics(
        self, loans: list[LoanRecord] | None
    ) -> CohortAnalyticsResponse:
        try:
            if loans is None:
                loans = []
            return await run_in_threadpool(self._calculate_cohort_analytics_sync, loans)
        except Exception as e:
            logger.error(
                "Error calculating cohort analytics for actor %s: %s", self.actor, e, exc_info=True
            )
            raise

    def _calculate_cohort_analytics_sync(self, loans: list[LoanRecord]) -> CohortAnalyticsResponse:
        df = self._convert_loan_records_to_dataframe(loans)
        if df.empty:
            return CohortAnalyticsResponse(
                generated_at=datetime.now(),
                cohorts=[],
                summary=CohortAnalyticsSummary(
                    cohort_count=0,
                    total_loans=0,
                    weighted_par30_pct=0.0,
                    highest_risk_cohort=None,
                    strongest_collection_cohort=None,
                ),
            )
        df = df.copy()
        df["loan_amount"] = pd.to_numeric(df["loan_amount"], errors="coerce").fillna(0.0)
        df["principal_balance"] = pd.to_numeric(df["principal_balance"], errors="coerce").fillna(
            0.0
        )
        origination_raw = (
            pd.to_datetime(df["origination_date"], errors="coerce", utc=True).dt.tz_convert(None)
            if "origination_date" in df.columns
            else pd.Series([pd.Timestamp.now()] * len(df), index=df.index)
        )
        month_fallback = pd.Timestamp.now().replace(day=1).normalize()
        df["cohort_month"] = origination_raw.fillna(month_fallback).dt.to_period("M").astype(str)
        if "days_past_due" in df.columns:
            dpd = pd.to_numeric(df["days_past_due"], errors="coerce").fillna(0.0).clip(lower=0)
        else:
            status = df.get("loan_status", pd.Series([""] * len(df))).astype(str).str.lower()
            dpd = pd.Series([0.0] * len(df), index=df.index, dtype=float)
            dpd = dpd.mask(status.str.contains(STATUS_PATTERN_90_PLUS, regex=True, na=False), 100.0)
            dpd = dpd.mask(status.str.contains(STATUS_PATTERN_60_89, regex=True, na=False), 75.0)
            dpd = dpd.mask(status.str.contains(STATUS_PATTERN_30_59, regex=True, na=False), 45.0)
        status_series = self._normalize_default_status(
            df.get("loan_status", pd.Series([""] * len(df), index=df.index))
        )
        default_mask = status_series.eq("defaulted")
        status_series = df.get("loan_status", pd.Series([""] * len(df))).astype(str).str.lower()
        default_mask = status_series.str.contains(STATUS_PATTERN_DEFAULT, regex=True, na=False)
        collected = (
            pd.to_numeric(df["last_payment_amount"], errors="coerce").fillna(0.0)
            if "last_payment_amount" in df.columns
            else pd.Series([0.0] * len(df), index=df.index)
        )
        scheduled = (
            pd.to_numeric(df["total_scheduled"], errors="coerce").fillna(0.0)
            if "total_scheduled" in df.columns
            else pd.Series([0.0] * len(df), index=df.index)
        )
        cohort_rows: list[CohortMetrics] = []
        for cohort_month, group_idx in df.groupby("cohort_month").groups.items():
            idx = list(group_idx)
            group_balance = float(df.loc[idx, "principal_balance"].sum())
            group_originated = float(df.loc[idx, "loan_amount"].sum())
            group_loans = len(idx)
            par30 = self._safe_pct(
                df.loc[idx, "principal_balance"][dpd.loc[idx] > 30].sum(), group_balance
            )
            par90 = self._safe_pct(
                df.loc[idx, "principal_balance"][dpd.loc[idx] > 90].sum(), group_balance
            )
            default_rate = self._safe_pct(float(default_mask.loc[idx].sum()), group_loans)
            collection_rate = self._safe_pct(
                float(collected.loc[idx].sum()), float(scheduled.loc[idx].sum())
            )
            cohort_rows.append(
                CohortMetrics(
                    cohort_month=str(cohort_month),
                    loan_count=group_loans,
                    originated_amount_usd=round(group_originated, 2),
                    outstanding_amount_usd=round(group_balance, 2),
                    par30_pct=round(par30, 2),
                    par90_pct=round(par90, 2),
                    default_rate_pct=round(default_rate, 2),
                    collection_rate_pct=round(collection_rate, 2),
                )
            )
        cohort_rows.sort(key=lambda row: row.cohort_month)
        total_outstanding = sum((row.outstanding_amount_usd for row in cohort_rows))
        weighted_par30 = (
            sum((row.par30_pct * row.outstanding_amount_usd for row in cohort_rows))
            / total_outstanding
            if total_outstanding > 0
            else 0.0
        )
        highest_risk = (
            max(cohort_rows, key=lambda row: row.par90_pct).cohort_month if cohort_rows else None
        )
        strongest_collection = (
            max(cohort_rows, key=lambda row: row.collection_rate_pct).cohort_month
            if cohort_rows
            else None
        )
        summary = CohortAnalyticsSummary(
            cohort_count=len(cohort_rows),
            total_loans=len(df),
            weighted_par30_pct=round(weighted_par30, 2),
            highest_risk_cohort=highest_risk,
            strongest_collection_cohort=strongest_collection,
        )
        return CohortAnalyticsResponse(
            generated_at=datetime.now(), cohorts=cohort_rows, summary=summary
        )

    async def calculate_vintage_curves(self, loans: list[LoanRecord]) -> VintageCurveResponse:
        return await run_in_threadpool(self._calculate_vintage_curves_sync, loans)

    @staticmethod
    def _resolve_vintage_dpd(df: pd.DataFrame) -> "pd.Series[float]":
        if "days_past_due" in df.columns:
            return pd.to_numeric(df["days_past_due"], errors="coerce").fillna(0.0)
        status = df.get("loan_status", pd.Series([""] * len(df))).astype(str).str.lower()
        dpd = pd.Series([0.0] * len(df), index=df.index)
        dpd = dpd.mask(status.str.contains("90\\+|default", na=False), 100.0)
        dpd = dpd.mask(status.str.contains("30-89|30\\+", na=False), 45.0)
        return dpd

    @staticmethod
    def _build_vintage_curve_point(group: pd.DataFrame, mob_val: int) -> VintageCurvePoint:
        loan_count = len(group)
        npl_ratio = float(group["is_npl"].sum()) / loan_count * 100 if loan_count > 0 else 0.0
        cum_default = float(group["is_default"].sum()) / loan_count * 100 if loan_count > 0 else 0.0
        return VintageCurvePoint(
            months_on_book=mob_val,
            cumulative_default_rate=round(cum_default, 2),
            npl_ratio=round(npl_ratio, 2),
            loan_count=loan_count,
        )

    def _calculate_vintage_curves_sync(self, loans: list[LoanRecord]) -> VintageCurveResponse:
        df = self._convert_loan_records_to_dataframe(loans)
        if df.empty:
            return VintageCurveResponse(
                generated_at=datetime.now(), curves={}, portfolio_average_curve=[]
            )
        df = df.copy()
        now = pd.Timestamp.now().normalize()
        origination = pd.to_datetime(df["origination_date"], errors="coerce").dt.tz_localize(None)
        if origination.isna().any():
            missing_count = int(origination.isna().sum())
            logger.warning(
                "Vintage curves: dropping %d loans missing origination_date", missing_count
            )
            keep_mask = origination.notna()
            df = df.loc[keep_mask].copy()
            origination = origination.loc[keep_mask]
            if df.empty:
                return VintageCurveResponse(
                    generated_at=datetime.now(), curves={}, portfolio_average_curve=[]
                )
        df["origination"] = origination
        df["cohort"] = df["origination"].dt.to_period("M").astype(str)
        df["mob"] = (
            (now.year - df["origination"].dt.year) * 12 + (now.month - df["origination"].dt.month)
        ).clip(lower=0)
        dpd = self._resolve_vintage_dpd(df)
        status_source = (
            df["loan_status"]
            if "loan_status" in df.columns
            else pd.Series([""] * len(df), index=df.index)
        )
        df["is_npl"] = (dpd > 90) | status_source.str.contains("default", case=False, na=False)
        df["is_default"] = status_source.str.contains("default", case=False, na=False)
        curves: Dict[str, List[VintageCurvePoint]] = {
            str(cohort): [
                self._build_vintage_curve_point(group, self._safe_int(group["mob"].iloc[0]))
            ]
            for cohort, group in df.groupby("cohort")
        }
        avg_curve: List[VintageCurvePoint] = [
            self._build_vintage_curve_point(group, self._safe_int(mob))
            for mob, group in df.groupby("mob")
        ]
        avg_curve.sort(key=lambda x: x.months_on_book)
        return VintageCurveResponse(
            generated_at=datetime.now(), curves=curves, portfolio_average_curve=avg_curve
        )

    async def calculate_stress_test(
        self,
        loans: list[LoanRecord] | None,
        par_deterioration_pct: float = 25.0,
        collection_efficiency_pct: float = -10.0,
        recovery_efficiency_pct: float = -15.0,
        funding_cost_bps: float = 150.0,
    ) -> StressTestResponse:
        try:
            if loans is None:
                loans = []
            return await run_in_threadpool(
                self._calculate_stress_test_sync,
                loans,
                par_deterioration_pct,
                collection_efficiency_pct,
                recovery_efficiency_pct,
                funding_cost_bps,
            )
        except Exception as e:
            logger.error(
                "Error calculating stress test for actor %s: %s", self.actor, e, exc_info=True
            )
            raise

    async def calculate_segment_analytics(
        self, loans: list[LoanRecord] | None, dimension: str = "risk_band", top_n: int = 20
    ) -> SegmentAnalyticsResponse:
        try:
            return await run_in_threadpool(
                self._calculate_segment_analytics_sync, loans or [], dimension, top_n
            )
        except Exception as e:
            logger.error(
                "Error calculating segment analytics for actor %s: %s", self.actor, e, exc_info=True
            )
            raise

    def _calculate_segment_analytics_sync(
        self, loans: list[LoanRecord], dimension: str, top_n: int
    ) -> SegmentAnalyticsResponse:
        df = self._convert_loan_records_to_dataframe(loans)
        if df.empty:
            return SegmentAnalyticsResponse(
                generated_at=datetime.now(),
                segments=[],
                summary=SegmentAnalyticsSummary(
                    dimension=dimension,
                    segment_count=0,
                    total_loans=0,
                    largest_segment=None,
                    riskiest_segment=None,
                ),
            )
        df = df.copy()
        df["principal_balance"] = pd.to_numeric(df["principal_balance"], errors="coerce").fillna(
            0.0
        )
        df["interest_rate"] = pd.to_numeric(df["interest_rate"], errors="coerce").fillna(0.0)
        if "loan_amount" in df.columns:
            df["loan_amount"] = pd.to_numeric(df["loan_amount"], errors="coerce").fillna(0.0)
        else:
            df["loan_amount"] = df["principal_balance"]
        if "days_past_due" in df.columns:
            dpd = pd.to_numeric(df["days_past_due"], errors="coerce").fillna(0.0).clip(lower=0)
        else:
            status = df.get("loan_status", pd.Series([""] * len(df))).astype(str).str.lower()
            dpd = pd.Series([0.0] * len(df), index=df.index, dtype=float)
            dpd = dpd.mask(status.str.contains(STATUS_PATTERN_90_PLUS, regex=True, na=False), 100.0)
            dpd = dpd.mask(status.str.contains(STATUS_PATTERN_60_89, regex=True, na=False), 75.0)
            dpd = dpd.mask(status.str.contains(STATUS_PATTERN_30_59, regex=True, na=False), 45.0)
        default_mask = self._normalize_default_status(
            df.get("loan_status", pd.Series([""] * len(df), index=df.index))
        )
        default_mask = default_mask.eq("defaulted")
        default_mask = (
            df.get("loan_status", pd.Series([""] * len(df)))
            .astype(str)
            .str.contains(STATUS_PATTERN_DEFAULT, regex=True, case=False, na=False)
        )
        collected = (
            pd.to_numeric(df["last_payment_amount"], errors="coerce").fillna(0.0)
            if "last_payment_amount" in df.columns
            else pd.Series([0.0] * len(df), index=df.index)
        )
        scheduled = (
            pd.to_numeric(df["total_scheduled"], errors="coerce").fillna(0.0)
            if "total_scheduled" in df.columns
            else pd.Series([0.0] * len(df), index=df.index)
        )
        segments = self._build_segment_dimension(df, dpd, dimension)
        df["segment_value"] = segments.fillna("unknown").astype(str)
        segment_rows: list[SegmentMetrics] = []
        for segment_value, group_idx in df.groupby("segment_value").groups.items():
            idx = list(group_idx)
            outstanding = float(df.loc[idx, "principal_balance"].sum())
            loan_count = len(idx)
            par30 = self._safe_pct(
                df.loc[idx, "principal_balance"][dpd.loc[idx] >= 30].sum(), outstanding
            )
            par60 = self._safe_pct(
                df.loc[idx, "principal_balance"][dpd.loc[idx] >= 60].sum(), outstanding
            )
            par90 = self._safe_pct(
                df.loc[idx, "principal_balance"][dpd.loc[idx] >= 90].sum(), outstanding
            )
            default_rate = self._safe_pct(float(default_mask.loc[idx].sum()), loan_count)
            collection_rate = self._safe_pct(
                float(collected.loc[idx].sum()), float(scheduled.loc[idx].sum())
            )
            avg_rate = float(df.loc[idx, "interest_rate"].mean()) * 100.0
            segment_rows.append(
                SegmentMetrics(
                    segment=str(segment_value),
                    loan_count=loan_count,
                    outstanding_usd=round(outstanding, 2),
                    par30_pct=round(par30, 2),
                    par60_pct=round(par60, 2),
                    par90_pct=round(par90, 2),
                    default_rate_pct=round(default_rate, 2),
                    avg_interest_rate_pct=round(avg_rate, 2),
                    collection_rate_pct=round(collection_rate, 2),
                )
            )
        segment_rows.sort(key=lambda row: row.outstanding_usd, reverse=True)
        segment_rows = segment_rows[:top_n]
        largest_segment = segment_rows[0].segment if segment_rows else None
        riskiest_segment = (
            max(segment_rows, key=lambda row: row.par90_pct).segment if segment_rows else None
        )
        summary = SegmentAnalyticsSummary(
            dimension=dimension,
            segment_count=len(segment_rows),
            total_loans=len(df),
            largest_segment=largest_segment,
            riskiest_segment=riskiest_segment,
        )
        return SegmentAnalyticsResponse(
            generated_at=datetime.now(), segments=segment_rows, summary=summary
        )

    async def calculate_roll_rate_analytics(
        self, loans: list[LoanRecord] | None
    ) -> RollRateAnalyticsResponse:
        try:
            if loans is None:
                loans = []
            return await run_in_threadpool(self._calculate_roll_rate_analytics_sync, loans)
        except Exception as e:
            logger.error(
                "Error calculating roll-rate analytics for actor %s: %s",
                self.actor,
                e,
                exc_info=True,
            )
            raise

    def _calculate_roll_rate_analytics_sync(
        self, loans: list[LoanRecord]
    ) -> RollRateAnalyticsResponse:
        df = self._convert_loan_records_to_dataframe(loans)
        if df.empty:
            return self._empty_roll_rate_analytics_response()
        prepared_df, matrix_df, explicit_previous_signal = self._build_roll_rate_base_frames(df)
        transition_matrix = self._build_roll_rate_transition_matrix(matrix_df)
        bucket_summaries = self._build_roll_rate_bucket_summaries(prepared_df)
        summary = self._build_roll_rate_summary(
            prepared_df, matrix_df, bucket_summaries, explicit_previous_signal
        )
        return RollRateAnalyticsResponse(
            generated_at=datetime.now(),
            transition_matrix=transition_matrix,
            bucket_summaries=bucket_summaries,
            summary=summary,
        )

    def _empty_roll_rate_analytics_response(self) -> RollRateAnalyticsResponse:
        return RollRateAnalyticsResponse(
            generated_at=datetime.now(),
            transition_matrix=[],
            bucket_summaries=[],
            summary=RollRateAnalyticsSummary(
                total_loans=0,
                historical_coverage_pct=0.0,
                portfolio_cure_rate_pct=0.0,
                portfolio_roll_forward_rate_pct=0.0,
                worst_migration_path=None,
                best_cure_source=None,
            ),
        )

    def _build_roll_rate_base_frames(
        self, df: pd.DataFrame
    ) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series]:
        work = df.copy()
        current_dpd = self._derive_dpd_series(
            df=work, dpd_column="days_past_due", status_column="loan_status"
        )
        previous_dpd_raw = self._derive_dpd_series(
            df=work, dpd_column="previous_days_past_due", status_column="previous_loan_status"
        )
        explicit_previous_signal = self._resolve_explicit_previous_signal(work)
        previous_dpd = previous_dpd_raw.where(explicit_previous_signal, current_dpd)
        to_balance = pd.to_numeric(work["principal_balance"], errors="coerce").fillna(0.0)
        if "previous_principal_balance" in work.columns:
            from_balance = (
                pd.to_numeric(work["previous_principal_balance"], errors="coerce")
                .fillna(to_balance)
                .astype(float)
            )
        else:
            from_balance = to_balance.astype(float)
        work["from_bucket"] = previous_dpd.apply(self._map_dpd_to_bucket)
        work["to_bucket"] = current_dpd.apply(self._map_dpd_to_bucket)
        work["from_severity"] = work["from_bucket"].map(self._bucket_severity).astype(int)
        work["to_severity"] = work["to_bucket"].map(self._bucket_severity).astype(int)
        work["from_exposure_usd"] = from_balance
        matrix_df = (
            work.groupby(["from_bucket", "to_bucket"], dropna=False)
            .agg(loan_count=("from_bucket", "size"), exposure_usd=("from_exposure_usd", "sum"))
            .reset_index()
        )
        matrix_df["from_order"] = matrix_df["from_bucket"].map(self._bucket_severity)
        matrix_df["to_order"] = matrix_df["to_bucket"].map(self._bucket_severity)
        matrix_df = matrix_df.sort_values(["from_order", "to_order"])
        return (work, matrix_df, explicit_previous_signal)

    @staticmethod
    def _resolve_explicit_previous_signal(df: pd.DataFrame) -> pd.Series:
        if "previous_days_past_due" in df.columns:
            previous_dpd_source = df["previous_days_past_due"]
            explicit_previous_signal = pd.to_numeric(previous_dpd_source, errors="coerce").notna()
        else:
            explicit_previous_signal = pd.Series([False] * len(df), index=df.index)
        if "previous_loan_status" in df.columns:
            previous_status_present = (
                df["previous_loan_status"].fillna("").astype(str).str.strip() != ""
            )
            explicit_previous_signal = explicit_previous_signal | previous_status_present
        return explicit_previous_signal

    def _build_roll_rate_transition_matrix(
        self, matrix_df: pd.DataFrame
    ) -> list[RollRateTransition]:
        from_totals_count = matrix_df.groupby("from_bucket")["loan_count"].transform("sum")
        from_totals_exposure = matrix_df.groupby("from_bucket")["exposure_usd"].transform("sum")
        matrix_df = matrix_df.copy()
        matrix_df["loan_share_pct"] = (
            (matrix_df["loan_count"] / from_totals_count * 100).fillna(0.0).round(2)
        )
        matrix_df["exposure_share_pct"] = (
            (matrix_df["exposure_usd"] / from_totals_exposure * 100).fillna(0.0).round(2)
        )
        matrix_df["exposure_usd"] = matrix_df["exposure_usd"].round(2)
        return [
            RollRateTransition(**row)
            for row in matrix_df[
                [
                    "from_bucket",
                    "to_bucket",
                    "loan_count",
                    "exposure_usd",
                    "loan_share_pct",
                    "exposure_share_pct",
                ]
            ].to_dict("records")
        ]

    def _build_roll_rate_bucket_summaries(self, df: pd.DataFrame) -> list[RollRateBucketSummary]:
        if "loan_count" not in df.columns:
            df = df.copy()
            df["loan_count"] = 1
        bucket_stats = df.groupby("from_bucket").agg(
            loan_count=("loan_count", "sum"), exposure_usd=("from_exposure_usd", "sum")
        )
        cure_counts = (
            df[(df["to_bucket"] == "current") & (df["from_bucket"] != "current")]
            .groupby("from_bucket")["loan_count"]
            .sum()
        )
        roll_forward_counts = (
            df[df["to_severity"] > df["from_severity"]].groupby("from_bucket")["loan_count"].sum()
        )
        stable_counts = (
            df[df["to_bucket"] == df["from_bucket"]].groupby("from_bucket")["loan_count"].sum()
        )
        summaries: list[RollRateBucketSummary] = []
        for bucket in self._bucket_order():
            count = (
                int(bucket_stats.loc[bucket, "loan_count"]) if bucket in bucket_stats.index else 0
            )
            exposure = (
                float(bucket_stats.loc[bucket, "exposure_usd"])
                if bucket in bucket_stats.index
                else 0.0
            )
            cure_c = int(cure_counts.get(bucket, 0))
            roll_f_c = int(roll_forward_counts.get(bucket, 0))
            stable_c = int(stable_counts.get(bucket, 0))
            summaries.append(
                RollRateBucketSummary(
                    from_bucket=bucket,
                    loan_count=count,
                    exposure_usd=round(exposure, 2),
                    cure_rate_pct=round(self._safe_pct(cure_c, float(count)), 2),
                    roll_forward_rate_pct=round(self._safe_pct(roll_f_c, float(count)), 2),
                    stability_rate_pct=round(self._safe_pct(stable_c, float(count)), 2),
                )
            )
        return summaries

    def _build_roll_rate_summary(
        self,
        df: pd.DataFrame,
        matrix_df: pd.DataFrame,
        bucket_summaries: list[RollRateBucketSummary],
        explicit_previous_signal: pd.Series,
    ) -> RollRateAnalyticsSummary:
        delinquent_mask = df["from_bucket"] != "current"
        cured_portfolio = int((delinquent_mask & (df["to_bucket"] == "current")).sum())
        delinquent_total = int(delinquent_mask.sum())
        max_severity = max(self._bucket_severity.values())
        roll_eligible_mask = df["from_severity"] < max_severity
        roll_forward_portfolio = int(
            (roll_eligible_mask & (df["to_severity"] > df["from_severity"])).sum()
        )
        roll_eligible_total = int(roll_eligible_mask.sum())
        migration_rows = matrix_df[matrix_df["to_order"] > matrix_df["from_order"]].sort_values(
            ["loan_count", "exposure_usd"], ascending=False
        )
        worst_migration_path = (
            f"{migration_rows.iloc[0]['from_bucket']}->{migration_rows.iloc[0]['to_bucket']}"
            if not migration_rows.empty and int(migration_rows.iloc[0]["loan_count"]) > 0
            else None
        )
        cure_candidates = [
            row for row in bucket_summaries if row.from_bucket != "current" and row.loan_count > 0
        ]
        if cure_candidates and (
            best_cure_row := max(
                cure_candidates, key=lambda row: (row.cure_rate_pct, row.loan_count)
            )
        ):
            best_cure_source = (
                best_cure_row.from_bucket if best_cure_row.cure_rate_pct > 0 else None
            )
        else:
            best_cure_source = None
        return RollRateAnalyticsSummary(
            total_loans=len(df),
            historical_coverage_pct=round(
                self._safe_pct(explicit_previous_signal.sum(), len(df)), 2
            ),
            portfolio_cure_rate_pct=round(self._safe_pct(cured_portfolio, delinquent_total), 2),
            portfolio_roll_forward_rate_pct=round(
                self._safe_pct(roll_forward_portfolio, roll_eligible_total), 2
            ),
            worst_migration_path=worst_migration_path,
            best_cure_source=best_cure_source,
        )

    def _calculate_stress_test_sync(
        self,
        loans: list[LoanRecord],
        par_deterioration_pct: float,
        collection_efficiency_pct: float,
        recovery_efficiency_pct: float,
        funding_cost_bps: float,
    ) -> StressTestResponse:
        df = self._convert_loan_records_to_dataframe(loans)
        if df.empty:
            zero_metrics = StressTestMetrics(
                par30_pct=0.0,
                par90_pct=0.0,
                default_rate_pct=0.0,
                loss_rate_pct=0.0,
                collection_rate_pct=0.0,
                recovery_rate_pct=0.0,
                gross_margin_pct=0.0,
                revenue_forecast_6m_usd=0.0,
                expected_credit_loss_usd=0.0,
                expected_collections_usd=0.0,
            )
            assumptions = StressTestAssumptions(
                par_deterioration_pct=par_deterioration_pct,
                collection_efficiency_pct=collection_efficiency_pct,
                recovery_efficiency_pct=recovery_efficiency_pct,
                funding_cost_bps=funding_cost_bps,
            )
            return StressTestResponse(
                scenario_id=str(uuid.uuid4()),
                generated_at=datetime.now(),
                assumptions=assumptions,
                baseline=zero_metrics,
                stressed=zero_metrics,
                deltas=zero_metrics,
                alerts=[],
            )
        baseline_raw = self._calculate_portfolio_performance_metrics(df.copy())
        total_originated = float(pd.to_numeric(df["loan_amount"], errors="coerce").fillna(0).sum())
        total_scheduled = (
            float(pd.to_numeric(df["total_scheduled"], errors="coerce").fillna(0).sum())
            if "total_scheduled" in df.columns
            else 0.0
        )
        baseline = StressTestMetrics(
            par30_pct=round(float(baseline_raw["par30"]), 2),
            par90_pct=round(float(baseline_raw["par90"]), 2),
            default_rate_pct=round(float(baseline_raw["default_rate"]), 2),
            loss_rate_pct=round(float(baseline_raw["loss_rate"]), 2),
            collection_rate_pct=round(float(baseline_raw["collection_rate"]), 2),
            recovery_rate_pct=round(float(baseline_raw["recovery_rate"]), 2),
            gross_margin_pct=round(float(baseline_raw["gross_margin_pct"]), 2),
            revenue_forecast_6m_usd=round(float(baseline_raw["revenue_forecast_6m"]), 2),
            expected_credit_loss_usd=round(
                total_originated * float(baseline_raw["loss_rate"]) / 100.0, 2
            ),
            expected_collections_usd=round(
                total_scheduled * float(baseline_raw["collection_rate"]) / 100.0, 2
            ),
        )
        par_factor = 1.0 + par_deterioration_pct / 100.0
        collection_factor = 1.0 + collection_efficiency_pct / 100.0
        recovery_factor = 1.0 + recovery_efficiency_pct / 100.0
        stressed_par30 = self._clamp_pct(baseline.par30_pct * par_factor)
        stressed_par90 = self._clamp_pct(
            baseline.par90_pct * (1.0 + par_deterioration_pct * 1.2 / 100.0)
        )
        stressed_default = self._clamp_pct(
            baseline.default_rate_pct * (1.0 + par_deterioration_pct * 0.8 / 100.0)
        )
        stressed_loss = self._clamp_pct(
            baseline.loss_rate_pct * (1.0 + par_deterioration_pct * 1.1 / 100.0)
        )
        stressed_collection = self._clamp_pct(baseline.collection_rate_pct * collection_factor)
        stressed_recovery = self._clamp_pct(baseline.recovery_rate_pct * recovery_factor)
        funding_cost_pct = float(funding_cost_bps) / 100.0
        loss_drag = max(0.0, stressed_loss - baseline.loss_rate_pct) * 0.35
        recovery_drag = max(0.0, baseline.recovery_rate_pct - stressed_recovery) * 0.15
        par_drag = max(0.0, stressed_par30 - baseline.par30_pct) * 0.1
        collection_drag = max(0.0, baseline.collection_rate_pct - stressed_collection) * 0.08
        stressed_margin = round(
            baseline.gross_margin_pct
            - funding_cost_pct
            - loss_drag
            - recovery_drag
            - par_drag
            - collection_drag,
            2,
        )
        forecast_drag = (
            max(0.0, stressed_default - baseline.default_rate_pct) * 0.5
            + max(0.0, baseline.collection_rate_pct - stressed_collection) * 0.3
        )
        stressed_forecast = max(
            0.0, baseline.revenue_forecast_6m_usd * (1.0 - forecast_drag / 100.0)
        )
        stressed = StressTestMetrics(
            par30_pct=round(stressed_par30, 2),
            par90_pct=round(stressed_par90, 2),
            default_rate_pct=round(stressed_default, 2),
            loss_rate_pct=round(stressed_loss, 2),
            collection_rate_pct=round(stressed_collection, 2),
            recovery_rate_pct=round(stressed_recovery, 2),
            gross_margin_pct=round(stressed_margin, 2),
            revenue_forecast_6m_usd=round(stressed_forecast, 2),
            expected_credit_loss_usd=round(total_originated * stressed_loss / 100.0, 2),
            expected_collections_usd=round(total_scheduled * stressed_collection / 100.0, 2),
        )
        deltas = StressTestMetrics(
            par30_pct=round(stressed.par30_pct - baseline.par30_pct, 2),
            par90_pct=round(stressed.par90_pct - baseline.par90_pct, 2),
            default_rate_pct=round(stressed.default_rate_pct - baseline.default_rate_pct, 2),
            loss_rate_pct=round(stressed.loss_rate_pct - baseline.loss_rate_pct, 2),
            collection_rate_pct=round(
                stressed.collection_rate_pct - baseline.collection_rate_pct, 2
            ),
            recovery_rate_pct=round(stressed.recovery_rate_pct - baseline.recovery_rate_pct, 2),
            gross_margin_pct=round(stressed.gross_margin_pct - baseline.gross_margin_pct, 2),
            revenue_forecast_6m_usd=round(
                stressed.revenue_forecast_6m_usd - baseline.revenue_forecast_6m_usd, 2
            ),
            expected_credit_loss_usd=round(
                stressed.expected_credit_loss_usd - baseline.expected_credit_loss_usd, 2
            ),
            expected_collections_usd=round(
                stressed.expected_collections_usd - baseline.expected_collections_usd, 2
            ),
        )
        alerts: list[str] = []
        if stressed.par90_pct >= 10.0:
            alerts.append("Severe delinquency stress: PAR90 exceeds 10%.")
        if stressed.collection_rate_pct < 75.0:
            alerts.append("Collections stress: projected collection rate below 75%.")
        if stressed.gross_margin_pct < 0.0:
            alerts.append("Profitability stress: projected gross margin turns negative.")
        if (
            baseline.expected_credit_loss_usd > 0
            and stressed.expected_credit_loss_usd >= baseline.expected_credit_loss_usd * 1.25
        ):
            alerts.append("Capital stress: expected credit loss increases by at least 25%.")
        assumptions = StressTestAssumptions(
            par_deterioration_pct=round(float(par_deterioration_pct), 2),
            collection_efficiency_pct=round(float(collection_efficiency_pct), 2),
            recovery_efficiency_pct=round(float(recovery_efficiency_pct), 2),
            funding_cost_bps=round(float(funding_cost_bps), 2),
        )
        return StressTestResponse(
            scenario_id=str(uuid.uuid4()),
            generated_at=datetime.now(),
            assumptions=assumptions,
            baseline=baseline,
            stressed=stressed,
            deltas=deltas,
            alerts=alerts,
        )

    async def get_risk_stratification(
        self, loans: list[LoanRecord] | None
    ) -> RiskStratificationResponse:
        if not loans:
            return RiskStratificationResponse(
                buckets=[], decision_flags=[], summary="No loans provided for stratification."
            )
        advanced_risk = await self.calculate_advanced_risk(loans)
        hhi = advanced_risk.concentration_hhi
        if hhi > 2500:
            status = "red"
            reason = f"HHI of {hhi:.0f} indicates high borrower concentration risk."
        elif hhi > 1500:
            status = "yellow"
            reason = f"HHI of {hhi:.0f} indicates moderate borrower concentration."
        else:
            status = "green"
            reason = f"HHI of {hhi:.0f} indicates healthy portfolio diversification."
        decision_flags = [DecisionFlag(flag="Concentration", status=status, reason=reason)]
        par30 = advanced_risk.par30
        if par30 > 15:
            status = "red"
            reason = f"PAR30 of {par30:.1f}% exceeds high-risk threshold."
        elif par30 > 8:
            status = "yellow"
            reason = f"PAR30 of {par30:.1f}% is in the cautionary zone."
        else:
            status = "green"
            reason = f"PAR30 of {par30:.1f}% is within healthy limits."
        decision_flags.append(DecisionFlag(flag="Asset Quality", status=status, reason=reason))
        coverage = advanced_risk.collections_coverage
        if coverage < 80:
            status = "red"
            reason = f"Collections coverage of {coverage:.1f}% indicates severe liquidity pressure."
        elif coverage < 90:
            status = "yellow"
            reason = f"Collections coverage of {coverage:.1f}% is below target."
        else:
            status = "green"
            reason = f"Collections coverage of {coverage:.1f}% is healthy."
        decision_flags.append(DecisionFlag(flag="Liquidity", status=status, reason=reason))
        roll_rates = await self.calculate_roll_rate_analytics(loans)
        cure_rate = roll_rates.summary.portfolio_cure_rate_pct
        if cure_rate < 20:
            status = "red"
            reason = f"Cure rate of {cure_rate:.1f}% indicates poor recovery from delinquency."
        elif cure_rate < 40:
            status = "yellow"
            reason = f"Cure rate of {cure_rate:.1f}% is below optimal levels."
        else:
            status = "green"
            reason = f"Cure rate of {cure_rate:.1f}% shows healthy collection efficiency."
        decision_flags.append(DecisionFlag(flag="Recovery", status=status, reason=reason))
        summary = f"Portfolio shows {par30:.1f}% PAR30 across {advanced_risk.total_loans} loans. Asset quality is {decision_flags[1].status} and diversification is {decision_flags[0].status}."
        return RiskStratificationResponse(
            buckets=advanced_risk.dpd_buckets, decision_flags=decision_flags, summary=summary
        )

    async def get_layered_insights(self, loans: list[LoanRecord] | None) -> list[AnalysisLayer]:
        if not loans:
            return []
        df = await run_in_threadpool(self._convert_loan_records_to_dataframe, loans)
        metrics = self._calculate_portfolio_performance_metrics(df)
        heatmap_summary = await self.get_risk_heatmap_summary(loans)
        critical_buckets = [
            bucket["label"]
            for bucket in heatmap_summary["heatmap"]
            if bucket["risk_intensity"] == "high"
        ]
        cure_rate = (
            await self.calculate_roll_rate_analytics(loans)
        ).summary.portfolio_cure_rate_pct
        return [
            self._build_portfolio_risk_layer(metrics, critical_buckets),
            self._build_growth_profitability_layer(metrics),
            self._build_operational_efficiency_layer(metrics, cure_rate),
        ]

    async def get_risk_heatmap_summary(self, loans: list[LoanRecord] | None) -> dict[str, Any]:
        if not loans:
            return {"status": "no_data", "heatmap": [], "critical_buckets": []}
        df = await run_in_threadpool(self._convert_loan_records_to_dataframe, loans)
        metrics = self._calculate_portfolio_performance_metrics(df)
        buckets = self._build_heatmap_buckets(metrics)
        heatmap, critical_buckets = self._build_heatmap_rows(buckets)
        narrative = self._build_heatmap_narrative(critical_buckets, heatmap)
        return {
            "status": "success",
            "heatmap": heatmap,
            "critical_buckets": critical_buckets,
            "narrative": narrative,
            "overall_par30": round(metrics["par30"], 2),
        }

    @staticmethod
    def _build_portfolio_risk_layer(
        metrics: dict[str, float], critical_buckets: list[str]
    ) -> AnalysisLayer:
        risk_status = "elevated" if metrics["par30"] > 10 or metrics["npl"] > 5 else "stable"
        risk_driver = (
            ", ".join(critical_buckets) if critical_buckets else "Normal migration patterns"
        )
        return AnalysisLayer(
            layer="Portfolio Risk",
            what=f"Portfolio risk is currently {risk_status} with PAR30 at {metrics['par30']:.1f}%.",
            why=f"Driver: {risk_driver}.",
            so_what=f"Impact: Potential {metrics['cor']:.1f}% hit to margin from expected credit losses.",
            now_what="Action: Trigger intensive collections for high-intensity buckets and review underwriting for toxic cohorts.",
        )

    @staticmethod
    def _build_growth_profitability_layer(metrics: dict[str, float]) -> AnalysisLayer:
        nim = metrics["gross_margin_pct"]
        clv_cac = metrics["customer_lifetime_value"] / metrics["cac"] if metrics["cac"] > 0 else 0.0
        return AnalysisLayer(
            layer="Growth & Profitability",
            what=f"Unit economics show a {clv_cac:.1f}x CLV/CAC ratio and {nim:.1f}% NIM.",
            why="Driver: High repeat borrower rate and stable yield spread.",
            so_what="Impact: Growth is sustainable and provides positive risk-adjusted returns.",
            now_what="Action: Maintain acquisition cadence while monitoring for any margin compression.",
        )

    @staticmethod
    def _build_operational_efficiency_layer(
        metrics: dict[str, float], cure_rate: float
    ) -> AnalysisLayer:
        return AnalysisLayer(
            layer="Operational Efficiency",
            what=f"Collections efficiency is at {metrics['collection_rate']:.1f}% with a {cure_rate:.1f}% cure rate.",
            why="Driver: Effective early-stage intervention and automated PTP tracking.",
            so_what="Impact: High cash conversion speed reduces funding pressure.",
            now_what="Action: Optimize SMS/Call timing based on DPD migration patterns to further improve cure rates.",
        )

    @staticmethod
    def _build_heatmap_buckets(metrics: dict[str, float]) -> list[dict[str, Any]]:
        return [
            {
                "id": "1_30",
                "label": "Early (1-30 DPD)",
                "value": metrics["dpd_1_30"],
                "threshold": 8.0,
            },
            {
                "id": "31_60",
                "label": "Warning (31-60 DPD)",
                "value": metrics["dpd_31_60"],
                "threshold": 4.0,
            },
            {
                "id": "61_90",
                "label": "Severe (61-90 DPD)",
                "value": metrics["dpd_61_90"],
                "threshold": 2.0,
            },
            {
                "id": "90_plus",
                "label": "NPL (90+ DPD)",
                "value": metrics["dpd_90_plus"],
                "threshold": 1.0,
            },
        ]

    @staticmethod
    def _bucket_risk_intensity(value: float, threshold: float) -> str:
        risk = "low"
        if value > threshold * 2:
            risk = "high"
        elif value > threshold:
            risk = "medium"
        return risk

    def _build_heatmap_rows(
        self, buckets: list[dict[str, Any]]
    ) -> tuple[list[dict[str, Any]], list[str]]:
        heatmap: list[dict[str, Any]] = []
        critical_buckets: list[str] = []
        for bucket in buckets:
            intensity = self._bucket_risk_intensity(
                float(bucket["value"]), float(bucket["threshold"])
            )
            if intensity == "high":
                critical_buckets.append(str(bucket["label"]))
            heatmap.append(
                {
                    "bucket": bucket["id"],
                    "label": bucket["label"],
                    "exposure_pct": round(float(bucket["value"]), 2),
                    "risk_intensity": intensity,
                }
            )
        return (heatmap, critical_buckets)

    @staticmethod
    def _build_heatmap_narrative(critical_buckets: list[str], heatmap: list[dict[str, Any]]) -> str:
        if critical_buckets:
            return f"Critical risk concentration identified in: {', '.join(critical_buckets)}."
        if any((bucket["risk_intensity"] == "medium" for bucket in heatmap)):
            return "Moderate risk migration detected in early-stage buckets."
        return "Portfolio risk is well-distributed."

    def _calculate_portfolio_performance_metrics(self, df: pd.DataFrame) -> dict:
        total_outstanding = float(df["principal_balance"].sum())
        total_originated = float(df["loan_amount"].sum())
        df["dpd"] = self._derive_dpd_series(df, "days_past_due", "loan_status")
        par_metrics = self._calculate_par_and_bucket_metrics(df, total_outstanding)
        status_series = self._normalize_default_status(df["loan_status"])
        default_mask = status_series.eq("defaulted")
        default_rate_pct = default_mask.sum() / len(df) * 100 if len(df) > 0 else 0
        defaulted_balance = float(df.loc[default_mask, "principal_balance"].sum())
        loss_rate = defaulted_balance / total_originated * 100 if total_originated > 0 else 0
        status_defaulted_mask = status_series.eq("defaulted")
        status_series = df["loan_status"].astype(str)
        default_mask = status_series.str.contains(STATUS_PATTERN_DEFAULT, case=False, na=False)
        default_rate_pct = default_mask.sum() / len(df) * 100 if len(df) > 0 else 0
        defaulted_balance = float(df.loc[default_mask, "principal_balance"].sum())
        loss_rate = defaulted_balance / total_originated * 100 if total_originated > 0 else 0
        status_defaulted_mask = status_series.str.contains(
            STATUS_PATTERN_DEFAULT, case=False, na=False
        )
        weighted_interest = float((df["interest_rate"] * df["principal_balance"]).sum())
        avg_interest_rate = weighted_interest / total_outstanding if total_outstanding > 0 else 0
        collection_rate, recovery_rate = self._calculate_collection_recovery_metrics(
            df, status_defaulted_mask
        )
        npl_pct = par_metrics["npl"]
        npl_90_pct = par_metrics["npl90"]
        lgd_pct = 100.0 - recovery_rate if defaulted_balance > 0 else 0.0
        self._populate_ltv_dti_ratios(df)
        active_borrowers, repeat_borrower_rate = self._calculate_borrower_metrics(df)
        executive_metrics = self._calculate_realtime_executive_metrics(df)
        disbursement_volume_mtd, new_loans_count_mtd = self._calculate_mtd_metrics(df)
        enriched_metrics = self._calculate_realtime_enriched_metrics(df, total_outstanding)
        gross_margin_pct = executive_metrics["gross_margin_pct"]
        return {
            "par30": par_metrics["par30"],
            "par60": par_metrics["par60"],
            "par90": par_metrics["par90"],
            "dpd_1_30": par_metrics["dpd_1_30"],
            "dpd_31_60": par_metrics["dpd_31_60"],
            "dpd_61_90": par_metrics["dpd_61_90"],
            "dpd_90_plus": par_metrics["dpd_90_plus"],
            "default_rate": default_rate_pct,
            "collection_rate": collection_rate,
            "loss_rate": loss_rate,
            "recovery_rate": recovery_rate,
            "npl": npl_pct,
            "npl_90": npl_90_pct,
            "lgd": lgd_pct,
            "cor": loss_rate,
            "cash_on_hand": self._calculate_cash_on_hand(df),
            "yield": avg_interest_rate,
            "aum": total_outstanding,
            "average_loan_size": float(df["loan_amount"].mean()) if len(df) > 0 else 0.0,
            "disbursement_volume_mtd": disbursement_volume_mtd,
            "new_loans_count_mtd": new_loans_count_mtd,
            "customer_lifetime_value": self._calculate_customer_lifetime_value(df),
            "cac": executive_metrics["cac"],
            "gross_margin_pct": gross_margin_pct,
            "revenue_forecast_6m": executive_metrics["revenue_forecast_6m"],
            "churn_90d": executive_metrics["churn_90d"],
            "avg_ltv": df["ltv_ratio"].mean(),
            "avg_dti": df["dti_ratio"].mean(),
            "active_borrowers": active_borrowers,
            "repeat_borrower_rate": repeat_borrower_rate,
            "automation_rate": self._calculate_automation_rate(df),
            "processing_time_avg": self._calculate_processing_time_avg(df),
            "count": self._calculate_total_loans_count(df, status_series),
            "collections_eligible_rate": enriched_metrics["collections_eligible_rate"],
            "government_sector_exposure_rate": enriched_metrics["government_sector_exposure_rate"],
            "avg_credit_line_utilization": enriched_metrics["avg_credit_line_utilization"],
            "capital_collection_rate": enriched_metrics["capital_collection_rate"],
            "mdsc_posted_rate": enriched_metrics["mdsc_posted_rate"],
        }

    @staticmethod
    def _first_present_column(df: pd.DataFrame, *candidates: str) -> str | None:
        return next((col for col in candidates if col in df.columns), None)

    @staticmethod
    def _compute_util_metric(df: pd.DataFrame, util_col: str) -> float:
        raw_util = df[util_col].astype(str).str.replace("[$,%\\s]", "", regex=True)
        util_series = pd.to_numeric(raw_util, errors="coerce").dropna()
        if util_series.empty:
            return 0.0
        median_val = float(util_series.median())
        if median_val < 2.0:
            util_series = util_series * 100
        return float(util_series.mean())

    def _calculate_realtime_enriched_metrics(
        self, df: pd.DataFrame, total_outstanding: float
    ) -> dict[str, float]:
        metrics = {
            "collections_eligible_rate": 0.0,
            "government_sector_exposure_rate": 0.0,
            "avg_credit_line_utilization": 0.0,
            "capital_collection_rate": 0.0,
            "mdsc_posted_rate": 0.0,
        }
        if df.empty:
            return metrics
        balance_col = self._first_present_column(
            df, "principal_balance", "outstanding_balance", "current_balance", "loan_amount"
        )
        if balance_col is None:
            return metrics
        balance = pd.to_numeric(df[balance_col], errors="coerce").fillna(0.0)
        denom = balance.sum() if total_outstanding <= 0 else total_outstanding
        if denom <= 0:
            return metrics
        eligible_col = self._first_present_column(df, "collections_eligible", "procede_a_cobrar")
        if eligible_col is not None:
            eligible_mask = (
                df[eligible_col]
                .astype(str)
                .str.strip()
                .str.upper()
                .isin({"Y", "YES", "SI", "S", "TRUE", "1"})
            )
            metrics["collections_eligible_rate"] = self._safe_pct(
                balance[eligible_mask].sum(), denom
            )
        govt_col = self._first_present_column(df, "government_sector", "goes")
        if govt_col is not None:
            govt_mask = df[govt_col].astype(str).str.strip().str.upper().eq("GOES")
            metrics["government_sector_exposure_rate"] = self._safe_pct(
                float(balance[govt_mask].sum()), denom
            )
        util_col = self._first_present_column(df, "utilization_pct", "porcentaje_utilizado")
        if util_col is not None:
            metrics["avg_credit_line_utilization"] = self._compute_util_metric(df, util_col)
        cap_col = self._first_present_column(df, "capital_collected", "capitalcobrado")
        if cap_col is not None:
            cap_collected = pd.to_numeric(df[cap_col], errors="coerce").fillna(0.0)
            metrics["capital_collection_rate"] = self._safe_pct(float(cap_collected.sum()), denom)
        mdsc_col = self._first_present_column(df, "mdsc_posted", "mdscposteado")
        if mdsc_col is not None:
            mdsc = pd.to_numeric(df[mdsc_col], errors="coerce").fillna(0.0)
            if len(mdsc) > 0:
                metrics["mdsc_posted_rate"] = self._safe_pct(float(mdsc.sum()), float(len(mdsc)))
        return metrics

    @staticmethod
    def _calculate_cash_on_hand(df: pd.DataFrame) -> float:
        if "current_balance" not in df.columns:
            return 0.0
        current_balance_series = pd.to_numeric(df["current_balance"], errors="coerce")
        null_or_zero_ratio = (
            (current_balance_series.isna() | (current_balance_series == 0)).mean()
            if len(current_balance_series) > 0
            else 1.0
        )
        if null_or_zero_ratio > 0.8:
            return float(pd.to_numeric(df["principal_balance"], errors="coerce").fillna(0).sum())
        return float(current_balance_series.fillna(0).sum())

    @staticmethod
    def _populate_ltv_dti_ratios(df: pd.DataFrame) -> None:
        if "appraised_value" in df.columns and df["appraised_value"].notna().any():
            df["ltv_ratio"] = df["loan_amount"] / df["appraised_value"] * 100
        else:
            df["ltv_ratio"] = float("nan")
        if (
            "monthly_debt" in df.columns
            and "borrower_income" in df.columns
            and df["borrower_income"].notna().any()
        ):
            df["dti_ratio"] = df["monthly_debt"] / df["borrower_income"] * 100
        else:
            df["dti_ratio"] = float("nan")

    @staticmethod
    def _calculate_processing_time_avg(df: pd.DataFrame) -> float:
        if (
            "term_months" in df.columns
            and pd.to_numeric(df["term_months"], errors="coerce").notna().any()
        ):
            return float(pd.to_numeric(df["term_months"], errors="coerce").dropna().mean())
        return 0.0

    @staticmethod
    def _calculate_mtd_metrics(df: pd.DataFrame) -> tuple[float, float]:
        if "origination_date" not in df.columns:
            return (0.0, 0.0)
        origination_dates = pd.to_datetime(
            df["origination_date"], errors="coerce", utc=True
        ).dt.tz_convert(None)
        month_start = pd.Timestamp.now().normalize().replace(day=1)
        mtd_mask = origination_dates >= month_start
        disbursement_volume_mtd = float(df.loc[mtd_mask, "loan_amount"].sum())
        new_loans_count_mtd = float(mtd_mask.sum())
        return (disbursement_volume_mtd, new_loans_count_mtd)

    @staticmethod
    def _calculate_customer_lifetime_value(df: pd.DataFrame) -> float:
        if "tpv" in df.columns and pd.to_numeric(df["tpv"], errors="coerce").notna().any():
            tpv_series = pd.to_numeric(df["tpv"], errors="coerce").fillna(0)
        else:
            tpv_series = pd.to_numeric(df["loan_amount"], errors="coerce").fillna(0)
        unique_borrowers = (
            float(df["borrower_id"].dropna().astype(str).nunique())
            if "borrower_id" in df.columns
            else 0.0
        )
        return float(tpv_series.sum()) / unique_borrowers if unique_borrowers > 0 else 0.0

    @staticmethod
    def _calculate_total_loans_count(df: pd.DataFrame, status_series: pd.Series) -> float:
        if "id" in df.columns and df["id"].notna().any():
            non_closed_mask = ~status_series.str.contains(
                "closed|complete|paid|settled", case=False, na=False
            )
            return float(df.loc[non_closed_mask, "id"].astype(str).nunique())
        return float(len(df))

    def _calculate_par_and_bucket_metrics(
        self, df: pd.DataFrame, total_outstanding: float
    ) -> dict[str, float]:
        status_series = df["loan_status"] if "loan_status" in df.columns else None
        ssot = calculate_asset_quality_metrics(
            balance=df["principal_balance"],
            dpd=df["dpd"],
            status=status_series,
            actor="api.service",
            metric_aliases=["par30", "par60", "par90", "npl", "npl90"],
        )
        dpd_1_30 = (
            float(df[(df["dpd"] > 0) & (df["dpd"] <= 30)]["principal_balance"].sum())
            / total_outstanding
            * 100
            if total_outstanding > 0
            else 0.0
        )
        dpd_31_60 = (
            float(df[(df["dpd"] > 30) & (df["dpd"] <= 60)]["principal_balance"].sum())
            / total_outstanding
            * 100
            if total_outstanding > 0
            else 0.0
        )
        dpd_61_90 = (
            float(df[(df["dpd"] > 60) & (df["dpd"] <= 90)]["principal_balance"].sum())
            / total_outstanding
            * 100
            if total_outstanding > 0
            else 0.0
        )
        dpd_90_plus = (
            float(df[df["dpd"] > 90]["principal_balance"].sum()) / total_outstanding * 100
            if total_outstanding > 0
            else 0.0
        )
        return {
            "par30": ssot.get("par30", 0.0),
            "par60": ssot.get("par60", 0.0),
            "par90": ssot.get("par90", 0.0),
            "npl": ssot.get("npl", 0.0),
            "npl90": ssot.get("npl90", 0.0),
            "dpd_1_30": dpd_1_30,
            "dpd_31_60": dpd_31_60,
            "dpd_61_90": dpd_61_90,
            "dpd_90_plus": dpd_90_plus,
        }

    def _calculate_collection_recovery_metrics(
        self, df: pd.DataFrame, status_defaulted_mask: pd.Series
    ) -> tuple[float, float]:
        scheduled = (
            pd.to_numeric(df["total_scheduled"], errors="coerce").fillna(0)
            if "total_scheduled" in df.columns
            else pd.Series([0.0] * len(df), index=df.index)
        )
        collected = (
            pd.to_numeric(df["last_payment_amount"], errors="coerce").fillna(0)
            if "last_payment_amount" in df.columns
            else pd.Series([0.0] * len(df), index=df.index)
        )
        total_scheduled = float(scheduled.sum())
        collection_rate = self._safe_pct(float(collected.sum()), total_scheduled)
        recovery_amount = float(collected[status_defaulted_mask].sum())
        defaulted_balance_for_recovery = float(
            df.loc[status_defaulted_mask, "principal_balance"].sum()
        )
        recovery_rate = self._safe_pct(recovery_amount, defaulted_balance_for_recovery)
        return (collection_rate, recovery_rate)

    def _calculate_borrower_metrics(self, df: pd.DataFrame) -> tuple[float, float]:
        if "borrower_id" not in df.columns or not df["borrower_id"].notna().any():
            return (0.0, 0.0)
        borrower_series = df["borrower_id"].dropna().astype(str)
        active_mask = ~df["loan_status"].str.contains(
            "closed|complete|paid|settled", case=False, na=False
        )
        active_borrowers = float(df.loc[active_mask, "borrower_id"].dropna().astype(str).nunique())
        borrower_counts = borrower_series.value_counts()
        repeat_borrower_rate = self._safe_pct(
            float((borrower_counts > 1).sum()), len(borrower_counts)
        )
        return (active_borrowers, repeat_borrower_rate)

    @staticmethod
    def _calculate_automation_rate(df: pd.DataFrame) -> float:
        if "payment_frequency" not in df.columns:
            return 0.0
        automated_mask = (
            df["payment_frequency"]
            .fillna("")
            .astype(str)
            .str.contains("bullet|auto", case=False, na=False)
        )
        return float(automated_mask.sum()) / float(len(df)) * 100 if len(df) > 0 else 0.0

    @staticmethod
    def _last_realtime_metric(rows: list[dict], key: str) -> float | None:
        value = next(
            (
                row.get(key)
                for row in reversed(rows)
                if row.get(key) is not None and (not pd.isna(row.get(key)))
            ),
            None,
        )
        return float(value) if value is not None else None

    def _calculate_realtime_executive_metrics(self, df: pd.DataFrame) -> dict[str, float]:
        try:
            normalized = self._normalize_loans_for_catalog(
                df.copy(), pd.DataFrame(), pd.DataFrame()
            )
            processor = KPICatalogProcessor(
                loans_df=normalized,
                payments_df=pd.DataFrame(),
                customers_df=pd.DataFrame(),
                schedule_df=pd.DataFrame(),
            )
            extended = processor.get_all_kpis()
            revenue_df = processor.get_monthly_revenue_df()
        except Exception as exc:
            logger.error(
                "Executive KPI computation failed — raising degraded state: %s", exc, exc_info=True
            )
            raise RuntimeError(
                f"Executive metrics unavailable: upstream KPI computation failed ({exc})"
            ) from exc
        executive_strip = extended.get("executive_strip", {}) or {}
        unit_economics = extended.get("unit_economics", []) or []
        churn_rows = extended.get("churn_90d_metrics", []) or []
        forecast_rows = extended.get("revenue_forecast_6m", []) or []
        cac_value = self._safe_float(
            executive_strip.get("cac_usd"),
            default=self._last_realtime_metric(unit_economics, "cac_usd"),
        )
        margin_ratio = self._safe_float(
            executive_strip.get("gross_margin_pct"),
            default=self._last_realtime_metric(unit_economics, "gross_margin_pct"),
        )
        churn_ratio = self._safe_float(self._last_realtime_metric(churn_rows, "churn90d_pct"))
        forecast_sum = float(
            sum(
                (
                    self._safe_float(row.get("forecast_revenue_usd"))
                    for row in forecast_rows
                    if isinstance(row, dict)
                )
            )
        )
        if (
            forecast_sum <= 0
            and isinstance(revenue_df, pd.DataFrame)
            and (not revenue_df.empty)
            and ("recv_revenue_for_month" in revenue_df.columns)
        ):
            revenue_series = pd.to_numeric(
                revenue_df["recv_revenue_for_month"], errors="coerce"
            ).fillna(0)
            if len(revenue_series) > 0:
                forecast_sum = max(0.0, float(revenue_series.iloc[-1]) * 6.0)
        return {
            "cac": round(cac_value, 4),
            "gross_margin_pct": round(self._ratio_to_percent(margin_ratio), 4),
            "revenue_forecast_6m": round(forecast_sum, 4),
            "churn_90d": round(self._ratio_to_percent(churn_ratio), 4),
        }

    @staticmethod
    def _ratio_to_percent(value: float) -> float:
        if pd.isna(value):
            return 0.0
        return value * 100.0 if -1.5 <= value <= 1.5 else value

    @staticmethod
    def _safe_float(value: float | int | None, default: float | None = 0.0) -> float:
        candidate = default if value is None else value
        try:
            return 0.0 if candidate is None or pd.isna(candidate) else float(candidate)
        except (TypeError, ValueError, OverflowError):
            return 0.0

    @staticmethod
    def _safe_int(value: Any, default: int = 0) -> int:
        try:
            return default if value is None or pd.isna(value) else int(float(value))
        except (TypeError, ValueError, OverflowError):
            return default

    @staticmethod
    def _clamp_pct(value: float) -> float:
        return max(0.0, min(100.0, value))

    @staticmethod
    def _safe_pct(numerator: float, denominator: float) -> float:
        return 0.0 if denominator <= 0 else numerator / denominator * 100.0

    @staticmethod
    def _series_from_aliases(
        df: pd.DataFrame, aliases: list[str], default: str = "unknown"
    ) -> pd.Series:
        lower_map = {col.lower(): col for col in df.columns}
        matched = next((lower_map.get(alias.lower()) for alias in aliases), None)
        return (
            df[matched].fillna(default).astype(str)
            if matched is not None
            else pd.Series([default] * len(df), index=df.index, dtype=object)
        )

    @staticmethod
    def _build_risk_band_series(df: pd.DataFrame, dpd: pd.Series) -> pd.Series:
        result = pd.Series(["current"] * len(df), index=df.index, dtype=object)
        result = result.mask((dpd > 0) & (dpd <= 30), "dpd_1_30")
        result = result.mask((dpd > 30) & (dpd <= 60), "dpd_31_60")
        result = result.mask((dpd > 60) & (dpd <= 90), "dpd_61_90")
        result = result.mask(dpd > 90, "dpd_90_plus")
        return result

    @staticmethod
    def _build_ticket_size_band_series(df: pd.DataFrame) -> pd.Series:
        amount_source = (
            df["loan_amount"]
            if "loan_amount" in df.columns
            else pd.Series([0] * len(df), index=df.index)
        )
        amounts = pd.to_numeric(amount_source, errors="coerce").fillna(0)
        result = pd.Series(["ticket_<1k"] * len(df), index=df.index, dtype=object)
        result = result.mask((amounts >= 1000) & (amounts < 5000), "ticket_1k_5k")
        result = result.mask((amounts >= 5000) & (amounts < 10000), "ticket_5k_10k")
        result = result.mask(amounts >= 10000, "ticket_10k_plus")
        return result

    @staticmethod
    def _build_month_period_series(df: pd.DataFrame, source_column: str) -> pd.Series:
        source = (
            df[source_column]
            if source_column in df.columns
            else pd.Series([None] * len(df), index=df.index)
        )
        parsed = pd.to_datetime(source, errors="coerce")
        return parsed.dt.to_period("M").astype(str).replace("NaT", "unknown")

    @staticmethod
    def _build_utilization_band_series(df: pd.DataFrame) -> pd.Series:
        if "utilization_pct" in df.columns:
            util_source = df["utilization_pct"]
        elif "porcentaje_utilizado" in df.columns:
            util_source = df["porcentaje_utilizado"]
        else:
            util_source = pd.Series([0] * len(df), index=df.index)
        util = pd.to_numeric(util_source, errors="coerce").fillna(0.0)
        if (util <= 1.0).all():
            util = util * 100.0
        return pd.cut(
            util,
            bins=[-0.001, 25, 50, 75, 100, float("inf")],
            labels=["0_25", "25_50", "50_75", "75_100", "100_plus"],
        ).astype(str)

    @staticmethod
    def _segment_aliases() -> dict[str, list[str]]:
        return {
            "company": ["company"],
            "credit_line": ["credit_line", "lineacredito", "linea_credito"],
            "client_code": ["client_code", "codcliente"],
            "issuer": ["issuer_name", "issuer"],
            "kam_hunter": ["kam_hunter", "cod_kam_hunter"],
            "kam_farmer": ["kam_farmer", "cod_kam_farmer"],
            "advisory_channel": ["advisory_channel", "asesoriadigital"],
            "gov": ["gov", "ministry", "ministerio"],
            "industry": ["industry", "industria", "giro"],
            "doc_type": ["doc_type"],
            "government_sector": ["government_sector", "goes"],
            "collections_eligible": ["collections_eligible", "procede_a_cobrar"],
        }

    @staticmethod
    def _build_segment_dimension(df: pd.DataFrame, dpd: pd.Series, dimension: str) -> pd.Series:
        normalized = (dimension or "risk_band").strip().lower()
        if normalized == "risk_band":
            return KPIService._build_risk_band_series(df, dpd)
        if normalized == "ticket_size_band":
            return KPIService._build_ticket_size_band_series(df)
        if normalized == "payment_frequency":
            return df.get(
                "payment_frequency", pd.Series(["unknown"] * len(df), index=df.index)
            ).fillna("unknown")
        if normalized == "loan_status":
            return df.get("loan_status", pd.Series(["unknown"] * len(df), index=df.index)).fillna(
                "unknown"
            )
        aliases_map = KPIService._segment_aliases()
        if normalized in aliases_map:
            return KPIService._series_from_aliases(df, aliases_map[normalized])
        if normalized == "origination_month":
            return KPIService._build_month_period_series(df, "origination_date")
        if normalized == "application_month":
            return KPIService._build_month_period_series(df, "application_date")
        if normalized == "utilization_band":
            return KPIService._build_utilization_band_series(df)
        return pd.Series(["unknown"] * len(df), index=df.index, dtype=object)

    @staticmethod
    def _derive_dpd_series(df: pd.DataFrame, dpd_column: str, status_column: str) -> pd.Series:
        if (
            dpd_column in df.columns
            and pd.to_numeric(df[dpd_column], errors="coerce").notna().any()
        ):
            return pd.to_numeric(df[dpd_column], errors="coerce").fillna(0.0).clip(lower=0.0)
        status = (
            df.get(status_column, pd.Series([""] * len(df), index=df.index)).astype(str).str.lower()
        )
        dpd = pd.Series([0.0] * len(df), index=df.index, dtype=float)
        dpd = dpd.mask(status.str.contains(STATUS_PATTERN_90_PLUS, regex=True, na=False), 100.0)
        dpd = dpd.mask(status.str.contains(STATUS_PATTERN_60_89, regex=True, na=False), 75.0)
        dpd = dpd.mask(status.str.contains(STATUS_PATTERN_30_59, regex=True, na=False), 45.0)
        return dpd

    @staticmethod
    def _map_dpd_to_bucket(dpd_value: float) -> str:
        if dpd_value <= 0:
            return "current"
        if dpd_value <= 30:
            return "1_30"
        if dpd_value <= 60:
            return "31_60"
        if dpd_value <= 90:
            return "61_90"
        return "90_plus"

    @staticmethod
    def _bucket_order() -> list[str]:
        return ["current", "1_30", "31_60", "61_90", "90_plus"]

    @property
    def _bucket_severity(self) -> dict[str, int]:
        return {"current": 0, "1_30": 1, "31_60": 2, "61_90": 3, "90_plus": 4}

    def _load_nsm_recurrent_tpv_sync(self) -> NSMRecurrentTPVResponse:
        runs_dir = Path("logs/runs")
        if not runs_dir.is_dir():
            return NSMRecurrentTPVResponse()
        run_dirs = [p for p in runs_dir.iterdir() if p.is_dir()]
        if not run_dirs:
            return NSMRecurrentTPVResponse()
        latest_run = max(run_dirs, key=lambda p: p.stat().st_mtime)
        nsm_path = latest_run / "nsm_recurrent_tpv.json"
        if not nsm_path.exists():
            nsm_path = latest_run / "nsm_recurrent_tpv_output.json"
        if not nsm_path.exists():
            return NSMRecurrentTPVResponse()
        with open(nsm_path, encoding="utf-8") as f:
            data = json.load(f)
        by_period = {
            period: NSMPeriodMetrics(period=period, **metrics)
            for period, metrics in data.get("by_period", {}).items()
        }
        latest_period = data.get("latest_period")
        latest_raw = data.get("latest")
        latest = (
            NSMPeriodMetrics(period=latest_period, **latest_raw)
            if latest_period and latest_raw
            else None
        )
        return NSMRecurrentTPVResponse(
            latest_period=latest_period, latest=latest, by_period=by_period
        )

    async def get_nsm_recurrent_tpv(self) -> NSMRecurrentTPVResponse:
        return await run_in_threadpool(self._load_nsm_recurrent_tpv_sync)
