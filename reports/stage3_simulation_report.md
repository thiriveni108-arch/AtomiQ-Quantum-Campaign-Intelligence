# Stage 3 six-qubit subscription simulation

## Status and integration boundary

This report is for **DEMO MODE only**. It consumes the exact synthetic Stage 2 selection already saved in `results/stage2_demo_exact_solution.json` and retrieves those customers' existing probabilities from `configs/stage2_experiments.json`. No probabilities or IDs were invented for Stage 3.

Official execution remains blocked because there is no verified Stage 1 test-row-to-customer-ID mapping and therefore no official Stage 2 selection artifact. `run_stage3.py --mode official` fails explicitly rather than writing synthetic data under an official filename.

## Demo input

| Customer | Predicted probability | RY angle (radians) |
|---|---:|---:|
| DEMO01 | 0.82 | 2.265295 |
| DEMO02 | 0.74 | 2.071451 |
| DEMO03 | 0.68 | 1.939064 |
| DEMO04 | 0.61 | 1.792611 |
| DEMO05 | 0.55 | 1.670964 |
| DEMO09 | 0.31 | 1.181000 |

Exactly six distinct customers are required and probabilities must be finite and lie in `[0,1]`.

## Quantum encoding

For customer `i`, Stage 3 applies

`θ_i = 2 asin(sqrt(p_i))`

and then `RY(θ_i)|0>`. The probability of measuring that qubit as one is `sin²(θ_i/2)=p_i`, so a measured one represents a simulated subscription. Six customers require exactly six qubits. An outcome is successful when its Hamming weight is at least three.

The circuit contains six RY gates and six measurements. Its reported depth including measurement is 2, with 12 operations. There are no entangling gates because the model assumes conditionally independent customer outcomes.

## Exact reference

The number of subscriptions follows a Poisson-binomial distribution: a sum of independent Bernoulli variables with non-identical probabilities. A dynamic program produced:

| Subscriptions k | P(X=k) |
|---:|---:|
| 0 | 0.001813519 |
| 1 | 0.023144687 |
| 2 | 0.113676023 |
| 3 | 0.274553662 |
| 4 | 0.341133225 |
| 5 | 0.202763926 |
| 6 | 0.042914959 |

Therefore, **P(X≥3) = 0.8613657712**.

The distribution sums to one to numerical precision. Ideal Qiskit statevector amplitudes gave `P(X≥3)=0.8613657711999999`; the maximum bin-wise difference from the dynamic program was `1.11×10⁻¹⁶`.

## Aer shot experiments

These estimates came from actual measured Qiskit Aer bitstrings using fixed seeds—not from a separate classical random-number generator.

| Shots | Seed | Successful outcomes | Estimate | Absolute error | Standard error | 95% normal half-width | Runtime s |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1,024 | 42 | 898 | 0.876953125 | 0.015587354 | 0.010265344 | 0.020120074 | 0.0133 |
| 4,096 | 43 | 3,478 | 0.849121094 | 0.012244677 | 0.005592669 | 0.010961631 | 0.0110 |
| 16,384 | 44 | 14,094 | 0.860229492 | 0.001136279 | 0.002708975 | 0.005309591 | 0.0406 |

Sampling standard error scales approximately as `1/sqrt(shots)`, so it falls as shots increase. Realized absolute error need not decrease monotonically in every run, although it did here. The 16,384-shot result is within 0.00114 of the exact probability.

Per-shot-count distributions over all seven Hamming weights are stored in `results/stage3_demo_distribution.csv`.

## Assumption and scientific interpretation

The circuit assumes the six subscription outcomes are independent after conditioning on their Stage 1 probabilities. Real customers can share economic, geographic, campaign-timing, or model-error dependencies. Ignoring positive dependence can understate tail risk; ignoring negative dependence can overstate it. The available Stage 1 output supplies marginal probabilities but no defensible joint dependence model, so independence is explicit rather than hidden.

This is a genuine quantum probability-encoding and sampling experiment: amplitudes encode Bernoulli probabilities and Aer measures the circuit. It is not evidence of quantum computational advantage. For six independent customers, the classical dynamic program is exact, cheap, and preferable as the correctness reference.

## Validation and reproduction

The complete project suite passes **32 tests**. Stage 3 coverage includes all-zero, all-one, exactly three certain subscriptions, the analytical six-fair-coin result `42/64=0.65625`, mixed inputs, invalid/non-finite inputs, wrong customer counts, duplicate IDs, bit ordering, Hamming weights, circuit gates, statevector equivalence, Stage 2 demo consistency, and the official blocker.

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe run_stage3.py --mode demo
.\.venv\Scripts\python.exe run_stage3.py --mode official
```

The last command must remain blocked until verified customer IDs permit a genuine official Stage 2 selection.
