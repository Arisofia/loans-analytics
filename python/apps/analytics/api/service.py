from __future__ import annotations

from datetime import datetime

import pandas as pd
from starlette.concurrency import run_in_threadpool

from python.apps.analytics.api.models import (
    DataQualityResponse,
    KpiContext,
    KpiSingleResponse,
    LoanRecord,
    ValidationResponse,
)
from python.config import settings
from python.kpis.catalog_processor import KPICatalogProcessor
from python.logging_config import get_logger
from python.supabase_pool import get_pool

logger = get_logger(__name__)


class KPIService:
    def __init__(self, actor: str = "api_user"):
        self.actor = actor

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
                # Handle potential string or date/datetime objects
                as_of_date = rec["as_of_date"]
                if hasattr(as_of_date, "isoformat"):
                    as_of_date_str = as_of_date.isoformat()
                else:
                    as_of_date_str = str(as_of_date)

                responses.append(
                    KpiSingleResponse(
                        id=rec["id"],
                        name=rec["name"],
                        value=float(rec["value"]),
                        unit=rec["unit"],
                        context=KpiContext(
                            metric=rec["name"],
                            timestamp=rec["created_at"],
                            formula="",
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

            risk_loans: list[dict] = []
            if df.empty:
                return risk_loans

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
            # This is a simplification; a real system would have a 'days_past_due' column
            def get_dpd(status: str) -> int:
                if "30-59" in status:
                    return 45
                if "60-89" in status:
                    return 75
                if "90+" in status:
                    return 100
                return 0

            df["days_past_due"] = df["loan_status"].apply(get_dpd)

            # Identify high-risk loans
            high_risk_df = df[
                (df["ltv"] > ltv_threshold)
                | (df["dti"] > dti_threshold)
                | (df["days_past_due"] > 30)
            ]

            for _, rec in high_risk_df.iterrows():
                # Calculate a mock risk score
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

                risk_loans.append(
                    {
                        "loan_id": rec["id"],  # Using the new 'id' field from LoanRecord
                        "risk_score": round(float(risk_score), 2),
                        "alerts": alerts,
                    }
                )

            return risk_loans
        except Exception as e:
            logger.error(
                "Error calculating risk alerts for actor %s: %s",
                self.actor,
                e,
                exc_info=True,
            )
            raise

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

        # Required aliases for outstanding/principal/APR.
        if "principal_balance" in normalized.columns and "outstanding_balance" not in normalized.columns:
            normalized["outstanding_balance"] = pd.to_numeric(
                normalized["principal_balance"],
                errors="coerce",
            ).fillna(0)
        if "loan_amount" in normalized.columns and "principal_amount" not in normalized.columns:
            normalized["principal_amount"] = pd.to_numeric(
                normalized["loan_amount"],
                errors="coerce",
            ).fillna(0)
        if "interest_rate" in normalized.columns and "interest_rate_apr" not in normalized.columns:
            normalized["interest_rate_apr"] = pd.to_numeric(
                normalized["interest_rate"],
                errors="coerce",
            ).fillna(0)

        # Entity identifiers.
        if "id" in normalized.columns and "loan_id" not in normalized.columns:
            normalized["loan_id"] = normalized["id"].fillna("")
        if "loan_id" not in normalized.columns:
            normalized["loan_id"] = [f"loan-{idx + 1}" for idx in range(len(normalized))]

        # Segment and date fallbacks for prioritization/forecast windows.
        if "client_segment" not in normalized.columns:
            normalized["client_segment"] = "general"
        if "origination_date" not in normalized.columns:
            normalized["origination_date"] = pd.Timestamp.now().floor("D")

        # Customer assignment fallback used by churn/CAC analytics.
        if "customer_id" not in normalized.columns:
            customer_ids: list[str] = []
            if not customers_df.empty and "customer_id" in customers_df.columns:
                customer_ids = (
                    customers_df["customer_id"].astype(str).dropna().unique().tolist()
                )
            elif not payments_df.empty and "customer_id" in payments_df.columns:
                customer_ids = payments_df["customer_id"].astype(str).dropna().unique().tolist()

            if customer_ids:
                normalized["customer_id"] = [
                    customer_ids[idx % len(customer_ids)]
                    for idx in range(len(normalized))
                ]
            else:
                normalized["customer_id"] = [f"cust-{idx + 1}" for idx in range(len(normalized))]

        return normalized

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

            total_records = len(df)
            if total_records == 0:
                return DataQualityResponse(data_quality_score=100.0, issues=[])

            # Duplicate Ratio
            duplicate_ratio = df.duplicated().sum() / total_records * 100.0

            # Average Null Ratio
            # We'll check for nulls across all expected columns from the LoanRecord model
            all_loan_record_columns = LoanRecord.model_fields.keys()
            null_counts = df[list(all_loan_record_columns)].isnull().sum()
            average_null_ratio = (
                null_counts.sum() / (total_records * len(all_loan_record_columns))
            ) * 100.0

            # Invalid Numeric Ratio (simplified example)
            # This would require more detailed validation from `validation.py`
            # For now, let's use a placeholder. Real implementation would involve iterating
            # through numeric columns and applying `validation.safe_numeric`.
            invalid_numeric_ratio = 0.0  # Placeholder

            # Overall Score - simple inverse of issues
            # A more sophisticated score would weigh different issues
            data_quality_score = 100.0 - (duplicate_ratio * 0.5 + average_null_ratio * 0.5)
            data_quality_score = max(0.0, data_quality_score)  # Ensure score is not negative

            issues = []
            if duplicate_ratio > 0:
                issues.append(f"Duplicate records found: {duplicate_ratio:.2f}%")
            if average_null_ratio > 0:
                issues.append(f"Average null values across columns: {average_null_ratio:.2f}%")

            return DataQualityResponse(
                duplicate_ratio=round(duplicate_ratio, 2),
                average_null_ratio=round(average_null_ratio, 2),
                invalid_numeric_ratio=round(invalid_numeric_ratio, 2),
                data_quality_score=round(data_quality_score, 2),
                issues=issues,
            )
        except Exception as e:
            logger.error(
                "Error calculating data quality profile for actor %s: %s",
                self.actor,
                e,
                exc_info=True,
            )
            raise

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

            # Ensure numeric types
            for col in ["loan_amount", "principal_balance", "interest_rate"]:
                df[col] = pd.to_numeric(df[col], errors="coerce")

            # Drop rows with NaN in critical calculation columns
            df.dropna(
                subset=["loan_amount", "principal_balance", "interest_rate"],
                inplace=True,
            )
            if df.empty:
                return []

            total_outstanding = df["principal_balance"].sum()

            # Placeholder for DPD (Days Past Due) logic
            # Needs to align with 'loan_status' enum from LoanRecord
            def get_dpd_category(status: str) -> int:
                if "30-59" in status:
                    return 45
                if "60-89" in status:
                    return 75
                if "90+" in status:
                    return 100
                return 0

            df["dpd"] = df["loan_status"].apply(get_dpd_category)

            # PAR30: % of outstanding value for loans with DPD > 30
            par30_val = df[df["dpd"] > 30]["principal_balance"].sum()
            par30_pct = (par30_val / total_outstanding * 100) if total_outstanding > 0 else 0

            # Weighted Average Interest Rate (Portfolio Yield proxy)
            weighted_interest_rate = (df["interest_rate"] * df["principal_balance"]).sum()
            avg_interest_rate = (
                (weighted_interest_rate / total_outstanding) if total_outstanding > 0 else 0
            )

            # LTV, DTI for average (optional for invoice factoring)
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
            avg_ltv = df["ltv_ratio"].mean()
            avg_dti = df["dti_ratio"].mean()

            now = datetime.now()
            context = KpiContext(
                metric="Portfolio Overview",
                timestamp=now,
                formula="PAR30, Yield, LTV, DTI",
                sample_size=len(loans),
                period="on-demand",
                calculation_date=now,
                filters={"loan_count": len(loans)},
            )

            return [
                KpiSingleResponse(
                    id="PAR30",
                    name="Portfolio at Risk (30+ days)",
                    value=round(float(par30_pct), 2),
                    unit="%",
                    context=context,
                ),
                KpiSingleResponse(
                    id="PORTFOLIO_YIELD",
                    name="Weighted Average Interest Rate",
                    # Convert to percentage
                    value=round(float(avg_interest_rate * 100), 2),
                    unit="%",
                    context=context,
                ),
                KpiSingleResponse(
                    id="AUM",
                    name="Assets Under Management",
                    value=round(float(total_outstanding), 2),
                    unit="USD",
                    context=context,
                ),
                KpiSingleResponse(
                    id="AVG_LTV",
                    name="Average Loan-to-Value",
                    value=round(float(avg_ltv), 2),
                    unit="%",
                    context=context,
                ),
                KpiSingleResponse(
                    id="AVG_DTI",
                    name="Average Debt-to-Income",
                    value=round(float(avg_dti), 2),
                    unit="%",
                    context=context,
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
