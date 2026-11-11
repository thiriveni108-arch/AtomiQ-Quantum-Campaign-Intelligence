# Stage 2 quantum-classical optimization report

## Status and data boundary

This is a **synthetic DEMO experiment**, not an official Stage 2 selection. The existing Stage 1 file contains `test_row_index` and provisional probabilities but no verified `customer_id`. Official mode therefore terminates with:

> OFFICIAL MODE BLOCKED: Stage 1 predictions have no verified customer_id. Obtain the organizer row-to-ID mapping, regenerate predictions with IDs, then retry.

No row-order assumption, guessed ID, Stage2_Data join, or official selection artifact was created. Stage 1 code, models, predictions, and artifacts were not retrained or modified. Stage 3 was not implemented.

The workbook constraints were read as `N=10`, `K=6`, budget `C=25`, and capacity `H=22`. Official contact costs lie in `[1,4]`; consequently, for exactly six selections their maximum possible sum is 24, so the official budget constraint is mathematically redundant. Capacity can still bind. The synthetic fixture uses values in the official ranges and deliberately makes capacity binding.

## Mathematical problem

For candidate decision bits `x_i`, expected net values are

`v_i = p_i d_i - c_i`.

The exact problem maximizes `Σ v_i x_i`, subject to `Σx_i=6`, `Σc_i x_i≤25`, `Σh_i x_i≤22`, and binary `x_i`.

The exhaustive reference checks all `C(10,6)=210` combinations. Ties are resolved by ascending lexicographic tuple of sorted customer IDs after objective values are rounded to numerical tolerance.

## Standard slack-variable QUBO

QAOA minimizes

`E(z) = -Σv_i x_i + P(Σx_i-6)² + P(Σc_i x_i+s_c-25)² + P(Σh_i x_i+s_h-22)²`.

The bounded slack encodings are:

- budget: weights `[1,2,4,8,10]`, exactly representing every integer from 0 through 25;
- capacity: weights `[1,2,4,8,7]`, exactly representing every integer from 0 through 22.

Thus standard QAOA needs 10 decision + 5 budget slack + 5 capacity slack = **20 qubits**. The implementation does not claim a 10-qubit slack formulation.

`P = Σ|v_i|+1 = 100.66` in the demo. A unit constraint violation then costs more than the maximum possible objective swing for this fixed instance. This establishes separation for this instance only; it is not a universal penalty guarantee.

After QUBO expansion, each binary product uses `x_i=(1-Z_i)/2`. Linear QUBO terms become Z rotations and pair terms become Z/Z interactions plus their required single-Z components. Unit tests compare expanded QUBO energy to the direct penalized objective for every one of the 1,024 decision strings, including encoded slack.

Standard QAOA begins in `|+>^20`, applies the QUBO phase separator and X mixer, and measures all 20 qubits. The first 10 little-endian decoded bits are decisions; the rest are slack. Every measured decision is rechecked against the original constraints.

## Cardinality-preserving QAOA

The constraint-aware circuit begins at the feasible-weight basis state `|1111110000>` in Qiskit wire order. Alternating RXX/RYY interactions implement an XY ring mixer. Statevector verification found exactly `0.0` probability outside Hamming weight six.

This mixer enforces only cardinality. Capacity is encoded in an exact 10-qubit diagonal phase function using `P·max(0,capacity-22)²`; budget uses the analogous term, although it is redundant for official ranges. Measurements are still filtered through the original constraints. The exact diagonal operator is convenient for this 1,024-state research instance but is not a scalable two-local construction.

## Synthetic exact reference

- Global optimum: **81.92**
- Selected demo IDs: `DEMO01, DEMO02, DEMO03, DEMO04, DEMO05, DEMO09`
- Total contact cost: **13**
- Total capacity: **22**
- Feasible combinations: **203 / 210**
- Runtime: **0.0011 s**

## Shot-based QAOA results

