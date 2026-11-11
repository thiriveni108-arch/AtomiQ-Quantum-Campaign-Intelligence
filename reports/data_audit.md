# Data audit

## Findings

- Workbook sheets: README, Stage1_Train, Stage1_Test, Stage2_Data, Stage2_Constraints.
- Stage1_Train: 300 rows, 17 columns; Stage1_Test: 100 rows, 15 columns.
- Labels: 35 yes and 265 no (positive prevalence 11.67%). This is materially imbalanced.
- Training IDs are unique: True; missing training IDs: 0.
- Exact duplicate rows: train 0, test 0. Missing cells: train 0, test 0.
- `duration` is absent, avoiding the known post-call leakage field.
- `unknown` is retained as an observed category, not treated as missing.
- `balance` has median 460, range [-2082, 27069]; robust scaling limits outlier influence without deleting customers.
- `pdays=-1` occurs 254 times and is represented by `pdays_never=1` plus numeric `pdays=0`.

## Customer ID mapping blocker

`Stage1_Test` has no `customer_id`. No separate organizer mapping was found (20 candidate files). Predictions therefore use zero-based `test_row_index` and are **provisional**. Official tie-breaking, submission formatting, and Stage 2 joins are blocked. No IDs were guessed or inferred from external data.

## Leakage controls

`customer_id` and `y` are excluded from features. Imputation, one-hot encoding, robust scaling, PCA, angle scaling, tuning, and calibration are fitted only on training folds through scikit-learn pipelines. Stage1_Test is used only once for final inference.
