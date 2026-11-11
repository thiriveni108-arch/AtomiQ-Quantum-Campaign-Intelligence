# Final submission report — official revised workbook

## Outcome

The revised workbook resolves the test customer mapping by supplying IDs directly on the unchanged 100 Stage1_Test rows. The complete official three-stage pipeline executed with consistent IDs and probabilities. Validation status is PASS and 42 automated tests pass.

## Stage 1

Training data and test features are unchanged, so the existing calibrated RBF-SVM was reused without retraining. Its validated metrics remain PR-AUC 0.1495, ROC-AUC 0.5619, Brier 0.1035, and log loss 0.3615. The exploratory fixed RY/CNOT quantum kernel remains research-only despite stronger observed fold metrics, because it was identified through a multi-configuration comparison on only 35 positives.

Official top 10, in rank order:

`C0193, C0256, C0050, C0111, C0202, C0020, C0031, C0088, C0079, C0293`.

All 100 official predictions are in `stage1_result.csv`; probabilities match the previous provisional row predictions exactly.

## Stage 2

The exact solver evaluated all 210 six-customer combinations. The exact optimum selects:

`C0256, C0111, C0020, C0088, C0079, C0293`.

- Expected net value: **12.0135828481**
- Contact cost: **14 / 25**
- Capacity: **20 / 22**

This exact feasible optimum is passed to Stage 3. The best measured quantum configuration was standard QAOA p=2, seed 137:

- Best feasible objective: **11.7347198834**
- Absolute gap: **0.2788629647**
- Relative gap: **2.3212%**
- Feasible-shot probability: **0.265625**
- Exact-optimum sampling probability: **0**
- Decision bitstring in top-10 order: `0101110110`

Cardinality QAOA maintained feasible-shot probability 1.0 for these official candidates but did not reach the exact objective. Exact enumeration remains the correct operational method at N=10; no quantum speedup is claimed.

## Stage 3

Customer-to-qubit order and unchanged probabilities:

| Qubit | Customer | Probability |
|---:|---|---:|
| 0 | C0256 | 0.1813275140 |
| 1 | C0111 | 0.1802287057 |
| 2 | C0020 | 0.1766896932 |
| 3 | C0088 | 0.1730625910 |
| 4 | C0079 | 0.1725544792 |
| 5 | C0293 | 0.1709775279 |

Exact Poisson-binomial and ideal statevector probability of at least three subscriptions:

**0.071426562343945**

| Samples/shots | Classical Monte Carlo | MC abs. error | Aer estimate | Aer abs. error |
|---:|---:|---:|---:|---:|
| 1,024 | 0.08203125 | 0.01060469 | 0.07031250 | 0.00111406 |
| 4,096 | 0.06909180 | 0.00233477 | 0.06787109 | 0.00355547 |
| 16,384 | 0.07183838 | 0.00041182 | 0.07189941 | 0.00047285 |

The six-qubit circuit has six RY gates and depth 2 including measurement. The controlled synthetic-noise run (0.5% one-qubit depolarizing plus 1% readout error, 4,096 shots) estimated 0.08715820; this is sensitivity analysis, not hardware noise.

## Requirements and research interpretation

The four-page PDF was read visually because it is scanned and has no text layer. All three requested result-file content sets are present at the repository top level. Circuit resources, seeds, package versions, simulator configurations, raw counts, QAOA parameters, and bitstrings are recorded in machine-readable artifacts.

The project demonstrates real quantum circuit simulation and quantum optimization research, but exact classical enumeration and Poisson-binomial dynamic programming are faster and exact for these small instances. There is no evidence of hardware or computational quantum advantage.

## Reproduction

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe run_end_to_end.py --mode official --workbook bank_campaign_participant_release-1.xlsx
.\.venv\Scripts\python.exe run_end_to_end.py --mode validate
```

Official outputs:

- `stage1_result.csv`
- `stage2_result.json`
- `stage3_result.json`

Detailed workbook comparison, compliance traceability, circuit resources, research experiments, and separate demo outputs remain under `reports/`, `results/`, and `artifacts/`.
