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

KPI_DEFINITIONS_PATH = Path(__file__).resolve().parents[4] / "config" / "kpis" / "kpi_definitions.yaml"

KPI_API_TO_CATALOG_ID = {
    "PAR30": "par_30",
    "PAR_30": "par_30",
    "PAR90": "par_90",
    "PAR_90": "par_90",
    "COLLECTION_RATE": "collections_rate",
    "PORTFOLIO_YIELD": "portfolio_yield",
    "PORTFOLIO_HEALTH": "portfolio_growth_rate",
    "AUM": "total_outstanding_balance",
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
    "RECOVERY_RATE": {
        "formula": "SUM(recovery_value) / SUM(defaulted_principal_balance) * 100",
        "definition": "Recovered value as a share of defaulted exposure.",
        "implications": "Higher recoveries reduce realized loss severity and provisioning pressure.",
    },
    "CONCENTRATION_HHI": {
        "formula": "SUM((borrower_exposure / total_exposure)^2) * 10000",
        "definition": "Herfindahl-Hirschman index for borrower concentration risk.",
        "implications": "Higher HHI indicates concentration and lower diversification resilience.",
    },
    "REPEAT_BORROWER_RATE": {
        "formula": "COUNT(borrowers_with_more_than_one_loan) / COUNT(unique_borrowers) * 100",
        "definition": "Share of borrowers with repeat borrowing activity.",
        "implications": "Repeat activity can signal retention strength but may amplify concentration risk.",
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
    "TOTAL_LOANS_COUNT": {
        "formula": "COUNT(loans)",
        "definition": "Total number of loans represented in the analyzed population.",
        "implications": "Loan-count growth changes operational load and may require capacity planning.",
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
            "Use trend and segment context when interpreting this KPI."
            f"{threshold_note}"
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
            "PortfolioHealth": ["AUM", "portfolio_growth_rate"],
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
            df["customer_id"] = [
                customer_ids[idx % len(customer_ids)] for idx in range(len(df))
            ]
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

            def build_kpi_response(kpi_id: str, name: str, value: float, unit: str) -> KpiSingleResponse:
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
                    "PORTFOLIO_YIELD",
                    "Weighted Average Interest Rate",
                    results["yield"] * 100,
                    "%",
                ),
                build_kpi_response("AUM", "Assets Under Management", results["aum"], "USD"),
                build_kpi_response("AVG_LTV", "Average Loan-to-Value", results["avg_ltv"], "%"),
                build_kpi_response("AVG_DTI", "Average Debt-to-Income", results["avg_dti"], "%"),
                build_kpi_response("DEFAULT_RATE", "Default Rate", results["default_rate"], "%"),
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
        total_outstanding = df["principal_balance"].sum()

        # DPD mapping
        def get_dpd_category(status: str) -> int:
            if "30-59" in status:
                return 45
            if "60-89" in status:
                return 75
            return 100 if "90+" in status else 0

        df["dpd"] = df["loan_status"].apply(get_dpd_category)

        # PAR
        par30_val = df[df["dpd"] > 30]["principal_balance"].sum()
        par30_pct = (par30_val / total_outstanding * 100) if total_outstanding > 0 else 0
        par90_val = df[df["dpd"] > 90]["principal_balance"].sum()
        par90_pct = (par90_val / total_outstanding * 100) if total_outstanding > 0 else 0

        # Default rate
        default_mask = df["loan_status"].str.contains(r"default|charged.off", case=False, na=False)
        default_rate_pct = (default_mask.sum() / len(df) * 100) if len(df) > 0 else 0

        # Yield
        weighted_interest = (df["interest_rate"] * df["principal_balance"]).sum()
        avg_interest_rate = (weighted_interest / total_outstanding) if total_outstanding > 0 else 0

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

        return {
            "par30": par30_pct,
            "par90": par90_pct,
            "default_rate": default_rate_pct,
            "yield": avg_interest_rate,
            "aum": total_outstanding,
            "avg_ltv": df["ltv_ratio"].mean(),
            "avg_dti": df["dti_ratio"].mean(),
            "count": float(len(df)),
        }
