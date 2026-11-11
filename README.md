# AtomiQ — Quantum Campaign Intelligence

AtomiQ is a reproducible hybrid quantum–classical system for selecting a bank term-deposit outreach campaign. It predicts subscription propensity, optimizes a constrained six-customer campaign, and estimates the probability that at least three selected customers subscribe. The repository includes the validated Python pipeline, FastAPI service, interactive Next.js application, tests, official outputs, and scientific audit artifacts.

> All quantum experiments in this release run on local simulators. The project does **not** claim quantum computational speedup.

## Table of contents

- [Quick start](#quick-start)
- [Project overview](#project-overview)
- [Three-stage architecture](#three-stage-architecture)
- [Pipeline methodology](#pipeline-methodology)
- [Stage 2 mathematical formulation](#stage-2-mathematical-formulation)
- [Stage 3 circuit and transpilation](#stage-3-circuit-and-transpilation)
- [Noise and error analysis](#noise-and-error-analysis)
- [Quantum implementation](#quantum-implementation)
- [Official results](#official-results)
- [Business conclusions](#business-conclusions)
- [Quantum vs classical comparison](#quantum-vs-classical-comparison)
- [Project structure](#project-structure)
- [Installation](#installation)
- [Running the pipeline](#running-the-pipeline)
- [Running the website](#running-the-website)
- [Submission deliverables](#submission-deliverables)
- [Reproducibility](#reproducibility)
- [Source references](#source-references)
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

## Pipeline methodology

### Stage 1: preprocessing, fidelity kernel, and calibration

Stage 1 fits every data-dependent transformation on training data only. `PDaysEngineer` first handles the campaign-specific `pdays` semantics. The preprocessing pipeline then imputes missing values, encodes categorical features, robust-scales numeric features, reduces the transformed matrix to four principal components, and maps the components into `[-pi, pi]` for four-qubit angle encoding. Official test features and customer IDs are used only after fitting, for inference and deterministic ranking.

For a transformed customer vector $x$, the deployed fixed depth-1 feature map applies a Hadamard gate to every qubit, then `RY(x_i)`, fixed zero `RZ`/`RY` rotations, and a linear CNOT chain. If $|\phi(x)\rangle$ is the resulting state, the precomputed kernel supplied to a class-balanced SVM is the squared fidelity

$$
K(x,z) = \left|\langle\phi(x)\mid\phi(z)\rangle\right|^2.
$$

Probability calibration is also training-only. A seeded stratified 25% inner holdout fits a logistic Platt calibrator to SVM decision scores; the SVM is then refitted on all 300 labeled rows. The calibrated probabilities drive the official ranking. Reported cross-validation metrics are exploratory estimates on labeled training data, not results on the unlabeled official test set.

### Stage 2: exact and quantum-assisted optimization

The ten highest-ranked Stage 1 candidates are joined to their expected deposit value, contact cost, and capacity data. Exact enumeration evaluates all $\binom{10}{6}=210$ six-customer selections and provides the authoritative optimum. Standard QAOA solves a decision-plus-slack QUBO, while cardinality-preserving QAOA works directly on the ten decision qubits. Both QAOA variants use seeded COBYLA optimization and finite-shot Aer sampling. The provably optimal exact selection, rather than a quantum sample, is passed to Stage 3.

### Stage 3: probability simulation

Each selected customer is modeled as an independent Bernoulli outcome using the unchanged Stage 1 probability. The pipeline calculates the exact Poisson-binomial distribution, constructs the corresponding six-qubit circuit, evaluates its ideal statevector, samples it on Qiskit Aer, compares seeded classical Monte Carlo, and runs one explicitly parameterized synthetic-noise sensitivity experiment. This separates analytic truth, ideal quantum simulation, finite-shot sampling, and controlled noise.

## Stage 2 mathematical formulation

For candidate $i$, let $x_i\in\{0,1\}$ indicate selection, $p_i$ be the Stage 1 subscription probability, $d_i$ the expected deposit value, $c_i$ the contact cost, and $h_i$ the capacity units. The implemented constrained problem is

$$
\max_{x}\quad \sum_{i=1}^{10} x_i\left(p_i d_i-c_i\right)
$$

subject to

$$
\sum_{i=1}^{10}x_i=6,
\qquad
\sum_{i=1}^{10}c_i x_i\le 25,
\qquad
\sum_{i=1}^{10}h_i x_i\le 22,
\qquad
x_i\in\{0,1\}.
$$

The standard QAOA implementation converts maximization to energy minimization. With $v_i=p_i d_i-c_i$, binary cost-slack bits $s_j$, capacity-slack bits $t_k$, and penalty $\lambda$, the QUBO energy is

$$
\begin{aligned}
E(x,s,t)={}&-\sum_i v_i x_i
+\lambda\left(\sum_i x_i-6\right)^2\\
&+\lambda\left(\sum_i c_i x_i+\sum_j w^{(c)}_j s_j-25\right)^2\\
&+\lambda\left(\sum_i h_i x_i+\sum_k w^{(h)}_k t_k-22\right)^2.
\end{aligned}
$$

The bounded binary slack weights are $w^{(c)}=[1,2,4,8,10]$ for contact cost and $w^{(h)}=[1,2,4,8,7]$ for capacity. The instance-specific penalty is $\lambda=64.28244844572103$, computed as one plus the sum of absolute candidate objective contributions. Standard QAOA therefore uses 10 decision qubits plus two five-qubit slack registers, for 20 logical qubits. Its circuit starts in a uniform superposition, applies the QUBO cost phase with `RZ`/`RZZ` gates, and uses an `RX` mixer.

The cardinality-preserving variant uses only the 10 decision qubits. It initializes a Hamming-weight-six basis state and alternates the diagonal penalized objective with a ring of paired `RXX` and `RYY` interactions. This XY-style mixer preserves Hamming weight, so $\sum_i x_i=6$ holds throughout ideal evolution; the recorded probability of leaving the weight-six subspace is `0.0`. Budget and capacity violations remain penalized in the diagonal cost. Exact enumeration is the classical certificate for QAOA feasibility and optimality gaps.

## Stage 3 circuit and transpilation

For selected-customer probability $p_i$, qubit $i$ starts in $|0\rangle$ and receives

$$
\theta_i=2\arcsin\sqrt{p_i},
\qquad
RY(\theta_i)|0\rangle=\sqrt{1-p_i}|0\rangle+\sqrt{p_i}|1\rangle.
$$

All six qubits are measured in the computational basis. The number of `1` bits is the simulated subscription count, and bitstrings with Hamming weight at least three are successes. No entangling gates are used because Stage 3 assumes independent customer outcomes. The circuit contains six `RY` gates followed by six measurements.

The requested depth-two resource comparison is below. Original and transpiled depths are equal under the recorded Aer transpilation; no routing SWAPs were introduced.

| Circuit | Logical qubits | Physical hardware qubits | Original depth | Transpiled depth | Recorded gate counts | SWAPs | Final sampling shots |
|---|---:|---|---:|---:|---|---:|---:|
| Standard QAOA, $p=2$ | 20 | N/A (simulator) | 106 | 106 | `rz: 620`, `rzz: 330`, `u2: 20`, `u3: 20`, `rx: 20`, `measure: 20` | 0 | 128 |
| Cardinality-preserving QAOA, $p=2$ | 10 | N/A (simulator) | 12 | 12 | `rxx: 20`, `ryy: 20`, `x: 6`, `diagonal: 2`, `measure: 10` | 0 | 128 |
| Stage 3 probability circuit | 6 | N/A (simulator) | 2 | 2 | `ry: 6`, `measure: 6` | 0 | 1,024 / 4,096 / 16,384 |

Physical hardware qubits are N/A because every experiment used local classical simulators; there was no physical-device mapping or hardware execution. The QAOA counts are identical for both recorded seeds at each formulation/depth.

## Noise and error analysis

The exact Poisson-binomial result is $P(S\ge3)=0.4669729140887742$. The ideal statevector gives `0.4669729140887741`; their maximum full-distribution difference is `1.1102230246251565e-16`, i.e. floating-point precision.

| Method | Samples / shots | Estimate of $P(S\ge3)$ | Absolute error vs exact | Standard error | Normal 95% half-width |
|---|---:|---:|---:|---:|---:|
| Exact Poisson-binomial | Exact | 0.4669729141 | 0 | N/A | N/A |
| Ideal statevector | Analytic | 0.4669729141 | ~`1.1e-16` | N/A | N/A |
| Qiskit Aer | 1,024 | 0.4580078125 | 0.0089651016 | 0.0155697980 | 0.0305168041 |
| Qiskit Aer | 4,096 | 0.4594726562 | 0.0075002578 | 0.0077867942 | 0.0152621166 |
| Qiskit Aer | 16,384 | 0.4659423828 | 0.0010305313 | 0.0038971776 | 0.0076384681 |
| Classical Monte Carlo | 1,024 | 0.4863281250 | 0.0193552109 | 0.0156191577 | 0.0306135490 |
| Classical Monte Carlo | 4,096 | 0.4597167969 | 0.0072561172 | 0.0077871035 | 0.0152627228 |
| Classical Monte Carlo | 16,384 | 0.4645385742 | 0.0024343399 | 0.0038964133 | 0.0076369701 |
| Controlled-noise Aer | 4,096 | 0.4846191406 | 0.0176462265 | 0.0078088027 | 0.0153052533 |

For each sampled estimate $\hat p$ with $N$ shots or samples, the implementation reports $SE=\sqrt{\hat p(1-\hat p)/N}$ and normal-approximation 95% half-width $1.96\,SE$. The decreasing half-widths show the expected $1/\sqrt{N}$ sampling behavior. Individual seeded estimates need not approach the exact value monotonically, but the highest-shot Aer run is within about `0.00103` absolute probability.

The controlled-noise run is a sensitivity experiment, not hardware data. It applies `0.005` one-qubit depolarizing error to every `RY` gate and symmetric `0.01` readout error, using 4,096 shots and seed 142. Its estimate shifts to `0.4846191406`, an absolute error of `0.0176462265`; gate/readout noise can therefore introduce bias in addition to finite-shot uncertainty. No mitigation or extrapolation is claimed.

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

## Business conclusions

The recommended campaign contains `C0079`, `C0088`, `C0202`, `C0345`, `C0258`, and `C0339`. Under the model, this portfolio has expected net objective `45.0419817314`, uses contact cost `15` of the available `25`, and uses capacity `16` of `22`. It is the exact optimum among all 210 six-customer combinations. The best cardinality-preserving QAOA run also sampled this portfolio with zero measured objective gap, but exact enumeration is the operational selection because it proves optimality at this scale.

Assuming the six predicted outcomes are independent Bernoulli variables with the Stage 1 probabilities, the modeled probability of at least three subscriptions is `0.4669729141` (46.70%). These are **predicted expected outcomes**, not observed business returns: the official test set is unlabeled, no outreach outcome is included, and no realized deposits, revenue, or profit are claimed. Model calibration, independence, and data representativeness remain material business assumptions.

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

## Submission Deliverables

- [Stage 1 predictions](stage1_predictions.csv)
- [Stage 2 selection](stage2_selection.json)
- [Stage 3 simulation](stage3_simulation.json)

## Reproducibility

- Official execution requires authorized copies of the three organizer files listed in [Quick start](#quick-start).
- `requirements.txt` and `web/package-lock.json` pin the validated dependencies.
- `artifacts/stage1_final_model.joblib` contains the fitted primary Stage 1 model.
- `artifacts/stage1_final_model_metadata.json` records feature-map, calibration, and training details.
- `configs/` records seeds and experiment settings.
- Official result files and detailed simulator/QAOA outputs are committed.
- The principal seeds are 42 and 137; per-shot Stage 3 runs record their exact seeds in JSON.

The official validator checks row counts, schemas, unique IDs, top-ten membership, constraints, and unchanged Stage 1 probabilities through Stage 3.

A complete official rerun requires authorized organizer copies of both workbooks and the challenge PDF listed in [Quick start](#quick-start). Those source datasets are not included in the public repository because no public redistribution license was supplied. Without them, judges can inspect the committed outputs, reports, fitted-model metadata, tests, and application, and can run the safe synthetic demonstration; they cannot regenerate the official predictions from raw organizer data. No hidden download or substitute dataset is used.

## Source references

The technical report above is traceable to these committed artifacts:

- [Stage 1 official predictions](stage1_result.csv) and [submission-form filename](stage1_predictions.csv)
- [Stage 2 official selection and QAOA results](stage2_result.json) and [submission-form filename](stage2_selection.json)
- [Stage 3 official probability, shot, Monte Carlo, and noise results](stage3_result.json) and [submission-form filename](stage3_simulation.json)
- [Quantum circuit resource audit](reports/quantum_circuit_resources.json)
- [Stage 2 circuit complexity and QUBO register details](reports/stage2_circuit_complexity.json)
- [Final submission report](reports/final_submission_report.md)
- [Submission compliance audit](reports/submission_compliance_audit.md)
- [Stage 1 fitted-model metadata](artifacts/stage1_final_model_metadata.json)
- [Stage 1 model implementation](src/pennylane_models.py), [QUBO formulation](src/optimization/qubo_formulation.py), [standard QAOA](src/optimization/qaoa_standard.py), [cardinality-preserving QAOA](src/optimization/qaoa_constrained.py), and [Stage 3 sampler](src/simulation/quantum_sampler.py)

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
