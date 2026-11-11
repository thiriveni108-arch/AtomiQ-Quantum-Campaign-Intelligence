# Submission compliance audit

Sources audited: official four-page challenge PDF, revised workbook README, all sheets, executed code, artifacts, and 42 automated tests.

| Requirement | Source | Evidence | Status | Note/action |
|---|---|---|---|---|
| 300 train / 100 test; continuous probabilities | PDF pp.1–2; README | `stage1_result.csv`, data audit | PASS | 100 unique IDs/probabilities |
| At least one quantum classifier and classical baseline | PDF p.1 | Qiskit QSVC/VQC, PennyLane kernels, LR/RBF-SVM | PASS | RBF-SVM selected on calibration evidence |
| Training-only preprocessing/tuning/calibration | PDF pp.1–2 | sklearn pipelines and nested folds | PASS | Test features used only for final inference |
| Rank descending; lower customer ID breaks ties | PDF p.2 | `src/integration.py` | PASS | Stable probability-descending/ID-ascending sort |
| Stage 1 result: ID, probability, rank, top-10 | PDF p.3 | `stage1_result.csv` | PASS | Exact requested fields represented |
| Same Stage 1 probabilities across stages | PDF p.2 | Stage 1→2→3 validator | PASS | Equality checked to 1e-12 |
| Select exactly six unique top-10 IDs | PDF p.2 | `stage2_result.json` | PASS | Six exact-optimum IDs, all within top 10 |
| Budget and capacity constraints | PDF p.2; workbook | Stage 2 exact result | PASS | Cost 14≤25; capacity 20≤22 |
| Quantum/hybrid binary optimizer and constraint explanation | PDF p.2 | Standard slack QUBO + cardinality QAOA reports | PASS | Penalties, auxiliaries, decoding documented |
| Optimized parameters and measured bitstrings | PDF pp.2–3 | `stage2_result.json` | PASS | All configurations include parameters and best decision bitstring |
| Exact classical Stage 2 comparison and gap | PDF pp.2–3 | Stage 2 result/CSV | PASS | Exact 12.013583; best quantum 11.734720; 2.321% gap |
| Six-qubit Stage 3, one qubit/customer | PDF p.2 | `stage3_result.json`, circuit PNG | PASS | Six RY gates; order recorded |
| Independent response assumption and Hamming weight≥3 | PDF p.2 | Stage 3 code/report/tests | PASS | Explicit assumption and endian tests |
| Exact and Monte Carlo Stage 3 validation | PDF p.3 | Stage 3 JSON/CSVs | PASS | Exact DP, statevector, MC, Aer shots |
| Stage 3 measurement counts, estimates, errors | PDF p.3 | `stage3_result.json` | PASS | Raw bitstrings and distributions included |
| Seeds, versions, backend, shots | PDF p.3 | configs and circuit resource JSON | PASS | Seeds and local simulators recorded |
| Logical/physical qubits, depths, gates, SWAP | PDF p.3 | `reports/quantum_circuit_resources.json` | PASS | Physical qubits N/A for simulators, not fabricated |
| Ideal, noiseless-shot, noisy results | PDF p.3 | Stage 3 result/noise CSV | PASS | Controlled synthetic noise clearly labeled |
| Runnable end-to-end code and README | PDF p.3 | `run_end_to_end.py`, README | PASS | Demo, official, validate modes |
| Three result files at top level | PDF p.3 | `stage1_result.csv`, `stage2_result.json`, `stage3_result.json` | PASS | PDF defines contents, not fixed names |
| Customer ID key in every official file | PDF p.3 | Three top-level results | PASS | Direct revised-workbook IDs |
| No unsupported quantum advantage claim | PDF p.2 | Unified and stage reports | PASS | Exact methods identified as operational references |

## Provenance qualification

The user supplied `bank_campaign_participant_release-1.xlsx` as the updated participant workbook alongside the official PDF. The revision changes only the missing ID column and has consistent workbook authorship/timestamps. The pipeline therefore treats it as the authorized revision. There is no embedded digital organizer signature, so cryptographic provenance cannot be independently established from file contents alone.

## Final status

All executable and data-integrity requirements are **PASS**. The official three-stage pipeline executed successfully. No demo data appears in the three top-level official result files.
