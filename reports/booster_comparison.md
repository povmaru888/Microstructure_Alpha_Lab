# Gradient-boosting model comparison

## Protocol

XGBoost 3.1.1, LightGBM 4.7.0, and CatBoost 1.2.10 were trained on the same
single-day AAPL LOBSTER feature table. All models use the same nine causal features,
chronological purged 60/20/20 Train/Validation/Test split, class mapping, random seed,
single CPU thread, learning rate 0.1, and 30-tree budget. Maximum depth 2 or 3 is
selected by Validation log loss, with five-round early stopping. The frozen Test set
is used once for the comparison.

Run: `lobster_aapl_20120621_l10_boosters_v3`.

## Frozen Test results

| Horizon | Model | Macro-F1 | Balanced accuracy | MCC | Log loss | Brier |
|---|---|---:|---:|---:|---:|---:|
| h10 | XGBoost | 0.3903 | 0.3941 | 0.1007 | 1.0325 | 0.6247 |
| h10 | LightGBM | **0.3979** | **0.3992** | **0.1065** | **1.0294** | **0.6232** |
| h10 | CatBoost | 0.3728 | 0.3868 | 0.0973 | 1.0310 | 0.6235 |
| h20 | XGBoost | 0.3603 | 0.4318 | 0.1820 | 1.0610 | 0.6372 |
| h20 | LightGBM | **0.3629** | **0.4337** | **0.1849** | 1.0629 | 0.6375 |
| h20 | CatBoost | 0.3583 | 0.4315 | 0.1814 | **1.0581** | **0.6360** |
| h50 | XGBoost | **0.3942** | **0.4246** | **0.2206** | **0.9565** | **0.5705** |
| h50 | LightGBM | 0.3940 | 0.4243 | 0.2193 | 0.9662 | 0.5713 |
| h50 | CatBoost | 0.3937 | 0.4240 | 0.2165 | **0.9564** | 0.5717 |

| Model | Mean Macro-F1 | Mean balanced accuracy | Mean MCC | Mean log loss | Mean Brier |
|---|---:|---:|---:|---:|---:|
| XGBoost | 0.3816 | 0.4168 | 0.1677 | 1.0167 | 0.6108 |
| **LightGBM** | **0.3849** | **0.4191** | **0.1703** | 1.0195 | 0.6106 |
| CatBoost | 0.3749 | 0.4141 | 0.1651 | **1.0152** | **0.6104** |

LightGBM is the classification winner by the prespecified ranking metrics: it has the
highest mean Macro-F1, balanced accuracy, and MCC. XGBoost is nearly tied and is best
at h50. CatBoost has the best average probabilistic scores but the weakest mean
Macro-F1. The differences are small and are descriptive rather than estimates of
cross-day superiority.

## Training cost and artifact size

Times include both depth candidates for all three horizons and were measured with one
CPU thread on the same environment. Sizes are the sum of three serialized models.

| Model | Training seconds | Serialized size |
|---|---:|---:|
| XGBoost | **6.98** | 322 KiB |
| LightGBM | 8.72 | **290 KiB** |
| CatBoost | 10.91 | 6.24 MiB |

## Limitations

All three models have near-zero `flat` recall at h20 and zero `flat` recall at h50.
The comparison covers one symbol and one trading day, so it does not establish
cross-day stability or live trading value. A deployment decision requires multi-day
walk-forward tests, block uncertainty estimates, execution-cost modelling, and paper
trading.
