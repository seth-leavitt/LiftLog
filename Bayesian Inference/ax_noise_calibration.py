from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from math import sqrt
from pathlib import Path
from typing import Iterable

from ax.service.managed_loop import optimize

from bayesian_weight_predictor import KCAL_PER_KG, DailyInputs, predict_next_day


@dataclass(frozen=True)
class DailyLog:
    weight_kg: float
    calories_in: float
    calories_out: float


def read_logs(path: Path) -> list[DailyLog]:
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        logs: list[DailyLog] = []
        for row in reader:
            logs.append(
                DailyLog(
                    weight_kg=float(row["weight_kg"]),
                    calories_in=float(row["calories_in"]),
                    calories_out=float(row["calories_out"]),
                )
            )
    if len(logs) < 2:
        raise ValueError("Need at least two rows to calibrate.")
    return logs


def update_posterior(
    prior_mean: float,
    prior_std: float,
    observed_weight: float,
    measurement_std: float,
) -> tuple[float, float]:
    prior_var = prior_std**2
    measurement_var = measurement_std**2
    posterior_var = 1 / (1 / prior_var + 1 / measurement_var)
    posterior_mean = (
        prior_mean / prior_var + observed_weight / measurement_var
    ) * posterior_var
    return posterior_mean, sqrt(posterior_var)


def mean_absolute_error(values: Iterable[float]) -> float:
    values = list(values)
    return sum(values) / len(values)


def calibration_loss(
    logs: list[DailyLog],
    prior_std_kg: float,
    measurement_std_kg: float,
    process_std_kg: float,
    balance_std_kcal: float,
) -> float:
    errors: list[float] = []
    prior_mean = logs[0].weight_kg
    prior_std = prior_std_kg

    for index in range(len(logs) - 1):
        today = logs[index]
        tomorrow = logs[index + 1]

        prediction = predict_next_day(
            DailyInputs(
                current_weight_kg=prior_mean,
                calories_in=today.calories_in,
                calories_out=today.calories_out,
                prior_std_kg=prior_std,
                process_std_kg=process_std_kg,
                balance_std_kcal=balance_std_kcal,
            )
        )

        errors.append(abs(prediction.mean_kg - tomorrow.weight_kg))
        prior_mean, prior_std = update_posterior(
            prediction.mean_kg,
            prediction.std_kg,
            tomorrow.weight_kg,
            measurement_std_kg,
        )

    return mean_absolute_error(errors)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Tune Bayesian noise parameters with Meta's Ax",
    )
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--prior-std", type=float, default=0.3)
    parser.add_argument("--measurement-std", type=float, default=0.25)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    logs = read_logs(args.data)

    def evaluate(parameters: dict[str, float]) -> float:
        return calibration_loss(
            logs=logs,
            prior_std_kg=args.prior_std,
            measurement_std_kg=args.measurement_std,
            process_std_kg=parameters["process_std_kg"],
            balance_std_kcal=parameters["balance_std_kcal"],
        )

    best_parameters, values, _, _ = optimize(
        parameters=[
            {
                "name": "process_std_kg",
                "type": "range",
                "bounds": [0.05, 0.6],
                "value_type": "float",
            },
            {
                "name": "balance_std_kcal",
                "type": "range",
                "bounds": [50.0, 600.0],
                "value_type": "float",
            },
        ],
        evaluation_function=evaluate,
        objective_name="mae",
        minimize=True,
        total_trials=25,
    )

    balance_std_kg = best_parameters["balance_std_kcal"] / KCAL_PER_KG

    print("Best parameters:")
    print(f"  process_std_kg: {best_parameters['process_std_kg']:.4f}")
    print(f"  balance_std_kcal: {best_parameters['balance_std_kcal']:.2f}")
    print(f"  balance_std_kg: {balance_std_kg:.4f}")
    print(f"  MAE: {values[0]['mae']:.4f} kg")


if __name__ == "__main__":
    main()
