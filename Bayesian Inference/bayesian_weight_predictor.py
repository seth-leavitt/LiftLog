from __future__ import annotations

import argparse
from dataclasses import dataclass
from math import sqrt


KCAL_PER_KG = 7700.0


@dataclass(frozen=True)
class Prediction:
    mean_kg: float
    std_kg: float


@dataclass(frozen=True)
class DailyInputs:
    current_weight_kg: float
    calories_in: float
    calories_out: float
    prior_std_kg: float
    process_std_kg: float
    balance_std_kcal: float


def predict_next_day(inputs: DailyInputs) -> Prediction:
    net_calories = inputs.calories_in - inputs.calories_out
    mean_change = net_calories / KCAL_PER_KG
    balance_std_kg = inputs.balance_std_kcal / KCAL_PER_KG

    next_mean = inputs.current_weight_kg + mean_change
    next_variance = (
        inputs.prior_std_kg**2 + inputs.process_std_kg**2 + balance_std_kg**2
    )
    next_std = sqrt(next_variance)
    return Prediction(mean_kg=next_mean, std_kg=next_std)


def parse_args() -> DailyInputs:
    parser = argparse.ArgumentParser(
        description="Predict tomorrow's weight with a Bayesian update",
    )
    parser.add_argument("--current-weight", type=float, required=True)
    parser.add_argument("--calories-in", type=float, required=True)
    parser.add_argument("--calories-out", type=float, required=True)
    parser.add_argument("--prior-std", type=float, default=0.3)
    parser.add_argument("--process-std", type=float, default=0.12)
    parser.add_argument("--balance-std", type=float, default=200)
    args = parser.parse_args()

    return DailyInputs(
        current_weight_kg=args.current_weight,
        calories_in=args.calories_in,
        calories_out=args.calories_out,
        prior_std_kg=args.prior_std,
        process_std_kg=args.process_std,
        balance_std_kcal=args.balance_std,
    )


def main() -> None:
    inputs = parse_args()
    prediction = predict_next_day(inputs)
    lower = prediction.mean_kg - 1.96 * prediction.std_kg
    upper = prediction.mean_kg + 1.96 * prediction.std_kg

    print("Tomorrow's weight prediction")
    print(f"Mean: {prediction.mean_kg:.2f} kg")
    print(f"Std dev: {prediction.std_kg:.2f} kg")
    print(f"95% interval: [{lower:.2f}, {upper:.2f}] kg")


if __name__ == "__main__":
    main()
