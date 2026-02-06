from datetime import datetime
from typing import List, Optional

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
from python.logging_config import get_logger
from python.supabase_pool import get_pool

logger = get_logger(__name__)


class KPIService:
    def __init__(self, actor: str = "api_user"):
        self.actor = actor

    async def get_latest_kpis(
        self, kpi_keys: Optional[List[str]] = None
    ) -> List[KpiSingleResponse]:
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
                v.kpi_key as id,
                d.display_name as name,
                v.value,
                d.unit,
                v.as_of_date,
                v.created_at
            FROM public.kpi_values v
            JOIN public.kpi_definitions d ON v.kpi_key = d.kpi_key
            WHERE v.id IN (
                SELECT MAX(id)
                FROM public.kpi_values
                GROUP BY kpi_key
            )
        """

        params = []
        if kpi_keys:
            query += " AND v.kpi_key = ANY($1)"
            params.append(kpi_keys)

        try:
            records = await pool.fetch(query, *params)

            responses = []
            for rec in records:
                responses.append(
                    KpiSingleResponse(
                        id=rec["id"],
                        name=rec["name"],
                        value=float(rec["value"]),
                        unit=rec["unit"],
                        context=KpiContext(
                            period="latest",
                            calculation_date=rec["created_at"],
                            filters={"as_of_date": rec["as_of_date"].isoformat()},
                        ),
                    )
                )

            return responses
        except Exception as e:
            logger.error(
                "Error fetching KPIs for actor %s: %s",
                self.actor,
                e,
            )
            raise

    async def get_kpi_by_id(self, kpi_id: str) -> Optional[KpiSingleResponse]:
        """Fetch a specific KPI by its ID."""
        kpis = await self.get_latest_kpis(kpi_keys=[kpi_id])
        return kpis[0] if kpis else None

    async def get_risk_alerts(
        self,
        loans: List[LoanRecord],
        ltv_threshold: float = 80.0,
        dti_threshold: float = 50.0,
    ) -> List[dict]:
        """
        Calculates high-risk loans based on LTV and DTI thresholds from an incoming list of
        LoanRecord objects.
        """
        try:
            df = await run_in_threadpool(self._convert_loan_records_to_dataframe, loans)

            risk_loans = []
            if df.empty:
                return risk_loans

            # Calculate LTV and DTI for each loan
            df["ltv"] = (df["principal_balance"] / df["appraised_value"] * 100).fillna(0)
            df["dti"] = (df["monthly_debt"] / df["borrower_income"] * 100).fillna(0)

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
            )
            raise

    def _convert_loan_records_to_dataframe(self, loans: List[LoanRecord]) -> pd.DataFrame:
        """Converts a list of LoanRecord Pydantic models to a Pandas DataFrame."""
        return pd.DataFrame([loan.model_dump() for loan in loans])

    async def get_data_quality_profile(self, loans: List[LoanRecord]) -> DataQualityResponse:
        """
        Calculates an overall data quality profile based on completeness, validity, and
        duplicates of an incoming list of LoanRecord objects.
        """
        try:
            df = await run_in_threadpool(self._convert_loan_records_to_dataframe, loans)

            total_records = len(df)
            if total_records == 0:
                return DataQualityResponse(score=100.0, issues=[])

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
            )
            raise

    async def validate_loan_portfolio_schema(
        self,
        loans: List[LoanRecord],
    ) -> ValidationResponse:
        """
        Validates the schema and data types of an incoming list of LoanRecord objects.
        """
        try:
            df = await run_in_threadpool(self._convert_loan_records_to_dataframe, loans)

            errors: List[str] = []
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
            )
            raise

    async def calculate_kpis_for_portfolio(
        self,
        loans: List[LoanRecord],
    ) -> List[KpiSingleResponse]:
        """Calculate KPIs in real-time for a specific portfolio subset from incoming loan data."""
        try:
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

            # LTV, DTI for average
            df["ltv_ratio"] = (df["loan_amount"] / df["appraised_value"] * 100).fillna(0)
            df["dti_ratio"] = (df["monthly_debt"] / df["borrower_income"] * 100).fillna(0)
            avg_ltv = df["ltv_ratio"].mean()
            avg_dti = df["dti_ratio"].mean()

            context = KpiContext(
                period="on-demand",
                calculation_date=datetime.now(),
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
            )
            raise
