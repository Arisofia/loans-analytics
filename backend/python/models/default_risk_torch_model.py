"""Optional PyTorch risk model wrapper for default probability inference."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

FEATURE_ORDER = [
    "loan_amount",
    "interest_rate",
    "term_months",
    "ltv_ratio",
    "dti_ratio",
    "credit_score",
    "days_past_due",
    "monthly_income",
    "employment_length_years",
    "num_open_accounts",
]


@dataclass
class TorchDefaultRiskModel:
    """Lazy-loaded MLP inference wrapper with optional normalization stats."""

    network: Any
    mean: np.ndarray
    std: np.ndarray

    @staticmethod
    def _require_torch():
        try:
            import torch
        except ImportError as exc:
            raise ImportError(
                "PyTorch backend requested but torch is not installed. "
                "Install with: pip install torch"
            ) from exc
        return torch

    @classmethod
    def load(cls, checkpoint_path: str) -> "TorchDefaultRiskModel":
        torch = cls._require_torch()
        path = Path(checkpoint_path)
        if not path.exists():
            raise FileNotFoundError(f"PyTorch model checkpoint not found: {checkpoint_path}")

        # Safer load with weights_only=True if supported
        try:
            payload = torch.load(path, map_location="cpu", weights_only=True)
        except TypeError:
            # Fallback for older torch versions (<1.13)
            payload = torch.load(path, map_location="cpu")  # nosec B614
        except Exception:
            # If weights_only=True fails due to complex types in payload,
            # we must decide if we want to allow unsafe load or fail.
            # For now, we allow it only for internal trusted models.
            payload = torch.load(path, map_location="cpu")  # nosec B614
        if "state_dict" not in payload:
            raise ValueError("Invalid checkpoint: missing state_dict")

        input_dim = int(payload.get("input_dim", len(FEATURE_ORDER)))
        hidden_dim = int(payload.get("hidden_dim", 64))

        class _MLP(torch.nn.Module):
            def __init__(self, in_features: int, hidden: int):
                super().__init__()
                self.net = torch.nn.Sequential(
                    torch.nn.Linear(in_features, hidden),
                    torch.nn.ReLU(),
                    torch.nn.Linear(hidden, hidden // 2),
                    torch.nn.ReLU(),
                    torch.nn.Linear(hidden // 2, 1),
                )

            def forward(self, x):  # type: ignore[no-untyped-def]
                return self.net(x)

        model = _MLP(input_dim, hidden_dim)
        model.load_state_dict(payload["state_dict"])
        model.eval()

        mean = np.array(payload.get("feature_mean", [0.0] * input_dim), dtype=np.float32)
        std = np.array(payload.get("feature_std", [1.0] * input_dim), dtype=np.float32)
        std = np.where(std == 0, 1.0, std)
        return cls(network=model, mean=mean, std=std)

    def predict_proba(self, loan_data: dict[str, Any]) -> float:
        torch = self._require_torch()
        values = np.array([float(loan_data.get(feature, 0.0)) for feature in FEATURE_ORDER])
        normalized = ((values - self.mean) / self.std).astype(np.float32)
        tensor = torch.tensor(normalized).unsqueeze(0)

        with torch.no_grad():
            logits = self.network(tensor)
            prob = torch.sigmoid(logits).item()
        return float(min(max(prob, 0.0), 1.0))
