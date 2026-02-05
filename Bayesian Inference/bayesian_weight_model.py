from __future__ import annotations

import pickle
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from sklearn.preprocessing import StandardScaler
from torch import nn

FEATURE_COLUMNS = [
    "calories_in",
    "calories_out",
    "height_cm",
    "pr_total_kg",
    "exercise_count",
    "exercise_volume_kg",
    "weight_kg",
    "weight_kg_7d_avg",
]

TARGET_COLUMN = "next_weight_kg"


@dataclass
class PreparedData:
    features: np.ndarray
    targets: np.ndarray
    scaler: StandardScaler


class BayesianWeightModel(nn.Module):
    def __init__(self, input_dim: int, hidden_dim: int = 64, dropout: float = 0.15) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, 1),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


def build_features(data: pd.DataFrame) -> pd.DataFrame:
    frame = data.copy()
    frame = frame.sort_values("date")
    frame["weight_kg_7d_avg"] = frame["weight_kg"].rolling(7, min_periods=1).mean()
    frame["next_weight_kg"] = frame["weight_kg"].shift(-1)
    frame = frame.dropna(subset=["next_weight_kg"])
    return frame


def prepare_data(data: pd.DataFrame) -> PreparedData:
    features_frame = build_features(data)
    scaler = StandardScaler()
    features = scaler.fit_transform(features_frame[FEATURE_COLUMNS])
    targets = features_frame[TARGET_COLUMN].to_numpy(dtype=np.float32)
    return PreparedData(features=features.astype(np.float32), targets=targets, scaler=scaler)


def save_model(model: BayesianWeightModel, scaler: StandardScaler, path: Path) -> None:
    payload = {
        "state_dict": model.state_dict(),
        "scaler": scaler,
    }
    with path.open("wb") as handle:
        pickle.dump(payload, handle)


def load_model(path: Path, input_dim: int) -> tuple[BayesianWeightModel, StandardScaler]:
    with path.open("rb") as handle:
        payload = pickle.load(handle)
    model = BayesianWeightModel(input_dim=input_dim)
    model.load_state_dict(payload["state_dict"])
    return model, payload["scaler"]
