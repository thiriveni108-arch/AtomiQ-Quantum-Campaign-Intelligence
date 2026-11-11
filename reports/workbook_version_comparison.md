# Workbook version comparison

## Files and provenance evidence

| File | SHA-256 | Size |
|---|---|---:|
| `bank_campaign_participant_release.xlsx` | `ff65cb30ceb8a32d682644cd8b161234c80f1315736d909c03afccd5553ef823` | 59,082 bytes |
| `bank_campaign_participant_release-1.xlsx` | `d2f8e63705af2883c7618c463a6ac2f351119d59a8869d2677f8825148e9a709` | 50,217 bytes |
| `PROBLEM_STATEMENT_THEATOMIQHACKTHON.pdf` | `8b1d38d02010fbad9c297d57c13085b01d9b26a3741152a21a54cc3609c48363` | 801,680 bytes |

Both workbooks report creator `openpyxl`, creation time `2026-11-03 23:35:33`, and last editor `Arna Roy`. The old workbook modification time is `2026-11-04 14:57:43`; the revised workbook is `2026-11-10 17:59:54`. The user supplied the latter explicitly as the updated participant workbook alongside the official challenge PDF. These facts strongly support revision provenance, but neither file contains a cryptographic organizer signature.

## Cell-level comparison

| Sheet/content | Old | Revised | Result |
|---|---:|---:|---|
| Sheet names | 5 | 5 | Identical |
| README | 21×2 | 21×2 | All cells identical |
| Stage1_Train | 300×17 | 300×17 | All cells, labels, IDs, and row order identical |
| Stage1_Test | 100×15 | 100×16 | All 1,500 feature cells and row order identical; revised adds `customer_id` only |
| Stage2_Data | 400×5 | 400×5 | All cells and row order identical |
| Stage2_Constraints | 6×4 | 6×4 | All cells identical |

## Revised test-ID validation

- 100 IDs; zero missing; 100 unique.
- Every test ID exists in Stage2_Data.
- No test ID overlaps Stage1_Train.
- The test-ID set equals exactly `Stage2_Data IDs − Stage1_Train IDs`.
- IDs are attached directly to unchanged test rows; no sorting or inferred pairing is used.

The customer mapping issue is therefore resolved for the revised workbook. The old workbook remains blocked because its Stage1_Test still has no ID column.

## Model compatibility

Because every training and test feature value and row position is unchanged, the prior calibrated RBF-SVM remained compatible and its revised-workbook probabilities matched the provisional values exactly. A later explicit model-deployment decision replaced it with the preselected fixed depth-1 PennyLane RY/CNOT kernel; that model was trained on all 300 unchanged labels. This change is a model decision, not a response to altered data.

## PDF audit

The four-page scanned official specification was visually reviewed in full. It confirms training-only development, continuous probabilities, customer-ID tie-breaking, exact-six constrained selection, exact classical comparison, independent six-qubit Stage 3 simulation, three result files, seeds/package/backend/circuit resources, and noiseless/noisy results where applicable. It specifies the content of the three result files but not fixed filenames; this project uses `stage1_result.csv`, `stage2_result.json`, and `stage3_result.json` at repository top level.
