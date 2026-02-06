from typing import List, Optional
from datetime import datetime
from python.supabase_pool import get_pool
from python.apps.analytics.api.models import KpiSingleResponse, KpiContext
from python.logging_config import get_logger

logger = get_logger(__name__)

class KPIService:
    def __init__(self, actor: str = "api_user"):
        self.actor = actor

    async def get_latest_kpis(self, kpi_keys: Optional[List[str]] = None) -> List[KpiSingleResponse]:
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
                responses.append(KpiSingleResponse(
                    id=rec["id"],
                    name=rec["name"],
                    value=float(rec["value"]),
                    unit=rec["unit"],
                    context=KpiContext(
                        period="latest",
                        calculation_date=rec["created_at"],
                        filters={"as_of_date": rec["as_of_date"].isoformat()}
                    )
                ))
            
            return responses
        except Exception as e:
            logger.error(f"Error fetching KPIs for actor {self.actor}: {e}")
            raise

    async def get_kpi_by_id(self, kpi_id: str) -> Optional[KpiSingleResponse]:
        """Fetch a specific KPI by its ID."""
        kpis = await self.get_latest_kpis(kpi_keys=[kpi_id])
        return kpis[0] if kpis else None

    async def get_risk_alerts(self, ltv_threshold: float = 80.0, dti_threshold: float = 50.0) -> List[dict]:
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
                ltv = float(rec["outstanding_loan_value"] / rec["disbursement_amount"] * 100) if rec["disbursement_amount"] > 0 else 0
                dpd = rec["days_past_due"]
                risk_score = min(100, (ltv / 100 * 50) + (dpd / 90 * 50))
                
                alerts = []
                if ltv > ltv_threshold:
                    alerts.append(f"LTV {ltv:.1f}% exceeds threshold {ltv_threshold}%")
                if dpd > 30:
                    alerts.append(f"DPD {dpd} indicates high credit risk")

                risk_loans.append({
                    "loan_id": rec["loan_id"],
                    "risk_score": round(risk_score, 2),
                    "alerts": alerts
                })

            return risk_loans
        except Exception as e:
            logger.error(f"Error fetching risk alerts: {e}")
            raise

    async def get_data_quality_score(self) -> dict:
        """Calculate overall data quality score based on completeness and validity."""
        pool = await get_pool()

        query = """
            SELECT 
                count(*) as total,
                count(product_type) as product_type_count,
                count(currency) as currency_count,
                count(disbursement_date) as date_count
            FROM public.loan_data
        """

        try:
            rec = await pool.fetchrow(query)
            if not rec or rec["total"] == 0:
                return {"score": 100.0, "issues": []}

            total = rec["total"]
            score = (rec["product_type_count"] + rec["currency_count"] + rec["date_count"]) / (3 * total) * 100

            issues = []
            if rec["product_type_count"] < total:
                issues.append(f"Missing product_type for {total - rec['product_type_count']} loans")
            if rec["currency_count"] < total:
                issues.append(f"Missing currency for {total - rec['currency_count']} loans")

            return {"score": round(score, 2), "issues": issues}
        except Exception as e:
            logger.error(f"Error fetching data quality score: {e}")
            raise

    async def validate_portfolio(self, loan_ids: List[str]) -> dict:
        """Validate a specific portfolio subset."""
        # For now, just check if loans exist
        pool = await get_pool()
        query = "SELECT loan_id FROM public.loan_data WHERE loan_id = ANY($1)"

        try:
            records = await pool.fetch(query, loan_ids)
            found_ids = {r["loan_id"] for r in records}
            missing = [lid for lid in loan_ids if lid not in found_ids]

            if missing:
                return {"valid": False, "errors": [f"Loans not found: {', '.join(missing)}"]}
            return {"valid": True, "errors": []}
        except Exception as e:
            logger.error(f"Error validating portfolio: {e}")
            raise

    async def calculate_kpis_for_portfolio(self, loan_ids: List[str]) -> List[KpiSingleResponse]:
        """
        Calculate KPIs in real-time for a specific portfolio subset.

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
            total_disbursed = sum(rec["disbursement_amount"] for rec in records)

            # PAR30: % of outstanding value for loans with DPD > 30
            par30_val = sum(rec["outstanding_loan_value"] for rec in records if rec["days_past_due"] > 30)
            par30_pct = (par30_val / total_outstanding * 100) if total_outstanding > 0 else 0

            # Weighted APR
            weighted_apr = sum(rec["interest_rate_apr"] * rec["outstanding_loan_value"] for rec in records)
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
