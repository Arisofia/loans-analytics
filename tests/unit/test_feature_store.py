"""Tests for the feature store modules."""

from __future__ import annotations

import pandas as pd
import pytest

from backend.python.multi_agent.feature_store.campaign_features import (
    build_campaign_features,
)
from backend.python.multi_agent.feature_store.treasury_features import (
    build_treasury_features,
)


@pytest.fixture()
def mart_data() -> dict:
    return {
        "marketing": pd.DataFrame(
            {
                "canal_origen": ["web", "branch", "referral", "web", "web"],
                "monto_desembolsado": [10_000, 20_000, 15_000, 25_000, 30_000],
                "fecha_desembolso": pd.to_datetime(
                    ["2024-01-01", "2024-01-15", "2024-02-01", "2024-02-15", "2024-03-01"]
                ),
            }
        ),
        "treasury": pd.DataFrame(
            {
                "saldo_actual": [900_000],
                "cuota_mensual": [50_000],
                "pagos_realizados": [10],
                "pagos_esperados": [12],
            }
        ),
    }


class TestCampaignFeatures:
    def test_returns_dataframe(self, mart_data: dict):
        result = build_campaign_features(mart_data.get("marketing"))
        assert isinstance(result, pd.DataFrame)

    def test_has_rows(self, mart_data: dict):
        result = build_campaign_features(mart_data.get("marketing"))
        assert len(result) >= 1


class TestTreasuryFeatures:
    def test_returns_dict(self, mart_data: dict):
        result = build_treasury_features(mart_data.get("treasury"))
        assert isinstance(result, dict)

    def test_has_expected_keys(self, mart_data: dict):
        result = build_treasury_features(mart_data.get("treasury"))
        assert len(result) >= 1
