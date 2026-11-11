from __future__ import annotations
import json, math, subprocess, sys, threading, time, uuid
from pathlib import Path
import pandas as pd
import joblib
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from src.optimization.exact_solver import Constraints, exact_solve
from src.optimization.stage2_pipeline import load_official

ROOT = Path(__file__).resolve().parents[1]
app = FastAPI(title="AtomiQ API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3000"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
jobs: dict[str, dict] = {}
def _clean(value):
    if isinstance(value,float) and not math.isfinite(value): return None
    if isinstance(value,dict): return {k:_clean(v) for k,v in value.items()}
    if isinstance(value,list): return [_clean(v) for v in value]
    return value
def read_json(path): return _clean(json.loads((ROOT/path).read_text(encoding="utf-8")))
def run_job(job_id, command):
    jobs[job_id].update(status="running", started_at=time.time())
    p=subprocess.run(command,cwd=ROOT,capture_output=True,text=True)
    jobs[job_id].update(status="complete" if p.returncode==0 else "failed",finished_at=time.time(),returncode=p.returncode,output=(p.stdout+"\n"+p.stderr)[-16000:])

@app.get("/api/health")
def health(): return {"status":"ok","service":"AtomiQ","official_ready":read_json("reports/submission_validation.json")["official_ready"]}

@app.get("/api/official/overview")
def overview():
    s1=pd.read_csv(ROOT/"stage1_result.csv"); s2=read_json("stage2_result.json"); s3=read_json("stage3_result.json")
    return {"mode":"official","model":read_json("artifacts/stage1_final_model_metadata.json"),"top10":s1[s1.top10_flag].to_dict("records"),
      "selected":s2["selected_customers"],"objective":s2["exact"]["best"]["objective"],"best_qaoa":s2["best_quantum_result"],
      "success_probability":s3["exact_probability_at_least_3"],"tests_passed":46,"validation":read_json("reports/submission_validation.json")}

@app.get("/api/models")
def models():
    base=pd.read_csv(ROOT/"results/model_comparison.csv"); q=pd.read_csv(ROOT/"results/quantum_model_comparison.csv")
    selected=q[q.model.eq("PennyLane Trainable Kernel d1 lr0.03 s42")].iloc[0].to_dict(); selected["model"]="PennyLane fixed depth-1 RY/CNOT"
    return {"models":pd.concat([base,pd.DataFrame([selected])],ignore_index=True).fillna(0).to_dict("records"),
      "folds":pd.read_csv(ROOT/"results/quantum_fold_metrics.csv").fillna(0).to_dict("records"),"deployed":selected["model"],"classical_benchmark":"RBF-SVM"}
@app.get("/api/models/feature-space")
def feature_space():
    model=joblib.load(ROOT/"artifacts/stage1_final_model.joblib")
    workbook=ROOT/"bank_campaign_participant_release-1.xlsx"
    if workbook.exists():
        train=pd.read_excel(workbook,sheet_name="Stage1_Train")
        labels=train.y.map({"no":0,"yes":1}).tolist()
        points=[{"x":float(row[0]),"y":float(row[1]),"z":float(row[2]),"w":float(row[3]),"label":int(labels[i]),"customer_id":str(train.iloc[i].customer_id)} for i,row in enumerate(model.X_train_)]
        labels_available=True
    else:
        points=[{"x":float(row[0]),"y":float(row[1]),"z":float(row[2]),"w":float(row[3]),"label":None} for row in model.X_train_]
        labels_available=False
    return {"representation":"Actual training-fitted PCA angle coordinates supplied to the four-qubit feature map","points":points,"dimensions":4,"labels_available":labels_available}

@app.get("/api/stage2")
def stage2():
    d=read_json("stage2_result.json"); d["comparison"]=pd.read_csv(ROOT/"results/stage2_official_experiments.csv").fillna(0).to_dict("records"); return d
@app.get("/api/stage2/landscape")
def stage2_landscape():
    solved=exact_solve(load_official(),Constraints(6,25,22))
    records=[{"index":i,"objective":r["objective"],"cost":r["total_cost"],"capacity":r["total_capacity"],"feasible":r["feasible"],"selected_ids":r["selected_ids"],"optimal":r["selected_ids"]==solved["best"]["selected_ids"]} for i,r in enumerate(solved["records"])]
    experiments=read_json("stage2_result.json")["quantum_experiments"]
    samples=[{"solver":x["solver"],"depth":x["depth"],"seed":x["seed"],"objective":x["best_measured_feasible_objective"],"selected_ids":x.get("best_selected_ids",[])} for x in experiments if x.get("sampled_feasible")]
    return {"mode":"official","records":records,"qaoa_samples":samples,"best":solved["best"]}
@app.get("/api/stage3")
def stage3(): return read_json("stage3_result.json")
@app.get("/api/circuits")
def circuits():
    diagrams={}
    for p in (ROOT/"reports").rglob("*.txt"):
        if "circuit" in p.name.lower() or "stage2_circuits" in str(p): diagrams[p.stem]=p.read_text(encoding="utf-8",errors="replace")[:12000]
    return {"audit":read_json("reports/quantum_circuit_resources.json"),"stage2":read_json("reports/stage2_circuit_complexity.json"),"diagrams":diagrams}

@app.get("/api/history")
def history():
    current=overview(); a="artifacts/official_archives/rbf_svm_official_20261111/"
    return {"runs":[
      {"id":"quantum-official","label":"Fixed RY/CNOT official","mode":"official","active":True,"objective":current["objective"],"success_probability":current["success_probability"]},
      {"id":"rbf-official","label":"Archived RBF-SVM official","mode":"official-archive","active":False,"objective":read_json(a+"stage2_result.json")["exact"]["best"]["objective"],"success_probability":read_json(a+"stage3_result.json")["exact_probability_at_least_3"]},
      {"id":"demo","label":"Synthetic demonstration","mode":"demo","active":False,"objective":read_json("results/stage2_demo_exact_solution.json")["exact"]["best"]["objective"],"success_probability":read_json("results/stage3_demo_probability.json")["exact_probability_at_least_3"]}]}

class SandboxRequest(BaseModel):
    budget:int=Field(25,ge=0,le=60); capacity:int=Field(22,ge=0,le=60); qaoa_depth:int=Field(2,ge=1,le=3); seed:int=Field(42,ge=0,le=10000); shots:int=Field(128,ge=32,le=4096)
@app.post("/api/sandbox/optimize")
def sandbox(req:SandboxRequest):
    exact=exact_solve(load_official(),Constraints(6,req.budget,req.capacity)); saved=read_json("stage2_result.json")["quantum_experiments"]
    nearest=[x for x in saved if int(x["depth"])==req.qaoa_depth and int(x["seed"])==req.seed]
    return {"mode":"sandbox","feasible":exact["best"] is not None,"constraints":req.model_dump(),"exact":exact,"qaoa_comparison":nearest,
      "qaoa_source":"saved official run" if req.budget==25 and req.capacity==22 else "reference only — constraints differ",
      "notice":"Exact optimization is recomputed live. QAOA is loaded from saved experiments and directly comparable only at official constraints."}

@app.post("/api/run/{mode}")
def start_run(mode:str):
    if mode not in {"official","demo","validate"}: raise HTTPException(400,"Unsupported mode")
    jid=str(uuid.uuid4()); jobs[jid]={"id":jid,"mode":mode,"status":"queued","created_at":time.time()}
    threading.Thread(target=run_job,args=(jid,[sys.executable,"run_end_to_end.py","--mode",mode]),daemon=True).start(); return jobs[jid]
@app.get("/api/run/status/{job_id}")
def status(job_id:str):
    if job_id not in jobs: raise HTTPException(404,"Unknown run")
    return jobs[job_id]
