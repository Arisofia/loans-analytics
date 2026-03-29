from __future__ import annotations

from scripts.ml import train_scorecard


def test_origination_feature_set_excludes_behavioral_leakage_features() -> None:
    overlap = set(train_scorecard.ORIGINATION_FEATURES) & train_scorecard.LEAKY_BEHAVIORAL_FEATURES
    assert overlap == set()


def test_parse_args_default_feature_set_is_origination(monkeypatch) -> None:
    monkeypatch.setattr("sys.argv", ["train_scorecard.py"])
    args = train_scorecard.parse_args()
    assert args.feature_set == "origination"
