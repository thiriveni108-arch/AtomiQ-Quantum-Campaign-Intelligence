from __future__ import annotations
from dataclasses import dataclass
import json,math
from pathlib import Path

class OfficialStage3Blocked(RuntimeError): pass

@dataclass(frozen=True)
class SubscriptionRecord:
    customer_id: str
    predicted_probability: float

def validate_records(records):
    if len(records)!=6: raise ValueError(f"Stage 3 requires exactly six customer records, got {len(records)}")
    ids=[r.customer_id for r in records]
    if any(not isinstance(i,str) or not i.strip() for i in ids): raise ValueError("customer_id must be non-empty")
    if len(set(ids))!=6: raise ValueError("Duplicate customer_id values are not allowed")
    for r in records:
        if not math.isfinite(r.predicted_probability) or not 0<=r.predicted_probability<=1: raise ValueError(f"Invalid probability for {r.customer_id}")
    return records

def load_demo(stage2_solution="results/stage2_demo_exact_solution.json",stage2_config="configs/stage2_experiments.json"):
    solution=json.loads(Path(stage2_solution).read_text(encoding="utf-8")); config=json.loads(Path(stage2_config).read_text(encoding="utf-8"))
    if solution.get("official") is not False or solution.get("mode")!="demo": raise ValueError("Expected a synthetic Stage 2 demo artifact")
    selected=solution["exact"]["best"]["selected_ids"]; by_id={r["customer_id"]:r for r in config["demo_candidates"]}
    if len(selected)!=6 or len(set(selected))!=6 or any(i not in by_id for i in selected): raise ValueError("Stage 2 demo selection is inconsistent with its candidate configuration")
    return validate_records([SubscriptionRecord(i,float(by_id[i]["predicted_probability"])) for i in selected])

def load_official(path="results/stage2_official_selection.json"):
    p=Path(path)
    if not p.exists(): raise OfficialStage3Blocked("OFFICIAL STAGE 3 BLOCKED: no verified official Stage 2 selection artifact exists. Resolve the Stage1_Test customer-ID mapping and run official Stage 2 first.")
    data=json.loads(p.read_text(encoding="utf-8"))
    if data.get("official") is not True: raise OfficialStage3Blocked("OFFICIAL STAGE 3 BLOCKED: the supplied Stage 2 artifact is not marked official.")
    records=data.get("selected_customers",[])
    return validate_records([SubscriptionRecord(str(r["customer_id"]),float(r["predicted_probability"])) for r in records])
