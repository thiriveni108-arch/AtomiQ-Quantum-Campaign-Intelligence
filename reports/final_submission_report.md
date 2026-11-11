# Final submission report — fixed PennyLane kernel official run

## Outcome

The primary Stage 1 model is now the preselected PennyLane fixed depth-1 RY/CNOT fidelity kernel. This was an implementation decision, not a new selection study. It was fitted on all 300 official labels, generated new probabilities for all 100 revised-workbook test rows, and drove fresh Stage 2 and Stage 3 runs. Validation is PASS.

The previous RBF-SVM official package is preserved at `artifacts/official_archives/rbf_svm_official_20261111/`.

## Stage 1

The exact selected map is four qubits with H gates, RY data encoding, fixed zero RZ/RY rotations, and a linear CNOT chain. The squared state fidelity is supplied to a balanced precomputed-kernel SVC. Leakage-free preprocessing is `PDaysEngineer`, training-fitted imputation/encoding/scaling, PCA to four dimensions, and angle scaling to `[-pi, pi]`. Platt calibration uses a seeded, stratified 25% split of the 300 training rows; the SVC is then refitted on all 300 rows. Test data and IDs are used only for inference and ranking.

The prior exploratory three-fold results remain PR-AUC 0.2329, ROC-AUC 0.6769, Precision@10 0.30, Brier 0.1007, and log loss 0.3488. They are exploratory metrics, not performance measured on the unlabeled official test set. The calibrated RBF-SVM remains the classical comparison.

Official top 10 in rank order:

`C0079, C0088, C0031, C0202, C0345, C0258, C0359, C0293, C0112, C0339`.

## Stage 2

Exact enumeration evaluated all 210 six-customer combinations. The exact feasible optimum selects:

`C0079, C0088, C0202, C0345, C0258, C0339`.

- Expected net value: **45.0419817314**
- Contact cost: **15 / 25**
- Capacity: **16 / 22**

The best measured quantum result was cardinality-preserving QAOA at p=2, seed 42. It sampled the exact optimum:

- Best feasible objective: **45.0419817314**
- Absolute and relative optimality gap: **0**
- Feasible-shot probability: **1.0**
- Exact-optimum sampling probability: **0.0234375**
- Decision bitstring in top-10 order: `1101110001`
- Circuit: 10 qubits, depth 12, 20 RXX + 20 RYY + 6 X + 2 diagonal + measurement operations

The exact optimum, rather than a quantum sample, is the operational selection passed to Stage 3 because it is provably optimal. No quantum speedup is claimed.

## Stage 3

Customer-to-qubit order and unchanged Stage 1 probabilities:

| Qubit | Customer | Probability |
|---:|---|---:|
| 0 | C0079 | 0.4978842732 |
| 1 | C0088 | 0.4631571315 |
| 2 | C0202 | 0.4007035068 |
| 3 | C0345 | 0.3884094241 |
| 4 | C0258 | 0.3709363665 |
| 5 | C0339 | 0.3113647639 |

Exact Poisson-binomial and ideal statevector probability of at least three subscriptions:

**0.4669729140887742**

| Samples/shots | Classical Monte Carlo | MC abs. error | Aer estimate | Aer abs. error |
|---:|---:|---:|---:|---:|
| 1,024 | 0.4863281250 | 0.0193552109 | 0.4580078125 | 0.0089651016 |
| 4,096 | 0.4597167969 | 0.0072561172 | 0.4594726562 | 0.0075002578 |
| 16,384 | 0.4645385742 | 0.0024343399 | 0.4659423828 | 0.0010305313 |

The six-qubit circuit contains six RY gates and has depth 2 including measurement. The controlled-noise sensitivity run is recorded separately and is not represented as hardware execution.

## Reproduction

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe run_end_to_end.py --mode official
.\.venv\Scripts\python.exe run_end_to_end.py --mode validate
```

Official outputs are `stage1_result.csv`, `stage2_result.json`, and `stage3_result.json`.
