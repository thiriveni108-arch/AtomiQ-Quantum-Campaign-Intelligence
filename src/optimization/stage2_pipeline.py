from __future__ import annotations
import json
from pathlib import Path
import pandas as pd
from .exact_solver import Candidate,Constraints,validate_candidates

class OfficialIntegrationBlocked(RuntimeError): pass

def candidates_from_records(records):
    required={"customer_id","predicted_probability","contact_cost","expected_deposit_value","capacity_units"}
    out=[]
    for r in records:
        missing=required-set(r)
        if missing: raise ValueError(f"Candidate record missing {sorted(missing)}")
        out.append(Candidate(r["customer_id"],float(r["predicted_probability"]),int(r["contact_cost"]),float(r["expected_deposit_value"]),int(r["capacity_units"])))
    validate_candidates(out); return out

def load_demo(config_path="configs/stage2_experiments.json"):
    cfg=json.loads(Path(config_path).read_text(encoding="utf-8")); return candidates_from_records(cfg["demo_candidates"]),cfg

def load_official(predictions_path="results/stage1_predictions_official.csv",workbook="bank_campaign_participant_release-1.xlsx"):
    if not Path(predictions_path).exists():
        raise OfficialIntegrationBlocked("OFFICIAL MODE BLOCKED: no verified customer_id prediction file exists. Supply an organizer-verified row mapping and run the official end-to-end command.")
    pred=pd.read_csv(predictions_path)
    if "customer_id" not in pred.columns:
        raise OfficialIntegrationBlocked("OFFICIAL MODE BLOCKED: Stage 1 predictions have no verified customer_id. Obtain the organizer row-to-ID mapping, regenerate predictions with IDs, then retry.")
    if pred.customer_id.isna().any() or pred.customer_id.duplicated().any() or pred.get("status",pd.Series(dtype=str)).astype(str).str.contains("PROVISIONAL",case=False).any():
        raise OfficialIntegrationBlocked("OFFICIAL MODE BLOCKED: prediction customer IDs are missing, duplicated, or provisional.")
    top=pred.sort_values(["predicted_probability","customer_id"],ascending=[False,True],kind="stable").head(10)
    s2=pd.read_excel(workbook,sheet_name="Stage2_Data")
    joined=top[["customer_id","predicted_probability"]].merge(s2,on="customer_id",how="left",validate="one_to_one",indicator=True)
    if (joined._merge!="both").any(): raise OfficialIntegrationBlocked("OFFICIAL MODE BLOCKED: one or more verified candidate IDs are absent from Stage2_Data.")
    return candidates_from_records(joined.to_dict("records"))
