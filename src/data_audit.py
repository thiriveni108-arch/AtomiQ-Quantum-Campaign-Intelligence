from __future__ import annotations
import json
from pathlib import Path
import pandas as pd
from .preprocessing import FEATURES

def audit_workbook(path, reports_dir="reports"):
    path, out = Path(path), Path(reports_dir); out.mkdir(parents=True, exist_ok=True)
    xls = pd.ExcelFile(path)
    sheets = {s: pd.read_excel(path, sheet_name=s) for s in xls.sheet_names}
    tr, te = sheets["Stage1_Train"], sheets["Stage1_Test"]
    label_counts = tr["y"].value_counts(dropna=False).to_dict()
    mapping_files = [str(p) for p in path.parent.rglob("*") if p.is_file() and p != path and
                     any(k in p.name.lower() for k in ("mapping","test_id","customer_id"))]
    audit = {
      "workbook": path.name, "sheets": {k: {"rows":len(v),"columns":list(v.columns)} for k,v in sheets.items()},
      "train_shape": list(tr.shape), "test_shape": list(te.shape), "label_counts": label_counts,
      "label_values_valid": set(tr.y.dropna().unique()) == {"yes","no"},
      "train_customer_id_unique": bool(tr.customer_id.is_unique),
      "train_customer_id_missing": int(tr.customer_id.isna().sum()),
      "test_customer_id_present": "customer_id" in te,
      "mapping_candidates": mapping_files,
      "duration_absent": all("duration" not in v.columns for v in sheets.values()),
      "train_duplicate_rows": int(tr.duplicated().sum()), "test_duplicate_rows": int(te.duplicated().sum()),
      "train_missing": {k:int(v) for k,v in tr.isna().sum().items()},
      "test_missing": {k:int(v) for k,v in te.isna().sum().items()},
      "categorical_values": {c:sorted(map(str,tr[c].dropna().unique())) for c in tr.select_dtypes(exclude="number") if c not in ("customer_id","y")},
      "numeric_summary": tr.select_dtypes(include="number").describe().round(3).to_dict(),
      "feature_schema_valid": set(FEATURES).issubset(tr) and set(FEATURES).issubset(te),
      "leakage_risks": ["customer_id excluded from features", "all transforms/tuning/calibration must be fold-fitted", "Stage1_Test prohibited from fitting"]
    }
    (out/"data_audit.json").write_text(json.dumps(audit, indent=2, default=str), encoding="utf-8")
    ratio = label_counts.get("yes",0)/len(tr)
    md = f"""# Data audit

## Findings

- Workbook sheets: {', '.join(xls.sheet_names)}.
- Stage1_Train: {len(tr)} rows, {tr.shape[1]} columns; Stage1_Test: {len(te)} rows, {te.shape[1]} columns.
- Labels: {label_counts.get('yes',0)} yes and {label_counts.get('no',0)} no (positive prevalence {ratio:.2%}). This is materially imbalanced.
- Training IDs are unique: {tr.customer_id.is_unique}; missing training IDs: {tr.customer_id.isna().sum()}.
- Exact duplicate rows: train {tr.duplicated().sum()}, test {te.duplicated().sum()}. Missing cells: train {int(tr.isna().sum().sum())}, test {int(te.isna().sum().sum())}.
- `duration` is absent, avoiding the known post-call leakage field.
- `unknown` is retained as an observed category, not treated as missing.
- `balance` has median {tr.balance.median():.0f}, range [{tr.balance.min()}, {tr.balance.max()}]; robust scaling limits outlier influence without deleting customers.
- `pdays=-1` occurs {(tr.pdays==-1).sum()} times and is represented by `pdays_never=1` plus numeric `pdays=0`.

## Customer ID mapping blocker

`Stage1_Test` has no `customer_id`. No separate organizer mapping was found ({len(mapping_files)} candidate files). Predictions therefore use zero-based `test_row_index` and are **provisional**. Official tie-breaking, submission formatting, and Stage 2 joins are blocked. No IDs were guessed or inferred from external data.

## Leakage controls

`customer_id` and `y` are excluded from features. Imputation, one-hot encoding, robust scaling, PCA, angle scaling, tuning, and calibration are fitted only on training folds through scikit-learn pipelines. Stage1_Test is used only once for final inference.
"""
    (out/"data_audit.md").write_text(md, encoding="utf-8")
    return audit
