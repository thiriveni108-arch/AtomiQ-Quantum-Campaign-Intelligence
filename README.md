# AtomiQ — Quantum Campaign Intelligence

AtomiQ is a reproducible hybrid quantum–classical system for selecting a bank term-deposit outreach campaign. It predicts subscription propensity, optimizes a constrained six-customer campaign, and estimates the probability that at least three selected customers subscribe. The repository includes the validated Python pipeline, FastAPI service, interactive Next.js application, tests, official outputs, and scientific audit artifacts.

> All quantum experiments in this release run on local simulators. The project does **not** claim quantum computational speedup.

## Table of contents

- [Quick start](#quick-start)
- [Project overview](#project-overview)
- [Three-stage architecture](#three-stage-architecture)
- [Quantum implementation](#quantum-implementation)
- [Official results](#official-results)
- [Quantum vs classical comparison](#quantum-vs-classical-comparison)
- [Project structure](#project-structure)
- [Installation](#installation)
- [Running the pipeline](#running-the-pipeline)
- [Running the website](#running-the-website)
- [Reproducibility](#reproducibility)
- [Limitations](#limitations)
- [License](#license)

## Quick start

Prerequisites: Python 3.11+ (the validated environment used Python 3.14), Node.js 20+, and Git.

```powershell
git clone https://github.com/thiriveni108-arch/AtomiQ-Quantum-Campaign-Intelligence.git
cd AtomiQ-Quantum-Campaign-Intelligence

python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

cd web
npm install
cd ..
```

Before executing official mode, place authorized copies of these organizer files in the repository root:

- `bank_campaign_participant_release.xlsx`
- `bank_campaign_participant_release-1.xlsx`
- `PROBLEM_STATEMENT_THEATOMIQHACKTHON.pdf`

They are intentionally not redistributed here because the supplied files contain no explicit public redistribution license. The checked-in official outputs can still be inspected without those source documents.

## Project overview

The challenge provides 300 labeled banking customers, 100 unlabeled campaign candidates, customer-level expected value/cost/capacity data, and campaign constraints. AtomiQ implements the complete decision chain:

1. predict a calibrated subscription probability for every test customer;
2. choose exactly six of the ten highest-ranked candidates under budget and capacity limits;
3. estimate the probability that at least three selected customers subscribe.

Classical exact methods are retained as correctness references throughout. Quantum methods are evaluated as executable research components, not presented as replacements for exact classical methods where the small problem size makes exact computation preferable.

## Three-stage architecture

### Stage 1 — Predict

The deployed model is a PennyLane fixed depth-1 RY/CNOT fidelity kernel. Leakage-free preprocessing engineers `pdays`, imputes and encodes features, robust-scales numeric values, reduces to four PCA components, and maps them into `[-π, π]`. A balanced precomputed-kernel SVM performs classification, followed by training-only Platt calibration. The calibrated RBF-SVM remains the classical benchmark.

### Stage 2 — Optimize

The top ten Stage 1 customers are joined to the official value, contact-cost, and capacity data. Three solvers are compared:

- exact enumeration of all `10 choose 6 = 210` selections;
- standard QAOA using a slack-variable QUBO;
- cardinality-preserving QAOA using a weight-preserving mixer.

The exact feasible optimum is the operational campaign passed to Stage 3. QAOA feasibility, objective, sampling probability, resources, and gap are reported separately.

### Stage 3 — Simulate

One qubit represents each selected customer. An `RY(2 asin(sqrt(p)))` rotation encodes the unchanged Stage 1 probability. No entanglement is used because the model assumes independent Bernoulli subscription outcomes. The probability of at least three subscriptions is evaluated by:

- exact Poisson-binomial dynamic programming;
- ideal Qiskit statevector simulation;
- Qiskit Aer sampling at 1,024, 4,096, and 16,384 shots;
- seeded classical Monte Carlo;
- a controlled synthetic-noise sensitivity run.

## Quantum implementation

- **Feature encoding:** four training-fitted PCA angles are encoded with Hadamard and RY operations followed by a linear CNOT chain.
- **Fidelity kernel:** squared state overlap produces the precomputed kernel consumed by the balanced SVM.
- **Standard QAOA:** a 20-qubit decision/slack formulation enforces campaign constraints through a validated instance-specific penalty.
- **Cardinality-preserving QAOA:** a 10-qubit XY-style mixer remains in the six-selected-customer subspace.
- **Probability circuit:** six independent RY rotations encode the selected subscription probabilities.
- **Classical references:** calibrated RBF-SVM, exact enumeration, exact Poisson-binomial calculation, and Monte Carlo simulation.

Circuit resources, parameters, counts, backends, seeds, and measured bitstrings are recorded under `reports/` and `results/`.

## Official results

The committed outputs are `stage1_result.csv`, `stage2_result.json`, and `stage3_result.json`.

**Top ten, in rank order**

`C0079, C0088, C0031, C0202, C0345, C0258, C0359, C0293, C0112, C0339`

**Exact selected campaign**

`C0079, C0088, C0202, C0345, C0258, C0339`

| Result | Value |
|---|---:|
| Exact expected net objective | `45.0419817314` |
| Contact cost | `15 / 25` |
| Capacity | `16 / 22` |
| Best measured QAOA gap | `0` |
| Exact `P(subscriptions ≥ 3)` | `0.4669729141` |

Cardinality-preserving QAOA at depth 2, seed 42 sampled the exact optimum. Exact enumeration remains the authoritative operational solver.

## Quantum vs classical comparison

These metrics are exploratory three-fold out-of-fold validation results on the 300 labeled training customers. They are **not** hidden-test performance.

| Model | PR-AUC ↑ | ROC-AUC ↑ | Precision@10 ↑ | Brier ↓ | Log loss ↓ |
|---|---:|---:|---:|---:|---:|
| PennyLane fixed depth-1 RY/CNOT kernel | 0.233 | 0.677 | 0.30 | 0.1007 | 0.3488 |
| Calibrated RBF-SVM | 0.149 | 0.562 | 0.10 | 0.1035 | 0.3615 |

The fixed kernel had the stronger observed exploratory metrics and was explicitly promoted to the primary model. With only 35 positive labels and several research configurations evaluated, these results do not establish generalization superiority or computational quantum advantage.

## Project structure

```text
api/          FastAPI adapter and real pipeline endpoints
artifacts/    fitted model and reproducibility metadata
configs/      Stage 1/2 experiment configurations
reports/      scientific, compliance, circuit, and resource reports
results/      detailed official/demo experiment outputs
src/          prediction, optimization, simulation, and audit modules
tests/        automated scientific, integration, and API tests
web/          Next.js App Router frontend
run_end_to_end.py
run_pipeline.py
run_quantum_experiments.py
run_stage2.py
run_stage3.py
stage1_result.csv
stage2_result.json
stage3_result.json
```

## Installation

### Python

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

On macOS/Linux, replace `.\.venv\Scripts\python.exe` with `.venv/bin/python`.

### Frontend

```powershell
cd web
npm install
```

`package-lock.json` is committed for reproducible dependency resolution.

## Running the pipeline

```powershell
# Automated tests
.\.venv\Scripts\python.exe -m pytest -q

# Complete official three-stage execution
.\.venv\Scripts\python.exe run_end_to_end.py --mode official

# Validate existing artifacts and cross-stage consistency
.\.venv\Scripts\python.exe run_end_to_end.py --mode validate

# Safe synthetic demonstration
.\.venv\Scripts\python.exe run_end_to_end.py --mode demo
```

Official mode verifies both workbook versions before reading IDs or features. It does not infer customer IDs for the original workbook.

## Running the website

Open two terminals from the repository root.

**FastAPI backend**

```powershell
.\.venv\Scripts\python.exe -m uvicorn api.main:app --reload --port 8000
```

API documentation is available at `http://localhost:8000/docs`.

**Next.js frontend**

```powershell
cd web
npm run dev
```

Open `http://localhost:3000`. The frontend requires the Python backend for official data, live pipeline jobs, and sandbox optimization.

## Reproducibility

- Official execution requires authorized copies of the three organizer files listed in [Quick start](#quick-start).
- `requirements.txt` and `web/package-lock.json` pin the validated dependencies.
- `artifacts/stage1_final_model.joblib` contains the fitted primary Stage 1 model.
- `artifacts/stage1_final_model_metadata.json` records feature-map, calibration, and training details.
- `configs/` records seeds and experiment settings.
- Official result files and detailed simulator/QAOA outputs are committed.
- The principal seeds are 42 and 137; per-shot Stage 3 runs record their exact seeds in JSON.

The official validator checks row counts, schemas, unique IDs, top-ten membership, constraints, and unchanged Stage 1 probabilities through Stage 3.

## Limitations

- All quantum circuits were executed on local classical simulators, not quantum hardware.
- The training set has 300 rows and only 35 positive labels; validation uncertainty is material.
- The deployed quantum kernel was chosen from exploratory experiments and needs larger independent evaluation.
- Stage 3 assumes independent customer outcomes.
- Exact enumeration and Poisson-binomial dynamic programming are faster and exact at these small problem sizes.
- No quantum speedup or production-banking suitability is claimed.
- Source workbooks and the challenge PDF are omitted pending explicit redistribution permission.

## License

Source code in this repository is released under the [MIT License](LICENSE). Organizer data and challenge materials, when obtained separately, remain subject to their own terms.
