import pandas as pd
import numpy as np
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)

class FinancialAnalyzer:
    def __init__(self):
        # Placeholder for payment processor dependency if needed
        pass

    def classify_dpd_buckets(self, df: pd.DataFrame, dpd_col: str = 'days_past_due') -> pd.DataFrame:
        """
        Clasifica los días de atraso en buckets estándar.
        """
        result = df.copy()
        if dpd_col not in result.columns:
            logger.warning(f"Columna {dpd_col} no encontrada para buckets DPD")
            return result
        
        # Ensure numeric
        result[dpd_col] = pd.to_numeric(result[dpd_col], errors='coerce').fillna(0)

        conditions = [
            (result[dpd_col] <= 0),
            (result[dpd_col] <= 29),
            (result[dpd_col] <= 59),
            (result[dpd_col] <= 89),
            (result[dpd_col] <= 119),
            (result[dpd_col] <= 149),
            (result[dpd_col] <= 179),
            (result[dpd_col] > 179)
        ]
        choices = ['Current', '1-29', '30-59', '60-89', '90-119', '120-149', '150-179', '180+']
        
        result['dpd_bucket'] = np.select(conditions, choices, default='Unknown')
        return result

    def segment_clients_by_exposure(self, df: pd.DataFrame, exposure_col: str = 'outstanding_balance') -> pd.DataFrame:
        """
        Segmenta clientes basado en su exposición (balance).
        """
        result = df.copy()
        if exposure_col not in result.columns:
            return result
            
        # Simple quantile-based segmentation or fixed thresholds
        # Using fixed thresholds as placeholder logic
        conditions = [
            (result[exposure_col] < 1000),
            (result[exposure_col] < 10000),
            (result[exposure_col] >= 10000)
        ]
        choices = ['Micro', 'Small', 'Medium/Large']
        result['exposure_segment'] = np.select(conditions, choices, default='Unknown')
        return result

    def classify_client_type(
        self,
        df: pd.DataFrame,
        customer_id_col: str = 'customer_id',
        loan_count_col: str = 'loan_count',
        last_active_col: str = 'last_active_date'
    ) -> pd.DataFrame:
        """
        Clasificar tipos de cliente: Nuevo, Recurrente, Recuperado.
        """
        result = df.copy()

        if customer_id_col not in result.columns:
            logger.error(f"Columna {customer_id_col} no encontrada en DataFrame")
            return result

        if loan_count_col in result.columns and last_active_col in result.columns:
            today = pd.to_datetime(datetime.now().date())
            result[last_active_col] = pd.to_datetime(result[last_active_col])
            result['days_since_active'] = (today - result[last_active_col]).dt.days

            conditions = [
                (result[loan_count_col] == 1),
                (result['days_since_active'] <= 90),
                (result['days_since_active'] > 90)
            ]
            choices = ['New', 'Recurring', 'Recovered']

            result['client_type'] = np.select(conditions, choices, default='Unknown')
        else:
            logger.warning("Faltan columnas de fecha para la clasificación de tipo de cliente")
            result['client_type'] = 'Unknown'

        return result

    def calculate_weighted_stats(
        self,
        loan_df: pd.DataFrame,
        weight_field: str = 'outstanding_balance',
        metrics: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Calculate weighted statistics (APR, EIR, Term) by OLB.
        """
        default_metrics = ['apr', 'eir', 'term']
        metrics = metrics or default_metrics

        # Check for required fields
        available_fields = [f for f in metrics if f in loan_df.columns or
                            any(f in col.lower() for col in loan_df.columns)]

        if not available_fields:
            logger.error(f"None of the required statistic fields found: {metrics}")
            return pd.DataFrame()

        if weight_field not in loan_df.columns:
            # Try to auto-detect weight field
            olb_patterns = ['outstanding_balance', 'olb', 'current_balance', 'saldo_actual', 'balance']
            detected_field = next((col for pattern in olb_patterns for col in loan_df.columns if pattern.lower() in col.lower()), None)

            if detected_field:
                logger.info(f"Using {detected_field} as weight field")
                weight_field = detected_field
            else:
                logger.error(f"Weight field not found in DataFrame")
                return pd.DataFrame()

        result = {}

        for stat in available_fields:
            stat_col = next((col for col in loan_df.columns if stat.lower() in col.lower()), None)

            if stat_col:
                filtered_df = loan_df.dropna(subset=[stat_col, weight_field])
                if not filtered_df.empty and filtered_df[weight_field].sum() > 0:
                    weighted_avg = np.average(filtered_df[stat_col], weights=filtered_df[weight_field])
                    result[f'weighted_{stat}'] = weighted_avg
                else:
                    logger.warning(f"No valid data for calculating weighted {stat}")

        return pd.DataFrame([result])

    def calculate_line_utilization(
        self,
        loan_df: pd.DataFrame,
        credit_line_field: str = 'line_amount',
        loan_amount_field: str = 'outstanding_balance'
    ) -> pd.DataFrame:
        """
        Calculate line utilization.
        """
        result_df = loan_df.copy()

        # Helper to find columns
        def find_col(patterns, df):
            return next((col for pattern in patterns for col in df.columns if pattern.lower() in col.lower()), None)

        if credit_line_field not in result_df.columns:
            credit_line_field = find_col(['line_amount', 'credit_line', 'line_limit', 'limite_credito'], result_df)
            if not credit_line_field:
                return result_df

        if loan_amount_field not in result_df.columns:
            loan_amount_field = find_col(['outstanding_balance', 'olb', 'current_balance', 'loan_amount'], result_df)
            if not loan_amount_field:
                return result_df

        # Coderabbit: Avoid division by zero; treat zero or negative credit line as NaN utilization
        result_df['line_utilization'] = np.where(
            result_df[credit_line_field] > 0,
            result_df[loan_amount_field] / result_df[credit_line_field],
            np.nan
        )
        # Clip utilization to [0.0, 1.0] to avoid negative and >100% values
        result_df['line_utilization'] = result_df['line_utilization'].clip(lower=0.0, upper=1.0)
        return result_df

    def calculate_hhi(
        self,
        loan_df: pd.DataFrame,
        customer_id_field: str,
        exposure_field: str = 'outstanding_balance'
    ) -> float:
        """
        Calculate HHI (Herfindahl-Hirschman Index) for exposure concentration.
        """
        if exposure_field not in loan_df.columns or customer_id_field not in loan_df.columns:
            return 0.0
            
        customer_exposure = loan_df.groupby(customer_id_field)[exposure_field].sum()
        total_exposure = customer_exposure.sum()

        if total_exposure == 0:
            return 0.0

        market_shares = customer_exposure / total_exposure
        hhi = (market_shares ** 2).sum()
        return hhi * 10000  # Scale to 0-10,000

    def enrich_master_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Aplicar todas las funciones de ingeniería de características al dataframe maestro.
        """
        result = df.copy()
        
        # Basic validation
        if 'outstanding_balance' not in result.columns:
             logger.warning("Missing outstanding_balance, skipping some enrichments")

        # 1. Buckets DPD
        result = self.classify_dpd_buckets(result)

        # 2. Segmentos
        result = self.segment_clients_by_exposure(result)

        # 3. Tipos de cliente
        if all(col in result.columns for col in ['customer_id', 'loan_count', 'last_active_date']):
            result = self.classify_client_type(result)

        # 4. Utilización
        result = self.calculate_line_utilization(result)

        # 5. Z-scores
        key_metrics = ['apr', 'term', 'days_past_due', 'outstanding_balance', 'line_utilization']
        for metric in key_metrics:
            if metric in result.columns and pd.api.types.is_numeric_dtype(result[metric]):
                std_dev = result[metric].std()
                if std_dev > 0:
                    result[f'{metric}_zscore'] = (result[metric] - result[metric].mean()) / std_dev

        return result