All circuits actually ran on local Qiskit Aer simulators. COBYLA was intentionally bounded to the minimum practical 4 evaluations for p=1 and 6 for p=2 after the original eight-iteration/128-shot budget exceeded 15 minutes. Optimization used 32 shots/evaluation; final estimates used 128 shots. Results therefore have substantial shot and optimizer noise.

| Formulation | p | Seed | Best feasible | Gap | Feasible shots | Optimum shots | Runtime s |
|---|---:|---:|---:|---:|---:|---:|---:|
| Standard | 1 | 42 | 81.53 | 0.39 | 0.211 | 0.000 | 0.96 |
| Standard | 1 | 137 | 80.28 | 1.64 | 0.133 | 0.000 | 0.83 |
| Standard | 2 | 42 | 81.53 | 0.39 | 0.227 | 0.000 | 1.57 |
| Standard | 2 | 137 | 80.28 | 1.64 | 0.195 | 0.000 | 1.70 |
| Cardinality | 1 | 42 | 59.81 | 22.11 | 1.000 | 0.000 | 0.67 |
| Cardinality | 1 | 137 | 81.53 | 0.39 | 0.984 | 0.000 | 0.56 |
| Cardinality | 2 | 42 | 81.53 | 0.39 | 0.992 | 0.000 | 0.84 |
| Cardinality | 2 | 137 | 81.53 | 0.39 | 0.969 | 0.000 | 0.89 |

No finite-shot QAOA run sampled the exact optimum. The best sampled gap was 0.39 (0.476%). Cardinality QAOA raised mean feasible-shot probability from **0.191** to **0.986**, as expected from a weight-preserving mixer, but seed 42/p=1 also shows that feasibility does not imply good objective quality.

For the 10-qubit cardinality circuits, exact statevector analysis at the optimized parameters gave ideal feasible probabilities from 0.964 to 0.998. Ideal exact-optimum probability was zero at p=1, 0.00260 for p=2/seed 42, and 0.000246 for p=2/seed 137. The finite 128-shot absence of the optimum is consistent with those small probabilities. The expensive 20-qubit ideal post-pass was not completed; its ideal fields are explicitly missing rather than inferred from shots.

## Circuit resources

- Standard p=1: 20 qubits, depth 66, 535 operations (`165 RZZ`, `310 RZ`, plus initialization/mixer/measurement).
- Standard p=2: 20 qubits, depth 106, 1,030 operations (`330 RZZ`, `620 RZ`, plus initialization/mixer/measurement).
- Cardinality p=1: 10 qubits, logical depth 7, 37 high-level operations.
- Cardinality p=2: 10 qubits, logical depth 12, 58 high-level operations.

The cardinality resource counts retain the high-level diagonal instruction; hardware decomposition would be substantially deeper. Text diagrams and exact metadata are in `reports/stage2_circuits/` and `reports/stage2_circuit_complexity.json`.

## Interpretation

A measurement represents one binary contact plan. Standard QAOA explores decision and slack assignments, so many measured plans fail the original constraints. Cardinality QAOA restricts exploration to six selected customers but still needs capacity handling and post-measurement validation.

The experiment demonstrates genuine quantum-circuit optimization, not a classical solver labeled QAOA. It does **not** demonstrate quantum advantage. Enumeration solved this ten-customer instance exactly in roughly a millisecond, faster and more reliably than every simulated QAOA configuration. p=2 modestly improved some solution probabilities but did not reliably sample the optimum under the bounded budget.

## Tests and reproduction

The full suite contains 17 passing tests covering previous Stage 1/PennyLane behavior plus exact optimality, infeasibility, ties, negative values, probability extremes, all-string QUBO equivalence, slack ranges, endian decoding, mixer preservation, schema validation, and the official-mode blocker.

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe run_stage2.py --mode demo
.\.venv\Scripts\python.exe run_stage2.py --mode official
```

The final command must remain blocked until a verified Stage1_Test row-to-customer-ID mapping is supplied.
