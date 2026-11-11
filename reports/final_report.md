# Stage 1 final report

> Historical benchmark report. It documents the original RBF-SVM deployment decision before the later explicit promotion of the fixed depth-1 PennyLane RY/CNOT kernel. Current official results are in `reports/final_submission_report.md`; the old official package is archived under `artifacts/official_archives/rbf_svm_official_20261111/`.

## 1. Data audit findings

The original workbook SHA-256 at execution was `ff65cb30ceb8a32d682644cd8b161234c80f1315736d909c03afccd5553ef823`; it was not edited. `Stage1_Train` contains 300 rows (35 yes, 265 no; 11.67% positive), and `Stage1_Test` contains 100 rows. Training IDs are present, unique, and non-missing. There are no missing cells or exact duplicate rows in either Stage 1 sheet. `duration` is absent. `unknown` remains a category. See `data_audit.md` and `data_audit.json` for schemas, categories, numeric summaries, and checks.

## 2. Customer ID mapping status

No organizer-supplied mapping was found anywhere in the project. `Stage1_Test` has no `customer_id`; predictions use zero-based `test_row_index`. The output is provisional. Official tie-breaking, submission formatting, and Stage 2 joins remain blocked. No IDs were guessed or externally reconstructed.

## 3. Methodology

All reported predictions are out-of-fold from seeded (`42`) stratified 3-fold CV. Imputation, one-hot encoding, robust scaling, PCA, and angle scaling are fitted inside each relevant fold. Logistic regression and RBF-SVM use bounded training-only 3-fold grid searches. The SVM is sigmoid-calibrated on inner folds. Quantum inputs use training-fitted PCA to four components followed by `[-pi, pi]` scaling. QSVC uses a shallow, linear-entangled ZZ feature map and an exact fidelity statevector kernel; its SVM is sigmoid-calibrated. VQC uses the same map, a shallow linear-entangled RealAmplitudes ansatz, statevector sampling, COBYLA, and 30 iterations. All quantum runs were actually executed locally.

## 4–6. Metrics and calibration

| Model | PR-AUC | ROC-AUC | P@10 | R@10 | Brier | Log loss | Train s | Infer s |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Dummy prior | 0.115 | 0.489 | 0.10 | 0.029 | 0.1031 | 0.3604 | 0.07 | 0.02 |
| Logistic regression | 0.124 | 0.510 | 0.10 | 0.029 | 0.1299 | 0.4900 | 8.63 | 0.02 |
| Calibrated RBF-SVM | 0.149 | 0.562 | 0.10 | 0.029 | 0.1035 | 0.3615 | 4.77 | 0.04 |
| Calibrated QSVC | 0.111 | 0.421 | 0.20 | 0.057 | 0.1050 | 0.3714 | 4.28 | 0.64 |
| VQC | 0.157 | 0.583 | 0.20 | 0.057 | 0.2246 | 0.6408 | 87.02 | 1.46 |

VQC has the strongest PR-AUC/ROC-AUC but severely inferior probability calibration. RBF-SVM is only marginally worse than the prior baseline in Brier/log loss, while providing a better ranking. Accuracy is 0.883 for the prior, RBF-SVM, and QSVC because none crosses the 0.5 threshold; this illustrates why accuracy is not the selection criterion. With only 35 positives (about 11–12 per validation fold), metric and top-10 uncertainty is substantial.

## 7. Winning model

Calibrated RBF-SVM wins the declared composite probability/ranking rule. The final training-only search chose `C=0.5`, `gamma=scale`; the fitted search/pipeline is serialized. This is not evidence of quantum advantage: VQC ranks somewhat better but its probabilities are not suitable for expected-value calculations without a more robust calibration experiment.

## 8. Generated outputs

- `results/model_comparison.csv`: all actual OOF metrics and runtimes.
- `results/stage1_predictions_provisional.csv`: 100 ranked probabilities, 10 marked candidates, and explicit missing-ID status.
- `artifacts/stage1_final_model.joblib`: fitted preprocessing, tuning, calibration, and model.
- `artifacts/vqc_training_metadata.json`: loss histories, fold circuit weights, optimizer limit, and seed.
- `reports/figures/`: PR, reliability, and confusion-matrix plots.
- `reports/runtime_circuit_complexity.json`: versions, seeds, selection rule, runtimes context, circuit depth/gates, losses, and weights.
- `reports/feature_map_circuit.txt` and `reports/vqc_ansatz_circuit.txt`: executable circuit diagrams.

## 9. Reproduction

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe run_pipeline.py --mode smoke
.\.venv\Scripts\python.exe run_pipeline.py --mode full
```

## 10. Limitations and next steps

The sample and positive count are small, PCA is unsupervised/linear and may discard minority signal, simulated four-qubit performance does not imply hardware or computational advantage, and VQC optimization is intentionally bounded. Obtain the organizer's row-to-ID mapping before any Stage 2 work. Then apply official ID tie-breaking, join only validated top-10 IDs to Stage2_Data, quantify uncertainty with repeated CV or bootstrap confidence intervals, and consider training-only calibration/representation comparisons. Stage 2 optimization and Stage 3 simulation were not implemented.
