from __future__ import annotations

from datetime import datetime
from functools import lru_cache
from pathlib import Path

import pandas as pd
from starlette.concurrency import run_in_threadpool

from python.apps.analytics.api.models import (
    AdvancedRiskResponse,
    DataQualityResponse,
    KpiContext,
    KpiSingleResponse,
    LoanRecord,
    ValidationResponse,
)
from python.config import settings
from python.kpis.advanced_risk import calculate_advanced_risk_metrics
from python.kpis.catalog_processor import KPICatalogProcessor
from python.logging_config import get_logger
from python.supabase_pool import get_pool

logger = get_logger(__name__)

try:
    import yaml
except ImportError:  # pragma: no cover - optional dependency for catalog enrichment
    yaml = None

KPI_DEFINITIONS_PATH = (
    Path(__file__).resolve().parents[4] / "config" / "kpis" / "kpi_definitions.yaml"
)

KPI_API_TO_CATALOG_ID = {
    "PAR30": "par_30",
    "PAR_30": "par_30",
    "PAR90": "par_90",
    "PAR_90": "par_90",
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

DEFAULT_KPI_METADATA = {
    "PAR30": {
        "formula": "SUM(principal_balance WHERE dpd > 30) / SUM(principal_balance) * 100",
        "definition": "Portfolio at Risk with more than 30 days past due.",
        "implications": "Higher PAR30 indicates deteriorating portfolio quality and collections pressure.",
    },
    "PAR90": {
        "formula": "SUM(principal_balance WHERE dpd > 90) / SUM(principal_balance) * 100",
        "definition": "Portfolio at Risk with more than 90 days past due.",
        "implications": "Higher PAR90 signals severe delinquency and elevated expected credit losses.",
    },
    "PAR60": {
        "formula": "SUM(principal_balance WHERE dpd > 60) / SUM(principal_balance) * 100",
        "definition": "Portfolio at Risk with more than 60 days past due.",
        "implications": "Rising PAR60 is an early warning for migration into severe delinquency buckets.",
    },
    "COLLECTION_RATE": {
        "formula": "SUM(collected_amount) / SUM(scheduled_amount) * 100",
        "definition": "Collection efficiency against scheduled amounts.",
        "implications": "Lower collection rate reduces cash conversion and may indicate process weaknesses.",
    },
    "LOSS_RATE": {
        "formula": "SUM(principal_balance WHERE status = defaulted) / SUM(loan_amount) * 100",
        "definition": "Defaulted outstanding exposure as a share of total originated principal.",
        "implications": "Higher loss rate increases provisioning needs and can pressure capital ratios.",
    },
    "RECOVERY_RATE": {
        "formula": "SUM(recovery_value WHERE status = defaulted) / SUM(principal_balance WHERE status = defaulted) * 100",
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
        "formula": "COUNT(loans)",
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
}


def _normalize_kpi_key(kpi_id: str) -> str:
    return (kpi_id or "").strip().replace("-", "_").replace(" ", "_").upper()


def _extract_kpi_metadata(kpi_id: str, kpi_def: dict) -> dict[str, str]:
    """Helper to extract and format metadata from a single KPI definition."""
    thresholds = kpi_def.get("thresholds")
    threshold_note = ""
    if isinstance(thresholds, dict) and thresholds:
        threshold_pairs = ", ".join(f"{k}={v}" for k, v in thresholds.items())
        threshold_note = f" Compare against configured thresholds ({threshold_pairs})."

    return {
        "formula": str(kpi_def.get("formula", "")),
        "definition": str(kpi_def.get("description", "")),
        "implications": (
            "Use trend and segment context when interpreting this KPI." f"{threshold_note}"
        ),
    }


@lru_cache(maxsize=1)
def _load_catalog_kpi_metadata() -> dict[str, dict[str, str]]:
    if yaml is None or not KPI_DEFINITIONS_PATH.exists():
        return {}

    try:
        with open(KPI_DEFINITIONS_PATH, encoding="utf-8") as handle:
            payload = yaml.safe_load(handle) or {}
    except Exception as exc:  # pragma: no cover - defensive parsing fallback
        logger.warning("Failed to load KPI catalog metadata: %s", exc)
        return {}

    metadata: dict[str, dict[str, str]] = {}
    for top_key, section in payload.items():
        if not top_key.endswith("_kpis") or not isinstance(section, dict):
            continue

        for kpi_id, kpi_def in section.items():
            if isinstance(kpi_def, dict):
                metadata[kpi_id.lower()] = _extract_kpi_metadata(kpi_id, kpi_def)

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
            "PAR90": ["PAR90", "par_90"],
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
            "LTV": ["AVG_LTV", "average_loan_size"],
            "DTI": ["AVG_DTI", "default_rate"],
            "PortfolioYield": ["PORTFOLIO_YIELD", "portfolio_yield"],
        }

    def _get_kpi_metadata(self, kpi_id: str, kpi_name: str | None = None) -> dict[str, str]:
        normalized = _normalize_kpi_key(kpi_id)
        catalog_key = KPI_API_TO_CATALOG_ID.get(normalized, str(kpi_id).lower())
        catalog_metadata = _load_catalog_kpi_metadata().get(catalog_key, {})
        default_metadata = DEFAULT_KPI_METADATA.get(normalized, {})
        definition_fallback = kpi_name or str(kpi_id)
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
        }

    async def get_latest_kpis(self, kpi_keys: list[str] | None = None) -> list[KpiSingleResponse]:
        """
        Fetch the latest KPI values from the database.

        Args:
            kpi_keys: Optional list of KPI keys to filter by.

        Returns:
            List of KpiSingleResponse objects.
        """
        pool = await get_pool(settings.database_url)

        query = """
            SELECT
                v.kpi_name as id,
                v.kpi_name as name,
                v.kpi_value as value,
                '%' as unit,
                v.run_date as as_of_date,
                v.timestamp as created_at
            FROM public.kpi_timeseries_daily v
            WHERE v.id IN (
                SELECT MAX(id)
                FROM public.kpi_timeseries_daily
                GROUP BY kpi_name
            )
        """

        params = []
        if kpi_keys:
            # Map API keys to pipeline names if needed
            # For now, assume they match or are handled by the caller
            query += " AND v.kpi_name = ANY($1)"
            params.append(kpi_keys)

        try:
            records = await pool.fetch(query, *params)

            responses = []
            for rec in records:
                kpi_id = str(rec["id"])
                kpi_name = str(rec["name"])
                metadata = self._get_kpi_metadata(kpi_id, kpi_name)
                # Handle potential string or date/datetime objects
                as_of_date = rec["as_of_date"]
                if hasattr(as_of_date, "isoformat"):
                    as_of_date_str = as_of_date.isoformat()
                else:
                    as_of_date_str = str(as_of_date)

                formula = metadata["formula"]
                responses.append(
                    KpiSingleResponse(
                        id=kpi_id,
                        name=kpi_name,
                        value=float(rec["value"]),
                        unit=rec["unit"],
                        formula=formula,
                        definition=metadata["definition"],
                        implications=metadata["implications"],
                        context=KpiContext(
                            metric=kpi_name,
                            timestamp=rec["created_at"],
                            formula=formula,
                            sample_size=0,
                            period="latest",
                            calculation_date=rec["created_at"],
                            filters={"as_of_date": as_of_date_str},
                        ),
                    )
                )

            return responses
        except Exception as e:
            logger.error(
                "Error fetching KPIs for actor %s: %s",
                self.actor,
                e,
                exc_info=True,
            )
            raise

    async def get_kpi_by_id(self, kpi_id: str) -> KpiSingleResponse | None:
        """Fetch a specific KPI by its ID."""
        kpis = await self.get_latest_kpis(kpi_keys=[kpi_id])
        return kpis[0] if kpis else None

    async def get_risk_alerts(
        self,
        loans: list[LoanRecord] | None,
        ltv_threshold: float = 80.0,
        dti_threshold: float = 50.0,
    ) -> list[dict]:
        """
        Calculates high-risk loans based on LTV and DTI thresholds from an incoming list of
        LoanRecord objects.
        """
        try:
            if loans is None:
                return []
            df = await run_in_threadpool(self._convert_loan_records_to_dataframe, loans)

            if df.empty:
                return []

            df = self._calculate_loan_risk_metrics(df)

            # Identify high-risk loans
            high_risk_df = df[
                (df["ltv"] > ltv_threshold)
                | (df["dti"] > dti_threshold)
                | (df["days_past_due"] > 30)
            ]

            risk_loans: list[dict] = []
            for _, rec in high_risk_df.iterrows():
                risk_loans.append(self._build_loan_risk_alert(rec, ltv_threshold, dti_threshold))

            return risk_loans
        except Exception as e:
            logger.error(
                "Error calculating risk alerts for actor %s: %s",
                self.actor,
                e,
                exc_info=True,
            )
            raise

    def _calculate_loan_risk_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """Helper to compute LTV, DTI and DPD for risk analysis."""
        # Calculate LTV and DTI for each loan (optional for invoice factoring)
        if "appraised_value" in df.columns and df["appraised_value"].notna().any():
            df["ltv"] = (df["principal_balance"] / df["appraised_value"] * 100).fillna(0)
        else:
            df["ltv"] = 0.0

        if (
            "monthly_debt" in df.columns
            and "borrower_income" in df.columns
            and df["borrower_income"].notna().any()
        ):
            df["dti"] = (df["monthly_debt"] / df["borrower_income"] * 100).fillna(0)
        else:
            df["dti"] = 0.0

        # Assuming 'loan_status' can be mapped to days past due for risk calculation
        def get_dpd(status: str) -> int:
            if "30-59" in status:
                return 45
            if "60-89" in status:
                return 75
            return 100 if "90+" in status else 0

        df["days_past_due"] = df["loan_status"].apply(get_dpd)
        return df

    def _build_loan_risk_alert(
        self, rec: pd.Series, ltv_threshold: float, dti_threshold: float
    ) -> dict:
        """Helper to build a single loan risk alert dictionary."""
        ltv = rec["ltv"]
        dti = rec["dti"]
        dpd = rec["days_past_due"]

        # Simple risk score: weighted average of LTV, DTI and DPD impact
        risk_score = (ltv / 100 * 0.3) + (dti / 100 * 0.3) + (dpd / 100 * 0.4)
        risk_score = min(100.0, risk_score * 100)  # Normalize to 0-100

        alerts = []
        if ltv > ltv_threshold:
            alerts.append(f"LTV {ltv:.1f}% exceeds threshold {ltv_threshold}%")
        if dti > dti_threshold:
            alerts.append(f"DTI {dti:.1f}% exceeds threshold {dti_threshold}%")
        if dpd > 30:
            alerts.append(f"DPD {dpd} indicates high credit risk")

        return {
            "loan_id": rec["id"],
            "risk_score": round(float(risk_score), 2),
            "alerts": alerts,
        }

    def _convert_loan_records_to_dataframe(self, loans: list[LoanRecord]) -> pd.DataFrame:
        """Converts a list of LoanRecord Pydantic models to a Pandas DataFrame."""
        return pd.DataFrame([loan.model_dump() for loan in loans])

    def _convert_dict_records_to_dataframe(self, rows: list[dict] | None) -> pd.DataFrame:
        """Converts optional list-of-dict rows into a DataFrame."""
        if not rows:
            return pd.DataFrame()
        return pd.DataFrame(rows)

    async def get_executive_analytics(
        self,
        loans: list[LoanRecord],
        payments: list[dict] | None = None,
        customers: list[dict] | None = None,
        schedule: list[dict] | None = None,
    ) -> dict:
        """Build strategic analytics for CAC/LTV/margins/churn/forecast/opportunities."""
        try:
            return await run_in_threadpool(
                self._calculate_executive_analytics_sync,
                loans,
                payments,
                customers,
                schedule,
            )
        except Exception as e:
            logger.error(
                "Error generating executive analytics for actor %s: %s",
                self.actor,
                e,
                exc_info=True,
            )
            raise

    def _calculate_executive_analytics_sync(
        self,
        loans: list[LoanRecord],
        payments: list[dict] | None = None,
        customers: list[dict] | None = None,
        schedule: list[dict] | None = None,
    ) -> dict:
        """Synchronous strategic analytics computation helper."""
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
        return {
            "strategic_confirmations": extended_kpis.get("strategic_confirmations", {}),
            "executive_strip": extended_kpis.get("executive_strip", {}),
            "churn_90d_metrics": extended_kpis.get("churn_90d_metrics", []),
            "unit_economics": extended_kpis.get("unit_economics", []),
            "pricing_analytics": extended_kpis.get("pricing_analytics", {}),
            "revenue_forecast_6m": extended_kpis.get("revenue_forecast_6m", []),
            "opportunity_prioritization": extended_kpis.get("opportunity_prioritization", []),
            "data_governance": extended_kpis.get("data_governance", {}),
        }

    def _normalize_loans_for_catalog(
        self,
        loans_df: pd.DataFrame,
        payments_df: pd.DataFrame,
        customers_df: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Adapt LoanRecord schema to KPI catalog expected fields.

        LoanRecord is intentionally compact for API consumers; this bridge creates
        compatible aliases so strategic analytics can still run.
        """
        if loans_df.empty:
            return loans_df

        normalized = loans_df.copy()
        normalized = self._apply_balance_aliases(normalized)
        normalized = self._apply_entity_identifiers(normalized)
        normalized = self._apply_segment_date_defaults(normalized)
        normalized = self._apply_customer_mapping(normalized, payments_df, customers_df)

        return normalized

    def _apply_balance_aliases(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply required aliases for outstanding/principal/APR."""
        if "principal_balance" in df.columns and "outstanding_balance" not in df.columns:
            df["outstanding_balance"] = pd.to_numeric(
                df["principal_balance"],
                errors="coerce",
            ).fillna(0)
        if "loan_amount" in df.columns and "principal_amount" not in df.columns:
            df["principal_amount"] = pd.to_numeric(
                df["loan_amount"],
                errors="coerce",
            ).fillna(0)
        if "interest_rate" in df.columns and "interest_rate_apr" not in df.columns:
            df["interest_rate_apr"] = pd.to_numeric(
                df["interest_rate"],
                errors="coerce",
            ).fillna(0)
        return df

    def _apply_entity_identifiers(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply entity identifier logic."""
        if "id" in df.columns and "loan_id" not in df.columns:
            df["loan_id"] = df["id"].fillna("")
        if "loan_id" not in df.columns:
            df["loan_id"] = [f"loan-{idx + 1}" for idx in range(len(df))]
        return df

    def _apply_segment_date_defaults(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply segment and date fallbacks for prioritization/forecast windows."""
        if "client_segment" not in df.columns:
            df["client_segment"] = "general"
        if "origination_date" not in df.columns:
            df["origination_date"] = pd.Timestamp.now().floor("D")
        return df

    def _apply_customer_mapping(
        self,
        df: pd.DataFrame,
        payments_df: pd.DataFrame,
        customers_df: pd.DataFrame,
    ) -> pd.DataFrame:
        """Customer assignment fallback used by churn/CAC analytics."""
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
        """
        Calculates an overall data quality profile based on completeness, validity, and
        duplicates of an incoming list of LoanRecord objects.
        """
        try:
            if loans is None:
                return DataQualityResponse(
                    duplicate_ratio=0.0,
                    average_null_ratio=0.0,
                    invalid_numeric_ratio=0.0,
                    data_quality_score=100.0,
                    issues=["No data provided for real-time profiling."],
                )
            df = await run_in_threadpool(self._convert_loan_records_to_dataframe, loans)

            if df.empty:
                return DataQualityResponse(data_quality_score=100.0, issues=[])

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
        """Helper to compute standard data quality metrics."""
        total_records = len(df)

        # Duplicate Ratio
        duplicate_ratio = df.duplicated().sum() / total_records * 100.0

        # Average Null Ratio
        all_loan_record_columns = LoanRecord.model_fields.keys()
        null_counts = df[list(all_loan_record_columns)].isnull().sum()
        average_null_ratio = (
            null_counts.sum() / (total_records * len(all_loan_record_columns))
        ) * 100.0

        # Invalid Numeric Ratio (placeholder)
        invalid_numeric_ratio = 0.0

        # Overall Score - simple inverse of issues
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

    async def validate_loan_portfolio_schema(
        self,
        loans: list[LoanRecord] | None,
    ) -> ValidationResponse:
        """
        Validates the schema and data types of an incoming list of LoanRecord objects.
        """
        try:
            if loans is None:
                return ValidationResponse(valid=True, message="No loans provided to validate.")
            df = await run_in_threadpool(self._convert_loan_records_to_dataframe, loans)

            errors: list[str] = []
            required_columns = list(LoanRecord.model_fields.keys())

            # Check for missing columns in the DataFrame
            missing_cols = [col for col in required_columns if col not in df.columns]
            if missing_cols:
                errors.append(f"Missing required columns: {', '.join(missing_cols)}")

            # Basic type validation using pandas dtypes and explicit checks
            # This is a simplified example; full validation would be more extensive
            for field_name, field_info in LoanRecord.model_fields.items():
                if field_name not in df.columns:
                    continue  # Already reported missing

                if field_info.annotation is float:
                    # Check if column can be coerced to numeric. `validation.safe_numeric`
                    # could be used here.
                    if not pd.api.types.is_numeric_dtype(df[field_name]):
                        errors.append(f"Column '{field_name}' is not numeric.")
                elif field_info.annotation is str:
                    if not pd.api.types.is_string_dtype(df[field_name]):
                        errors.append(f"Column '{field_name}' is not string type.")
                elif field_info.annotation is datetime:
                    # Check if column can be parsed to datetime. `validation.validate_iso8601_dates`
                    # could be used here.
                    try:
                        pd.to_datetime(df[field_name], errors="raise")
                    except Exception:
                        errors.append(f"Column '{field_name}' contains invalid datetime format.")

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
        self,
        loans: list[LoanRecord] | None,
    ) -> list[KpiSingleResponse]:
        """Calculate KPIs in real-time for a specific portfolio subset from incoming loan data."""
        try:
            if loans is None:
                return []
            df = await run_in_threadpool(self._convert_loan_records_to_dataframe, loans)

            if df.empty:
                return []

            # Ensure numeric types and drop NaNs in critical columns
            numeric_cols = ["loan_amount", "principal_balance", "interest_rate"]
            for col in numeric_cols:
                df[col] = pd.to_numeric(df[col], errors="coerce")
            df.dropna(subset=numeric_cols, inplace=True)

            if df.empty:
                return []

            results = self._calculate_portfolio_performance_metrics(df)
            now = datetime.now()

            def build_kpi_response(
                kpi_id: str, name: str, value: float, unit: str
            ) -> KpiSingleResponse:
                metadata = self._get_kpi_metadata(kpi_id, name)
                formula = metadata["formula"]
                return KpiSingleResponse(
                    id=kpi_id,
                    name=name,
                    value=round(value, 2),
                    unit=unit,
                    formula=formula,
                    definition=metadata["definition"],
                    implications=metadata["implications"],
                    context=KpiContext(
                        metric=name,
                        timestamp=now,
                        formula=formula,
                        sample_size=len(loans),
                        period="on-demand",
                        calculation_date=now,
                        filters={"loan_count": len(loans)},
                    ),
                )

            return [
                build_kpi_response("PAR30", "Portfolio at Risk (30+ days)", results["par30"], "%"),
                build_kpi_response("PAR90", "Portfolio at Risk (90+ days)", results["par90"], "%"),
                build_kpi_response(
                    "COLLECTION_RATE",
                    "Collection Rate",
                    results["collection_rate"],
                    "%",
                ),
                build_kpi_response("LOSS_RATE", "Loss Rate", results["loss_rate"], "%"),
                build_kpi_response("RECOVERY_RATE", "Recovery Rate", results["recovery_rate"], "%"),
                build_kpi_response("CASH_ON_HAND", "Cash on Hand", results["cash_on_hand"], "USD"),
                build_kpi_response(
                    "PORTFOLIO_YIELD",
                    "Weighted Average Interest Rate",
                    results["yield"] * 100,
                    "%",
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
                "Error calculating real-time KPIs for actor %s: %s",
                self.actor,
                e,
                exc_info=True,
            )
            raise

    async def calculate_advanced_risk(
        self,
        loans: list[LoanRecord] | None,
    ) -> AdvancedRiskResponse:
        """Calculate advanced risk and portfolio quality metrics for the given loan set."""
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

    def _calculate_portfolio_performance_metrics(self, df: pd.DataFrame) -> dict:
        """Internal helper to calculate various portfolio metrics from a clean dataframe."""
        total_outstanding = float(df["principal_balance"].sum())
        total_originated = float(df["loan_amount"].sum())

        # DPD mapping
        def get_dpd_category(status: str) -> int:
            if "30-59" in status:
                return 45
            if "60-89" in status:
                return 75
            return 100 if "90+" in status else 0

        if (
            "days_past_due" in df.columns
            and pd.to_numeric(df["days_past_due"], errors="coerce").notna().any()
        ):
            df["dpd"] = pd.to_numeric(df["days_past_due"], errors="coerce").fillna(0)
        else:
            df["dpd"] = df["loan_status"].astype(str).apply(get_dpd_category)

        # PAR
        par30_val = float(df[df["dpd"] > 30]["principal_balance"].sum())
        par30_pct = (par30_val / total_outstanding * 100) if total_outstanding > 0 else 0
        par90_val = float(df[df["dpd"] > 90]["principal_balance"].sum())
        par90_pct = (par90_val / total_outstanding * 100) if total_outstanding > 0 else 0

        # Default rate
        default_mask = df["loan_status"].str.contains(r"default|charged.off", case=False, na=False)
        default_rate_pct = (default_mask.sum() / len(df) * 100) if len(df) > 0 else 0
        defaulted_balance = float(df.loc[default_mask, "principal_balance"].sum())
        loss_rate = (defaulted_balance / total_originated * 100) if total_originated > 0 else 0

        # Yield
        weighted_interest = float((df["interest_rate"] * df["principal_balance"]).sum())
        avg_interest_rate = (weighted_interest / total_outstanding) if total_outstanding > 0 else 0

        # Collection and recovery inputs from loan-level payment fields
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
        collection_rate = (
            (float(collected.sum()) / total_scheduled * 100) if total_scheduled > 0 else 0
        )
        recovery_raw = (
            pd.to_numeric(df["recovery_value"], errors="coerce").fillna(0)
            if "recovery_value" in df.columns
            else pd.Series([0.0] * len(df), index=df.index)
        )
        if float(recovery_raw.sum()) <= 0:
            recovery_raw = collected
        recovery_amount = float(recovery_raw[default_mask].sum())
        recovery_rate = (recovery_amount / defaulted_balance * 100) if defaulted_balance > 0 else 0

        cash_on_hand = (
            float(pd.to_numeric(df["current_balance"], errors="coerce").fillna(0).sum())
            if "current_balance" in df.columns
            else 0.0
        )
        average_loan_size = float(df["loan_amount"].mean()) if len(df) > 0 else 0.0

        # LTV/DTI
        if "appraised_value" in df.columns and df["appraised_value"].notna().any():
            df["ltv_ratio"] = (df["loan_amount"] / df["appraised_value"] * 100).fillna(0)
        else:
            df["ltv_ratio"] = 0.0

        if (
            "monthly_debt" in df.columns
            and "borrower_income" in df.columns
            and df["borrower_income"].notna().any()
        ):
            df["dti_ratio"] = (df["monthly_debt"] / df["borrower_income"] * 100).fillna(0)
        else:
            df["dti_ratio"] = 0.0

        if "borrower_id" in df.columns and df["borrower_id"].notna().any():
            borrower_series = df["borrower_id"].dropna().astype(str)
            active_mask = ~df["loan_status"].str.contains(
                r"closed|complete|paid|settled", case=False, na=False
            )
            active_borrowers = float(
                df.loc[active_mask, "borrower_id"].dropna().astype(str).nunique()
            )
            borrower_counts = borrower_series.value_counts()
            repeat_borrower_rate = (
                (float((borrower_counts > 1).sum()) / float(len(borrower_counts)) * 100)
                if len(borrower_counts) > 0
                else 0.0
            )
        else:
            active_borrowers = 0.0
            repeat_borrower_rate = 0.0

        if "payment_frequency" in df.columns:
            automated_mask = (
                df["payment_frequency"]
                .fillna("")
                .astype(str)
                .str.contains(r"bullet|auto", case=False, na=False)
            )
            automation_rate = (
                (float(automated_mask.sum()) / float(len(df)) * 100) if len(df) > 0 else 0
            )
        else:
            automation_rate = 0.0

        if (
            "term_months" in df.columns
            and pd.to_numeric(df["term_months"], errors="coerce").notna().any()
        ):
            processing_time_avg = float(
                pd.to_numeric(df["term_months"], errors="coerce").dropna().mean()
            )
        else:
            processing_time_avg = 0.0

        if "origination_date" in df.columns:
            origination_dates = pd.to_datetime(
                df["origination_date"], errors="coerce", utc=True
            ).dt.tz_convert(None)
            month_start = pd.Timestamp.now().normalize().replace(day=1)
            mtd_mask = origination_dates >= month_start
            disbursement_volume_mtd = float(df.loc[mtd_mask, "loan_amount"].sum())
            new_loans_count_mtd = float(mtd_mask.sum())
        else:
            disbursement_volume_mtd = 0.0
            new_loans_count_mtd = 0.0

        if "tpv" in df.columns and pd.to_numeric(df["tpv"], errors="coerce").notna().any():
            tpv_series = pd.to_numeric(df["tpv"], errors="coerce").fillna(0)
        else:
            tpv_series = pd.to_numeric(df["loan_amount"], errors="coerce").fillna(0)
        unique_borrowers = (
            float(df["borrower_id"].dropna().astype(str).nunique())
            if "borrower_id" in df.columns
            else 0.0
        )
        customer_lifetime_value = (
            float(tpv_series.sum()) / unique_borrowers if unique_borrowers > 0 else 0.0
        )
        executive_metrics = self._calculate_realtime_executive_metrics(df)

        return {
            "par30": par30_pct,
            "par90": par90_pct,
            "default_rate": default_rate_pct,
            "collection_rate": collection_rate,
            "loss_rate": loss_rate,
            "recovery_rate": recovery_rate,
            "cash_on_hand": cash_on_hand,
            "yield": avg_interest_rate,
            "aum": total_outstanding,
            "average_loan_size": average_loan_size,
            "disbursement_volume_mtd": disbursement_volume_mtd,
            "new_loans_count_mtd": new_loans_count_mtd,
            "customer_lifetime_value": customer_lifetime_value,
            "cac": executive_metrics["cac"],
            "gross_margin_pct": executive_metrics["gross_margin_pct"],
            "revenue_forecast_6m": executive_metrics["revenue_forecast_6m"],
            "churn_90d": executive_metrics["churn_90d"],
            "avg_ltv": df["ltv_ratio"].mean(),
            "avg_dti": df["dti_ratio"].mean(),
            "active_borrowers": active_borrowers,
            "repeat_borrower_rate": repeat_borrower_rate,
            "automation_rate": automation_rate,
            "processing_time_avg": processing_time_avg,
            "count": float(len(df)),
        }

    def _calculate_realtime_executive_metrics(self, df: pd.DataFrame) -> dict[str, float]:
        """
        Derive executive metrics (CAC, margin, forecast, churn) from the existing
        KPI catalog processor so the standard realtime endpoint can expose them.
        """
        try:
            normalized = self._normalize_loans_for_catalog(
                df.copy(),
                pd.DataFrame(),
                pd.DataFrame(),
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
            logger.warning("Executive KPI fallback failed in realtime path: %s", exc)
            return {
                "cac": 0.0,
                "gross_margin_pct": 0.0,
                "revenue_forecast_6m": 0.0,
                "churn_90d": 0.0,
            }

        executive_strip = extended.get("executive_strip", {}) or {}
        unit_economics = extended.get("unit_economics", []) or []
        churn_rows = extended.get("churn_90d_metrics", []) or []
        forecast_rows = extended.get("revenue_forecast_6m", []) or []

        def last_metric(rows: list[dict], key: str) -> float | None:
            for row in reversed(rows):
                value = row.get(key)
                if value is None:
                    continue
                if pd.isna(value):
                    continue
                return float(value)
            return None

        cac_value = self._safe_float(
            executive_strip.get("cac_usd"),
            default=last_metric(unit_economics, "cac_usd"),
        )
        margin_ratio = self._safe_float(
            executive_strip.get("gross_margin_pct"),
            default=last_metric(unit_economics, "gross_margin_pct"),
        )
        churn_ratio = self._safe_float(last_metric(churn_rows, "churn90d_pct"))
        forecast_sum = float(
            sum(
                self._safe_float(row.get("forecast_revenue_usd"))
                for row in forecast_rows
                if isinstance(row, dict)
            )
        )
        if forecast_sum <= 0 and isinstance(revenue_df, pd.DataFrame) and not revenue_df.empty:
            if "recv_revenue_for_month" in revenue_df.columns:
                revenue_series = pd.to_numeric(
                    revenue_df["recv_revenue_for_month"],
                    errors="coerce",
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
        """Convert ratio-like values (0-1) to percent while preserving percent inputs."""
        if pd.isna(value):
            return 0.0
        return float(value * 100.0) if -1.5 <= float(value) <= 1.5 else float(value)

    @staticmethod
    def _safe_float(value: float | int | None, default: float | None = 0.0) -> float:
        """Safely coerce optional numeric values to float."""
        candidate = default if value is None else value
        try:
            if candidate is None or pd.isna(candidate):
                return 0.0
            return float(candidate)
        except Exception:
            return 0.0
