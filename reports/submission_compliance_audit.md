# Official submission compliance audit

Status: **PASS**. Primary Stage 1 model: **PennyLane fixed depth-1 RY/CNOT fidelity kernel**.

| Requirement | Evidence | Status |
|---|---|---|
| 300 labeled training and 100 test records | Revised workbook validation and `stage1_result.csv` | PASS |
| Quantum/hybrid classifier plus classical baseline | Fixed PennyLane kernel primary; calibrated RBF-SVM retained in benchmark/archive | PASS |
| Training-only preprocessing and calibration | Fitted preprocessing plus seeded training-only Platt split; test used only by `predict_proba` | PASS |
| Continuous probabilities | 100 finite values in `[0,1]` | PASS |
| Descending ranking; ascending customer ID tie-break | Stable two-key ranking in `src/integration.py` | PASS |
| Stage 1 required fields and exactly ten flags | `stage1_result.csv` | PASS |
| Exact six selected from actual top ten | `stage2_result.json` | PASS |
| Workbook budget/capacity constraints | Cost 15/25; capacity 16/22 | PASS |
| Exact classical comparison | All 210 combinations; objective 45.0419817314 | PASS |
| Standard and cardinality-preserving QAOA | Parameters, counts, bitstrings, feasibility, resources and runtimes in Stage 2 artifacts | PASS |
| Do not assume QAOA optimum | Exact solver remains operational authority; quantum comparison reported separately | PASS |
| One qubit per selected customer | Six-qubit RY subscription circuit | PASS |
| Same IDs/probabilities through all stages | Automated validator checks exact ID order and tolerance `1e-12` | PASS |
| Exact, ideal, shot, Monte Carlo and noise comparisons | `stage3_result.json` and detailed CSV artifacts | PASS |
| 1,024, 4,096 and 16,384 shots | All present with seeds, errors and uncertainty | PASS |
| Circuit resources and reproducibility | Model metadata, QAOA circuit complexity, Stage 3 gate counts, package audit | PASS |
| Three top-level result files | `stage1_result.csv`, `stage2_result.json`, `stage3_result.json` | PASS |
| Previous official result preserved | `artifacts/official_archives/rbf_svm_official_20261111/` | PASS |
| No unsupported advantage claim | Reports explicitly make no computational-speedup claim | PASS |

The exploratory cross-validation metrics motivated the user-directed implementation decision but are not presented as official-test performance. The revised workbook remains structurally verified but has no embedded cryptographic organizer signature.
