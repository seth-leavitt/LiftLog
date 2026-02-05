from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import torch

from bayesian_weight_model import (
    FEATURE_COLUMNS,
    BayesianWeightModel,
    build_features,
    load_model,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Predict with Bayesian weight model")
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--model-path", type=Path, default=Path("bayesian_weight_model.pkl"))
    parser.add_argument("--samples", type=int, default=50)
    parser.add_argument("--last-n", type=int, default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    data = pd.read_csv(args.data)
    if args.last_n is not None:
        data = data.tail(args.last_n)
    features_frame = build_features(data)
    last_row = features_frame.iloc[-1]
    feature_values = last_row[FEATURE_COLUMNS].to_numpy(dtype=np.float32)

    model, scaler = load_model(args.model_path, input_dim=len(FEATURE_COLUMNS))
    model.train()

    scaled_features = scaler.transform(feature_values.reshape(1, -1))
    feature_tensor = torch.from_numpy(scaled_features.astype(np.float32))

    samples = []
    for _ in range(args.samples):
        with torch.no_grad():
            prediction = model(feature_tensor).item()
            samples.append(prediction)

    mean = float(np.mean(samples))
    std = float(np.std(samples, ddof=1)) if len(samples) > 1 else 0.0
    lower = mean - 1.96 * std
    upper = mean + 1.96 * std

    print("Bayesian model prediction")
    print(f"Mean: {mean:.2f} kg")
    print(f"Std dev: {std:.2f} kg")
    print(f"95% interval: [{lower:.2f}, {upper:.2f}] kg")


if __name__ == "__main__":
    main()
