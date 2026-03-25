import logging
from typing import Dict, List, Optional
import numpy as np
import pandas as pd
logger = logging.getLogger(__name__)

class WoEIVEngine:

    def __init__(self, target_col: str='is_default') -> None:
        self.target_col = target_col

    def analyze_all(self, df: pd.DataFrame, feature_cols: List[str]) -> Dict[str, float]:
        iv_results = {}
        for feat in feature_cols:
            iv = self.compute_iv(df, feat)
            if iv is not None:
                iv_results[feat] = iv
        return dict(sorted(iv_results.items(), key=lambda x: x[1], reverse=True))

    def compute_iv(self, df: pd.DataFrame, feat: str) -> Optional[float]:
        try:
            from optbinning import OptimalBinning
        except ImportError:
            logger.error('optbinning not installed. Run pip install optbinning.')
            return None
        if feat not in df.columns or self.target_col not in df.columns:
            return None
        series = df[feat]
        y = df[self.target_col]
        mask = series.notna()
        if mask.sum() < 10:
            return None
        x_clean = series[mask].values
        y_clean = y[mask].values
        if len(np.unique(x_clean)) < 2:
            return None
        dtype = 'categorical' if series.dtype in (object, bool) else 'numerical'
        try:
            ob = OptimalBinning(name=feat, dtype=dtype, solver='cp', max_n_bins=8, min_bin_size=0.03)
            ob.fit(x_clean, y_clean)
            bt = ob.binning_table.build()
            iv_val = float(bt.loc[bt.index[:-1], 'IV'].sum())
            return round(iv_val, 4)
        except Exception as e:
            logger.warning('Binning failed for %s: %s', feat, e)
            return None

    def interpret_iv(self, iv: float) -> str:
        if iv < 0.02:
            return 'Inútil / Sin poder predictivo'
        elif iv < 0.1:
            return 'Débil'
        elif iv < 0.3:
            return 'Medio'
        elif iv < 0.5:
            return 'Fuerte'
        else:
            return 'Muy Fuerte (Cuidado: Posible Leakage)'
