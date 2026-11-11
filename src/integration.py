from __future__ import annotations
import json
from pathlib import Path
import pandas as pd
import joblib
from .preprocessing import FEATURES
from .pennylane_models import FixedRYCNOTKernelClassifier

class MappingVerificationError(RuntimeError): pass

def validate_verified_mapping(mapping_csv, metadata_json, workbook="bank_campaign_participant_release.xlsx"):
    mp=Path(mapping_csv); meta_path=Path(metadata_json)
    if not mp.exists() or not meta_path.exists():
        raise MappingVerificationError("Verified mapping unavailable. Supply a 100-row CSV plus organizer-verification metadata JSON.")
    meta=json.loads(meta_path.read_text(encoding="utf-8"))
    if meta.get("organizer_verified") is not True or not str(meta.get("verification_source","")).strip():
        raise MappingVerificationError("Mapping metadata must set organizer_verified=true and identify verification_source.")
    m=pd.read_csv(mp)
    if list(m.columns)!=["test_row_index","customer_id"]: raise MappingVerificationError("Mapping CSV columns must be exactly test_row_index,customer_id.")
    if len(m)!=100 or m.test_row_index.duplicated().any() or m.customer_id.duplicated().any(): raise MappingVerificationError("Mapping must contain 100 unique row indices and customer IDs.")
    if set(m.test_row_index)!=set(range(100)): raise MappingVerificationError("Mapping indices must be exactly 0..99.")
    tr=pd.read_excel(workbook,sheet_name="Stage1_Train"); s2=pd.read_excel(workbook,sheet_name="Stage2_Data")
    expected=set(s2.customer_id)-set(tr.customer_id)
    if set(m.customer_id)!=expected: raise MappingVerificationError("Mapped IDs do not exactly equal Stage2_Data IDs absent from Stage1_Train.")
    return m.sort_values("test_row_index"),meta

def build_official_stage1(mapping_csv,metadata_json,provisional="results/stage1_predictions_provisional.csv",out="results/stage1_predictions_official.csv"):
    m,meta=validate_verified_mapping(mapping_csv,metadata_json); p=pd.read_csv(provisional)
    if len(p)!=100 or set(p.test_row_index)!=set(range(100)): raise MappingVerificationError("Provisional predictions do not cover test rows 0..99 exactly once.")
    x=p[["test_row_index","predicted_probability"]].merge(m,on="test_row_index",validate="one_to_one")
    x=x.sort_values(["predicted_probability","customer_id"],ascending=[False,True],kind="stable").reset_index(drop=True)
    x.insert(0,"rank",range(1,101)); x["top_10"]=x["rank"]<=10
    result=x[["customer_id","predicted_probability","rank","top_10"]]
    Path(out).parent.mkdir(parents=True,exist_ok=True); result.to_csv(out,index=False)
    return result,meta

