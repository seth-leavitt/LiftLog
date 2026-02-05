from __future__ import annotations

import argparse
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

KCAL_PER_KG = 7700.0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate spoofed weight data")
    parser.add_argument("--days", type=int, default=60)
    parser.add_argument("--start-weight", type=float, default=82.0)
    parser.add_argument("--height-cm", type=float, default=178.0)
    parser.add_argument("--output", type=Path, default=Path("sample_data.csv"))
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rng = np.random.default_rng(args.seed)

    start_date = date.today() - timedelta(days=args.days)
    weight = args.start_weight
    pr_total = 420.0

    rows: list[dict[str, float | str]] = []

    for day_index in range(args.days):
        current_date = start_date + timedelta(days=day_index)
        calories_in = float(rng.normal(2500, 250))
        calories_out = float(rng.normal(2600, 200))
        exercise_count = int(max(0, rng.poisson(4)))
        exercise_volume = float(max(0.0, rng.normal(12000, 2500)))

        net_calories = calories_in - calories_out
        weight_change = net_calories / KCAL_PER_KG + rng.normal(0, 0.12)
        weight = weight + weight_change

        if exercise_count > 0 and rng.random() < 0.15:
            pr_total += rng.normal(2.5, 1.0)

        rows.append(
            {
                "date": current_date.isoformat(),
                "weight_kg": round(weight, 2),
                "calories_in": round(calories_in, 0),
                "calories_out": round(calories_out, 0),
                "height_cm": args.height_cm,
                "pr_total_kg": round(pr_total, 1),
                "exercise_count": exercise_count,
                "exercise_volume_kg": round(exercise_volume, 0),
            }
        )

    pd.DataFrame(rows).to_csv(args.output, index=False)
    print(f"Wrote {len(rows)} rows to {args.output}")


if __name__ == "__main__":
    main()
