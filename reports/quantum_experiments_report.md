# PennyLane quantum experiments

## Scope and controls

This extension preserved the prior Stage 1 implementation, results, serialized RBF-SVM, and provisional predictions. It did not touch Stage 2/3 or infer customer IDs. Every model used the same `StratifiedKFold(3, shuffle=True, random_state=42)` outer splits. Preprocessing, supervised feature selection, kernel alignment, early stopping, and sigmoid calibration were fitted using only each outer training partition. Inputs remained four-dimensional and bounded to `[-π, π]`.

The environment used Python 3.14, Qiskit 2.6.2, Qiskit Machine Learning 0.9.1, PennyLane 0.45.1, PennyLane Lightning 0.45.0, PyTorch 2.15.0, and scikit-learn 1.9.1. Exact statevector simulators were local; no hardware or paid backend was used.

## Architectures

- **PennyLane QSVC replication:** exact 4-qubit Qiskit `zz_feature_map(reps=1, entanglement="linear")`: four H gates, `PhaseShift(2x_i)`, and three `CNOT–PhaseShift(2(π-x_i)(π-x_j))–CNOT` blocks. The kernel is `|<φ(x)|φ(y)>|²`; classification uses a precomputed balanced SVC and training-only sigmoid calibration.
- **Alignment kernel:** RY data encoding, trainable RZ/RY rotations, and linear CNOT entanglement. Depth 1 has 8 nominal parameters; depth 2 has 16. Alignment used at most 80 stratified outer-training examples, six bounded Adam steps, two learning rates, and two seeds.
- **Data re-uploading QNN:** two layers, four qubits, RY data gates, trainable Rot gates, ring CNOTs, 24 parameters, Pauli-Z probability mapping, Adam/BCE, inner validation early stopping, and inner sigmoid calibration.

Circuit texts and complexity metadata are in `reports/quantum_circuits/`.

## Qiskit–PennyLane equivalence

On 20 identical fold-fitted PCA vectors, maximum absolute kernel difference was **6.66×10⁻¹⁶**, mean difference **4.29×10⁻¹⁷**, and prediction agreement under identical precomputed SVCs was **100%**. Minimum eigenvalues were 0.0202812088550631 (Qiskit) and 0.0202812088550622 (PennyLane); neither kernel had an eigenvalue below −1×10⁻¹⁰. Thus the circuit/kernel implementations are numerically equivalent. Aggregate fixed-model metrics differ from the old Qiskit result because the new experiment uses an explicit holdout Platt calibration implementation rather than the earlier `CalibratedClassifierCV` procedure—not because the kernels differ.

## Aggregate results

| Model | PR-AUC | ROC-AUC | P@10 | Brier | Log loss | Runtime s |
|---|---:|---:|---:|---:|---:|---:|
| Existing RBF-SVM | 0.149 | 0.562 | 0.10 | 0.1035 | 0.3615 | 4.77 |
| Existing Qiskit QSVC | 0.111 | 0.421 | 0.20 | 0.1050 | 0.3714 | 4.28 |
| Existing Qiskit VQC | 0.157 | 0.583 | 0.20 | 0.2246 | 0.6408 | 87.02 |
| PennyLane replicated QSVC, PCA | 0.107 | 0.432 | 0.10 | 0.1063 | 0.3789 | 4.56 |
| PennyLane replicated QSVC, supervised | 0.110 | 0.464 | 0.10 | 0.1087 | 0.3799 | 4.30 |
| **PennyLane alternate kernel, depth 1** | **0.233** | **0.677** | **0.30** | **0.1007** | **0.3488** | 20–21 |
| Best depth-2 alignment run (lr .08, seed 42) | 0.199 | 0.652 | 0.10 | 0.1013 | 0.3516 | 36.55 |
| Data re-uploading QNN, seed 137 | 0.137 | 0.536 | 0.20 | 0.1030 | 0.3601 | 145.88 |
| Data re-uploading QNN, seed 42 | 0.125 | 0.494 | 0.10 | 0.1033 | 0.3609 | 148.81 |

Full configurations and less successful depth-2 runs are in `results/quantum_model_comparison.csv`; all 36 new fold records are in `results/quantum_fold_metrics.csv`.

## Kernel alignment findings

The apparent depth-1 “trainable” result needs a precise interpretation. With one layer, every trainable rotation and entangler occurs after the data encoding as the same data-independent unitary for all samples. Fidelity is unitary-invariant, so these parameters cancel from the kernel. Alignment remained unchanged to numerical precision across all six optimizer steps, learning rates, and seeds, and predictions were identical. The improvement over ZZ-QSVC is therefore evidence for a better **fixed alternate RY/CNOT feature map**, not successful kernel learning.

Depth 2 interleaves a second data encoding, so parameters genuinely affect fidelity. Training alignment increased slightly in every fold/configuration, but held-out performance was highly seed- and fold-sensitive. For example, depth-2 lr=.08 seed=42 fold PR-AUCs were 0.311, 0.094, and 0.224. Other depth-2 seeds fell below the dummy baseline. Increased training alignment did not reliably translate to better held-out prediction.

## Fold stability of the strongest candidate

The depth-1 alternate fixed kernel produced fold PR-AUCs **0.299, 0.232, 0.257**, ROC-AUCs **0.727, 0.701, 0.719**, P@10 **0.30, 0.20, 0.30**, and Brier scores **0.0959, 0.1042, 0.1018**. Directional consistency is encouraging, but only 35 positives and evaluation of multiple quantum configurations make the aggregate optimistic and insufficient for a statistical quantum-advantage claim.

## Feature and QNN experiments

Supervised `f_classif` selection modestly raised the replicated fixed kernel's PR-AUC from 0.107 to 0.110 and ROC-AUC from 0.432 to 0.464, while worsening Brier/log loss. It did not establish that PCA discards useful signal. A nonlinear representation was omitted to avoid expanding the search after observing outer-fold results.

The data re-uploading QNN dramatically improved calibration relative to Qiskit VQC (Brier ≈0.103 versus 0.225), but did not improve ranking: the better seed reached PR-AUC 0.137 versus VQC 0.157. Seed variation was material, so it does not replace VQC as the strongest variational ranker.

## Model selection conclusion

The strongest observed quantum candidate is the depth-1 alternate fixed RY/CNOT fidelity kernel. It beats the existing RBF-SVM on the present aggregate metrics and is consistent across the three folds. A subsequent explicit implementation decision promoted this fixed kernel to the official Stage 1 model; no additional selection study was run. These exploratory metrics remain subject to the original small-sample and multiple-configuration caveats. There is no evidence of computational quantum advantage because every circuit ran on a classical simulator.

## Reproduction

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe run_quantum_experiments.py --mode smoke
.\.venv\Scripts\python.exe run_quantum_experiments.py --mode full
```

At experiment time, Stage1_Test remained untouched during fitting and lacked verified customer IDs. The later organizer-supplied workbook revision added row-aligned IDs without changing features. The RBF-SVM-era official artifacts are archived under `artifacts/official_archives/rbf_svm_official_20261111/`; the active model artifact is now the fixed depth-1 kernel fitted on all 300 labels.
