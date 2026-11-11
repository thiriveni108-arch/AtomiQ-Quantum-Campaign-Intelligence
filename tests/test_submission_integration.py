import json
from pathlib import Path
import numpy as np,pandas as pd,pytest
from src.integration import validate_verified_mapping,build_official_stage1,MappingVerificationError,validate_stage1_outputs
from src.simulation.classical_monte_carlo import run_classical_monte_carlo
from src.simulation.stage3_pipeline import load_demo
from run_end_to_end import validate_all

def make_mapping(tmp_path,verified=True):
    p="bank_campaign_participant_release.xlsx"; tr=pd.read_excel(p,sheet_name="Stage1_Train"); s2=pd.read_excel(p,sheet_name="Stage2_Data")
    ids=sorted(set(s2.customer_id)-set(tr.customer_id)); csv=tmp_path/"map.csv"; pd.DataFrame({"test_row_index":range(100),"customer_id":ids}).to_csv(csv,index=False)
    meta=tmp_path/"meta.json"; meta.write_text(json.dumps({"organizer_verified":verified,"verification_source":"unit-test fixture"}))
    return csv,meta

def test_verified_mapping_integrity_and_schema(tmp_path):
    csv,meta=make_mapping(tmp_path); m,_=validate_verified_mapping(csv,meta); assert len(m)==100 and m.customer_id.is_unique
    out=tmp_path/"official.csv"; result,_=build_official_stage1(csv,meta,out=out); assert list(result.columns)==["customer_id","predicted_probability","rank","top_10"] and result.top_10.sum()==10
def test_mapping_requires_explicit_verification(tmp_path):
    csv,meta=make_mapping(tmp_path,False)
    with pytest.raises(MappingVerificationError): validate_verified_mapping(csv,meta)
def test_duplicate_mapping_rejected(tmp_path):
    csv,meta=make_mapping(tmp_path); d=pd.read_csv(csv); d.loc[1,"customer_id"]=d.loc[0,"customer_id"]; d.to_csv(csv,index=False)
    with pytest.raises(MappingVerificationError): validate_verified_mapping(csv,meta)
def test_stage1_output_and_propagation():
    assert validate_stage1_outputs()==[]
    s2=json.loads(Path("results/stage2_demo_exact_solution.json").read_text()); assert [r.customer_id for r in load_demo()]==s2["exact"]["best"]["selected_ids"]
def test_monte_carlo_fair_coins_reproducible():
    a=run_classical_monte_carlo([.5]*6,50000,42); b=run_classical_monte_carlo([.5]*6,50000,42)
    assert a["estimated_probability"]==b["estimated_probability"] and abs(a["estimated_probability"]-42/64)<.01
def test_submission_validation_passes(): validate_all()
