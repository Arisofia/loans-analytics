from datetime import datetime
from typing import List, Optional, Any, Dict

import pandas as pd
from starlette.concurrency import run_in_threadpool

from python.supabase_pool import get_pool
from python.apps.analytics.api.models import (
    KpiSingleResponse, KpiContext, LoanRecord,
    DataQualityResponse, ValidationResponse, ErrorResponse
)
from python.logging_config import get_logger
from python import validation

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
        pool = await get_pool()

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
            logger.error(f"Error fetching KPIs for actor {self.actor}: {e}")
            raise

    async def get_kpi_by_id(self, kpi_id: str) -> Optional[KpiSingleResponse]:
        """Fetch a specific KPI by its ID."""
        kpis = await self.get_latest_kpis(kpi_keys=[kpi_id])
        return kpis[0] if kpis else None

    async def get_risk_alerts(
        self, ltv_threshold: float = 80.0, dti_threshold: float = 50.0
    ) -> List[dict]:
        """
        Fetch high-risk loans based on LTV and DTI thresholds.

        Note: Currently uses a simplified calculation as a placeholder.
        """
        pool = await get_pool()

        # Simplified query targeting high-risk indicators
        query = """
            SELECT 
                loan_id,
                outstanding_loan_value,
                disbursement_amount,
                days_past_due
            FROM public.loan_data
            WHERE (outstanding_loan_value / NULLIF(disbursement_amount, 0) * 100) > $1
               OR days_past_due > 30
            LIMIT 50
        """

        try:
            records = await pool.fetch(query, ltv_threshold)

            risk_loans = []
            for rec in records:
                # Calculate a mock risk score
                ltv = (
                    float(rec["outstanding_loan_value"] / rec["disbursement_amount"] * 100)
                    if rec["disbursement_amount"] > 0
                    else 0
                )
                dpd = rec["days_past_due"]
                risk_score = min(100, (ltv / 100 * 50) + (dpd / 90 * 50))

                alerts = []
                if ltv > ltv_threshold:
                    alerts.append(f"LTV {ltv:.1f}% exceeds threshold {ltv_threshold}%")
                if dpd > 30:
                    alerts.append(f"DPD {dpd} indicates high credit risk")

                risk_loans.append(
                    {
                        "loan_id": rec["loan_id"],
                        "risk_score": round(risk_score, 2),
                        "alerts": alerts,
                    }
                )

            return risk_loans
        except Exception as e:
            logger.error(f"Error fetching risk alerts: {e}")
            raise

    def _convert_loan_records_to_dataframe(self, loans: List[LoanRecord]) -> pd.DataFrame:
        """Converts a list of LoanRecord Pydantic models to a Pandas DataFrame."""
        return pd.DataFrame([loan.model_dump() for loan in loans])

    async def get_data_quality_profile(self, loans: List[LoanRecord]) -> DataQualityResponse:
        """
        Calculates an overall data quality profile based on completeness, validity, and duplicates
        of an incoming list of LoanRecord objects.
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
            average_null_ratio = (null_counts.sum() / (total_records * len(all_loan_record_columns))) * 100.0

            # Invalid Numeric Ratio (simplified example)
            # This would require more detailed validation from `validation.py`
            # For now, let's use a placeholder. Real implementation would involve iterating
            # through numeric columns and applying `validation.safe_numeric`.
            invalid_numeric_ratio = 0.0 # Placeholder

            # Overall Score - simple inverse of issues
            # A more sophisticated score would weigh different issues
            data_quality_score = 100.0 - (duplicate_ratio * 0.5 + average_null_ratio * 0.5)
            data_quality_score = max(0.0, data_quality_score) # Ensure score is not negative

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
                issues=issues
            )
        except Exception as e:
            logger.error(f"Error calculating data quality profile for actor {self.actor}: {e}")
            raise

    async def validate_loan_portfolio_schema(self, loans: List[LoanRecord]) -> ValidationResponse:
        """
        Validates the schema and data types of an incoming list of LoanRecord objects.
        """
        try:
            df = await run_in_threadpool(self._convert_loan_records_to_dataframe, loans)

            errors: List[str] = []
            required_columns = list(LoanRecord.model_fields.keys())
            
            # Check for missing columns in the DataFrame
            missing_cols = validation._missing_columns(df, required_columns)
            if missing_cols:
                errors.append(f"Missing required columns: {', '.join(missing_cols)}")
            
            # Basic type validation using pandas dtypes and explicit checks
            # This is a simplified example; full validation would be more extensive
            for field_name, field_info in LoanRecord.model_fields.items():
                if field_name not in df.columns:
                    continue # Already reported missing

                if field_info.annotation == float:
                    # Check if column can be coerced to numeric. `validation.safe_numeric` could be used here.
                    if not pd.api.types.is_numeric_dtype(df[field_name]):
                        errors.append(f"Column '{field_name}' is not numeric.")
                elif field_info.annotation == str:
                    if not pd.api.types.is_string_dtype(df[field_name]):
                        errors.append(f"Column '{field_name}' is not string type.")
                elif field_info.annotation == datetime:
                    # Check if column can be parsed to datetime. `validation.validate_iso8601_dates` could be used here.
                    try:
                        pd.to_datetime(df[field_name], errors='raise')
                    except Exception:
                        errors.append(f"Column '{field_name}' contains invalid datetime format.")

            if errors:
                return ValidationResponse(valid=False, errors=errors)
            return ValidationResponse(valid=True)
        except Exception as e:
            logger.error(f"Error validating loan portfolio schema for actor {self.actor}: {e}")
            raise


    async def calculate_kpis_for_portfolio(self, loan_ids: List[str]) -> List[KpiSingleResponse]:
        """Calculate KPIs in real-time for a specific portfolio subset.

        Note: Currently uses a simplified calculation for on-demand requests.
        """
        pool = await get_pool()

        query = """
            SELECT 
                loan_id,
                outstanding_loan_value,
                disbursement_amount,
                days_past_due,
                interest_rate_apr
            FROM public.loan_data
            WHERE loan_id = ANY($1)
        """

        try:
            records = await pool.fetch(query, loan_ids)
            if not records:
                return []

            total_outstanding = sum(rec["outstanding_loan_value"] for rec in records)

            # PAR30: % of outstanding value for loans with DPD > 30
            par30_val = sum(
                rec["outstanding_loan_value"]
                for rec in records
                if rec["days_past_due"] > 30
            )
            par30_pct = (par30_val / total_outstanding * 100) if total_outstanding > 0 else 0

            # Weighted APR
            weighted_apr = sum(
                rec["interest_rate_apr"] * rec["outstanding_loan_value"] for rec in records
            )
            avg_apr = (weighted_apr / total_outstanding) if total_outstanding > 0 else 0

            context = KpiContext(
                period="on-demand",
                calculation_date=datetime.now(),
                filters={"loan_count": len(records)}
            )

            return [
                KpiSingleResponse(
                    id="PAR30",
                    name="Portfolio at Risk (30+ days)",
                    value=round(float(par30_pct), 2),
                    unit="%",
                    context=context
                ),
                KpiSingleResponse(
                    id="PORTFOLIO_YIELD",
                    name="Weighted Average APR",
                    value=round(float(avg_apr), 2),
                    unit="%",
                    context=context
                ),
                KpiSingleResponse(
                    id="AUM",
                    name="Assets Under Management",
                    value=round(float(total_outstanding), 2),
                    unit="USD",
                    context=context
                )
            ]
        except Exception as e:
            logger.error(f"Error calculating real-time KPIs: {e}")
            raise