def verify_updated_workbook(updated="bank_campaign_participant_release-1.xlsx",original="bank_campaign_participant_release.xlsx"):
    if not Path(updated).exists(): raise MappingVerificationError(f"Updated workbook not found: {updated}")
    old=pd.ExcelFile(original); new=pd.ExcelFile(updated)
    if old.sheet_names!=new.sheet_names: raise MappingVerificationError("Workbook sheet names changed unexpectedly")
    for sheet in ("README","Stage1_Train","Stage2_Data","Stage2_Constraints"):
        a=pd.read_excel(original,sheet_name=sheet,header=None if sheet=="README" else 0)
        b=pd.read_excel(updated,sheet_name=sheet,header=None if sheet=="README" else 0)
        if not a.equals(b): raise MappingVerificationError(f"Updated workbook changed protected sheet {sheet}")
    old_test=pd.read_excel(original,sheet_name="Stage1_Test"); new_test=pd.read_excel(updated,sheet_name="Stage1_Test")
    if "customer_id" not in new_test: raise MappingVerificationError("Updated Stage1_Test still lacks customer_id")
    if not old_test.equals(new_test.drop(columns="customer_id")): raise MappingVerificationError("Updated Stage1_Test features or row order changed")
    tr=pd.read_excel(updated,sheet_name="Stage1_Train"); s2=pd.read_excel(updated,sheet_name="Stage2_Data"); ids=new_test.customer_id
    if len(ids)!=100 or ids.isna().any() or ids.duplicated().any(): raise MappingVerificationError("Updated test IDs must be 100 unique, non-null values")
    if not ids.isin(s2.customer_id).all() or ids.isin(tr.customer_id).any(): raise MappingVerificationError("Updated test IDs fail cross-sheet membership/disjointness")
    if set(ids)!=(set(s2.customer_id)-set(tr.customer_id)): raise MappingVerificationError("Updated test IDs are not exactly the non-training Stage2 IDs")
    return {"updated":updated,"original":original,"test_rows":100,"mapping_resolved":True,"features_unchanged":True,"training_unchanged":True,"stage2_unchanged":True}

def build_official_stage1_from_workbook(updated="bank_campaign_participant_release-1.xlsx",original="bank_campaign_participant_release.xlsx",
        model_path="artifacts/stage1_final_model.joblib",out="results/stage1_predictions_official.csv"):
    verification=verify_updated_workbook(updated,original); test=pd.read_excel(updated,sheet_name="Stage1_Test")
    model=joblib.load(model_path); probabilities=model.predict_proba(test[FEATURES])[:,1]
    result=pd.DataFrame({"customer_id":test.customer_id.astype(str),"predicted_probability":probabilities})
    result=result.sort_values(["predicted_probability","customer_id"],ascending=[False,True],kind="stable").reset_index(drop=True)
    result["rank"]=range(1,101); result["top10_flag"]=result["rank"]<=10
    Path(out).parent.mkdir(parents=True,exist_ok=True); result.to_csv(out,index=False); result.to_csv("stage1_result.csv",index=False)
    return result,verification

def train_official_fixed_quantum_model(updated="bank_campaign_participant_release-1.xlsx", original="bank_campaign_participant_release.xlsx",
        model_path="artifacts/stage1_final_model.joblib"):
    """Fit the preselected fixed depth-1 PennyLane model on all official labels."""
    verification = verify_updated_workbook(updated, original)
    train = pd.read_excel(updated, sheet_name="Stage1_Train")
    y = train.y.map({"no": 0, "yes": 1})
    if y.isna().any(): raise ValueError("Stage1_Train contains an unsupported target label")
    model = FixedRYCNOTKernelClassifier(seed=42, C=1.0).fit(train[FEATURES], y.to_numpy())
    Path(model_path).parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, model_path)
    Path("artifacts/stage1_final_model_metadata.json").write_text(json.dumps(model.model_metadata_, indent=2), encoding="utf-8")
    return model, verification

def validate_stage1_outputs(path="results/stage1_predictions_provisional.csv"):
    p=pd.read_csv(path); errors=[]
    if len(p)!=100: errors.append("Stage 1 must contain 100 predictions")
    if p.predicted_probability.isna().any() or not p.predicted_probability.between(0,1).all(): errors.append("Stage 1 probabilities must lie in [0,1]")
    if int(p.top_10.sum())!=10: errors.append("Stage 1 must flag exactly 10 candidates")
    if "test_row_index" in p and (p.test_row_index.duplicated().any() or set(p.test_row_index)!=set(range(100))): errors.append("test_row_index must uniquely cover 0..99")
    ranked=p.sort_values(["predicted_probability",("customer_id" if "customer_id" in p else "test_row_index")],ascending=[False,True],kind="stable")
    if ranked.iloc[:10].index.tolist()!=p[p.top_10].index.tolist(): errors.append("top_10 flags are inconsistent with deterministic ranking")
    return errors
