"""Invoice LTV (Loan-to-Value) calculation module.

Invoice LTV = capital_desembolsado / (valor_nominal_factura * (1 - tasa_dilucion))
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def calculate_ltv_sintetico(df: pd.DataFrame) -> pd.Series:
    """Calculate synthetic LTV and persist opacity metadata on the frame.

    LTV Sintetico = capital_desembolsado / (valor_nominal_factura * (1 - tasa_dilucion))

    Rows with non-positive or missing adjusted invoice value are marked opaque
    and produce NaN LTV values. The helper writes two columns in-place:
    - ltv_sintetico_is_opaque (0/1)
    - ltv_sintetico (float)
    """
    required = ("capital_desembolsado", "valor_nominal_factura", "tasa_dilucion")
    if not all(col in df.columns for col in required):
        return pd.Series(dtype=float)

    valor_nominal = pd.to_numeric(df["valor_nominal_factura"], errors="coerce")
    tasa_dilucion = pd.to_numeric(df["tasa_dilucion"], errors="coerce")
    capital = pd.to_numeric(df["capital_desembolsado"], errors="coerce")

    valor_ajustado = valor_nominal * (1 - tasa_dilucion)
    is_opaque = valor_ajustado.isna() | (valor_ajustado <= 0)
    ltv = np.where(is_opaque, np.nan, capital / valor_ajustado)

    df.loc[:, "ltv_sintetico_is_opaque"] = is_opaque.astype(int)
    df.loc[:, "ltv_sintetico"] = pd.Series(ltv, index=df.index, dtype=float)
    return df["ltv_sintetico"]
