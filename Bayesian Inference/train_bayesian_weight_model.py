from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

from bayesian_weight_model import (
    FEATURE_COLUMNS,
    BayesianWeightModel,
    prepare_data,
    save_model,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train Bayesian weight model")
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--epochs", type=int, default=200)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--model-path", type=Path, default=Path("bayesian_weight_model.pkl"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    data = pd.read_csv(args.data)

    prepared = prepare_data(data)
    dataset = TensorDataset(
        torch.from_numpy(prepared.features),
        torch.from_numpy(prepared.targets).unsqueeze(1),
    )
    loader = DataLoader(dataset, batch_size=args.batch_size, shuffle=True)

    model = BayesianWeightModel(input_dim=len(FEATURE_COLUMNS))
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)
    loss_fn = nn.MSELoss()

    model.train()
    for epoch in range(args.epochs):
        epoch_loss = 0.0
        for batch_features, batch_targets in loader:
            optimizer.zero_grad()
            predictions = model(batch_features)
            loss = loss_fn(predictions, batch_targets)
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item() * batch_features.size(0)

        if (epoch + 1) % 25 == 0:
            avg_loss = epoch_loss / len(dataset)
            print(f"Epoch {epoch + 1}: loss={avg_loss:.4f}")

    save_model(model, prepared.scaler, args.model_path)
    print(f"Saved model to {args.model_path}")


if __name__ == "__main__":
    main()
