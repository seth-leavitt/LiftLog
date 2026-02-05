# Ax Bayesian Weight Forecast

This example uses **Meta's Ax** to calibrate a Bayesian weight forecast model that predicts tomorrow's weight from daily inputs **and** a Bayesian-augmented deep learning model that incorporates exercise history, PRs, and body stats. The workflow includes:

- A lightweight Kalman-style baseline for fast estimates.
- A Bayesian neural network (MC Dropout) for richer feature inputs and data-driven uncertainty.

- **State**: body weight in kg.
- **Process model**: weight changes by `(calories_in - calories_out) / kcal_per_kg` plus noise.
- **Uncertainty**: propagated from the prior variance + process noise + calorie-balance noise.

## Why the baseline uncertainty works this way

Let:

- `w_t ~ Normal(mu_t, sigma_t^2)` be today's weight distribution.
- `b_t = calories_in - calories_out` be the net calorie balance.
- `k = 7700` kcal/kg.
- `process_std_kg` be unexplained biological/process noise.
- `balance_std_kcal` be uncertainty in the calorie balance estimate.

The **predictive distribution** for tomorrow is:

```
mu_{t+1} = mu_t + b_t / k
sigma_{t+1}^2 = sigma_t^2 + process_std_kg^2 + (balance_std_kcal / k)^2
```

That variance formula is the **uncertainty measurement**: it combines your current uncertainty about weight with uncertainty introduced by metabolism + calorie estimation error. The standard deviation is `sqrt(sigma_{t+1}^2)`.

## Bayesian augmented deep learning overview

For the deep learning model, we use **MC Dropout** to approximate Bayesian inference. The model predicts the mean weight change and estimates uncertainty by sampling the network multiple times with dropout active at inference time. The predictive mean/variance are computed from those samples:

```
mu = average(predictions)
sigma^2 = average((prediction - mu)^2)
```

We then report `mu` and `sigma` for the next-day weight forecast.

## Setup

```bash
cd "Bayesian Inference"
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Generate spoofed data

```bash
python generate_spoofed_data.py --days 90 --output sample_data.csv
```

## Predict tomorrow's weight

```bash
python bayesian_weight_predictor.py \
  --current-weight 82.0 \
  --calories-in 2400 \
  --calories-out 2700 \
  --prior-std 0.3 \
  --process-std 0.12 \
  --balance-std 200
```

## Calibrate noise terms with Meta's Ax

If you have historical day logs (weight + calorie balance), you can tune `process_std_kg` and `balance_std_kcal` to minimize prediction error.

```bash
python ax_noise_calibration.py --data sample_data.csv
```

The script uses **Meta's Ax** to search for noise values that minimize mean absolute error.

## Train the Bayesian deep learning model

```bash
python train_bayesian_weight_model.py --data sample_data.csv --epochs 150
```

## Predict with the Bayesian deep learning model

```bash
python predict_bayesian_weight_model.py --data sample_data.csv --last-n 7 --samples 50
```

## Sample data format

`sample_data.csv` expects:

```
date,weight_kg,calories_in,calories_out,height_cm,pr_total_kg,exercise_count,exercise_volume_kg
2024-05-01,82.4,2450,2700,178,420,5,12500
2024-05-02,82.2,2550,2600,178,420,4,10800
```
