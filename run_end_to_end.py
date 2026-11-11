from __future__ import annotations
import argparse,json
from pathlib import Path
import pandas as pd
from src.integration import build_official_stage1,build_official_stage1_from_workbook,train_official_fixed_quantum_model,verify_updated_workbook,validate_stage1_outputs,MappingVerificationError
from src.circuit_audit import generate_circuit_audit
from src.simulation.stage3_pipeline import load_demo as load_stage3_demo

REQUIRED=["artifacts/stage1_final_model.joblib","results/stage1_predictions_provisional.csv","results/model_comparison.csv",
 "results/stage2_demo_exact_solution.json","results/stage3_demo_probability.json","reports/data_audit.json"]

def validate_all():
    errors=[]
    for p in REQUIRED:
        if not Path(p).exists(): errors.append(f"Missing artifact: {p}")
    errors.extend(validate_stage1_outputs())
    if Path("results/stage2_demo_exact_solution.json").exists():
        s2=json.loads(Path("results/stage2_demo_exact_solution.json").read_text()); ids=s2["exact"]["best"]["selected_ids"]
        if len(ids)!=6 or len(set(ids))!=6: errors.append("Stage 2 demo must select six distinct IDs")
        b=s2["exact"]["best"]
        if b["total_cost"]>25 or b["total_capacity"]>22: errors.append("Stage 2 demo violates constraints")
        s3=load_stage3_demo()
        if [r.customer_id for r in s3]!=ids: errors.append("Stage 2 selected ID order is not propagated unchanged to Stage 3")
    wb="bank_campaign_participant_release-1.xlsx"; s2d=pd.read_excel(wb,sheet_name="Stage2_Data")
    if int(s2d.contact_cost.max())!=4 or 6*int(s2d.contact_cost.max())>=25: errors.append("Workbook budget-redundancy premise changed")
    official_files=[Path("stage1_result.csv"),Path("stage2_result.json"),Path("stage3_result.json")]
    if any(p.exists() for p in official_files):
        if not all(p.exists() for p in official_files): errors.append("Official outputs are incomplete; all three top-level result files are required")
        else:
            s1=pd.read_csv(official_files[0]); s2=json.loads(official_files[1].read_text()); s3=json.loads(official_files[2].read_text())
            if list(s1.columns)!=["customer_id","predicted_probability","rank","top10_flag"] or len(s1)!=100 or s1.customer_id.nunique()!=100 or int(s1.top10_flag.sum())!=10: errors.append("Official Stage 1 schema/content invalid")
            top=set(s1.loc[s1.top10_flag,"customer_id"]); selected=s2["exact"]["best"]["selected_ids"]
            if len(selected)!=6 or len(set(selected))!=6 or not set(selected)<=top: errors.append("Official Stage 2 selection is not six unique Stage 1 top-10 IDs")
            if s2["exact"]["best"]["total_cost"]>25 or s2["exact"]["best"]["total_capacity"]>22: errors.append("Official Stage 2 selection violates constraints")
            qids=[x["customer_id"] for x in s3["customers"]]; qprob={x["customer_id"]:x["predicted_probability"] for x in s3["customers"]}
            s1prob=dict(zip(s1.customer_id,s1.predicted_probability))
            if qids!=selected or any(abs(qprob[i]-s1prob[i])>1e-12 for i in qids): errors.append("Official Stage 2 IDs/probabilities did not propagate unchanged to Stage 3")
    generate_circuit_audit()
    mapping_ready=pdf_ready=False
    try: verify_updated_workbook(); mapping_ready=True
    except Exception as e: errors.append(f"Updated workbook verification: {e}")
    pdf_ready=Path("PROBLEM_STATEMENT_THEATOMIQHACKTHON.pdf").exists()
    official_ready=mapping_ready and pdf_ready
    status={"status":"PASS" if not errors else "FAIL","errors":errors,"official_ready":official_ready,
      "official_blocker":None if official_ready else "Missing validated updated workbook mapping and/or official problem-statement PDF.",
      "provenance_note":"Workbook structure/metadata and user-provided revision context support provenance; no digital organizer signature is embedded."}
    Path("reports/submission_validation.json").write_text(json.dumps(status,indent=2),encoding="utf-8"); print(json.dumps(status,indent=2))
    if errors: raise SystemExit(1)

def main(mode,mapping=None,mapping_metadata=None,workbook="bank_campaign_participant_release-1.xlsx"):
    if mode=="validate": validate_all(); return
    if mode=="demo":
        from run_stage2 import main as stage2; from run_stage3 import main as stage3
        stage2("demo"); stage3("demo"); validate_all(); return
    if Path(workbook).exists():
        train_official_fixed_quantum_model(workbook)
        build_official_stage1_from_workbook(workbook)
    elif mapping and mapping_metadata: build_official_stage1(mapping,mapping_metadata)
    else: raise MappingVerificationError("OFFICIAL MODE BLOCKED: provide the validated updated workbook or organizer-verified mapping files.")
    from run_stage2 import main as stage2; from run_stage3 import main as stage3
    stage2("official",workbook); stage3("official"); validate_all()

if __name__=="__main__":
    a=argparse.ArgumentParser(); a.add_argument("--mode",choices=["demo","official","validate"],required=True); a.add_argument("--mapping"); a.add_argument("--mapping-metadata"); a.add_argument("--workbook",default="bank_campaign_participant_release-1.xlsx")
    args=a.parse_args()
    try: main(args.mode,args.mapping,args.mapping_metadata,args.workbook)
    except MappingVerificationError as e: raise SystemExit(str(e))
