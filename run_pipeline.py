from __future__ import annotations
import argparse, json, platform, sys
from pathlib import Path
import joblib, numpy as np, pandas as pd, sklearn, qiskit, qiskit_machine_learning
from src.data_audit import audit_workbook
from src.classical_models import models, SEARCH_PROTOCOL
from src.evaluation import evaluate_classical, evaluate_quantum, make_plots
from src.preprocessing import FEATURES
from src.predict import save_predictions
from src.quantum_models import circuit_metadata, circuits

DATA="bank_campaign_participant_release-1.xlsx"
def main(mode="full"):
    for d in ("reports","results","artifacts","reports/figures"): Path(d).mkdir(parents=True,exist_ok=True)
    audit_workbook(DATA)
    tr=pd.read_excel(DATA,sheet_name="Stage1_Train"); te=pd.read_excel(DATA,sheet_name="Stage1_Test")
    X=tr[FEATURES].copy(); y=tr.y.map({"no":0,"yes":1}).to_numpy()
    classical=models(42); crows,coof=evaluate_classical(X,y,classical)
    maxiter=8 if mode=="smoke" else 30
    qrows,qoof,losses=evaluate_quantum(X,y,maxiter=maxiter)
    rows=crows+qrows; comp=pd.DataFrame(rows).sort_values(["brier","log_loss","pr_auc"],ascending=[True,True,False])
    comp.to_csv("results/model_comparison.csv",index=False); make_plots(y,{**coof,**qoof})
    # Selection prioritizes probability quality, then ranking. Quantum models remain eligible.
    eligible=comp[np.isfinite(comp.brier)&np.isfinite(comp.pr_auc)].copy()
    eligible["selection_score"]=eligible.brier + .1*eligible.log_loss - .1*eligible.pr_auc - .05*eligible.precision_at_10
    winner=eligible.sort_values("selection_score").iloc[0].model
    # Final deployable models use the strongest classical option if a quantum model wins; Q models are stored separately below.
    if winner in classical: final=classical[winner].fit(X,y); deployed=winner
    else:
        deployed="LogisticRegression"; final=classical[deployed].fit(X,y)
    preds=save_predictions(final,te[FEATURES])
    meta={"selected_by_validation":winner,"deployed_model":deployed,"quantum_deployment_fallback":winner not in classical,
          "selection_rule":"minimize brier + 0.1 log_loss - 0.1 PR-AUC - 0.05 Precision@10",
          "search_protocol":SEARCH_PROTOCOL,"mode":mode,"seed":42,"test_ids_available":False,
          "versions":{"python":sys.version,"platform":platform.platform(),"pandas":pd.__version__,"sklearn":sklearn.__version__,"qiskit":qiskit.__version__,"qiskit_ml":qiskit_machine_learning.__version__},
          "circuits":circuit_metadata(),"vqc_loss_history":losses}
    Path("reports/runtime_circuit_complexity.json").write_text(json.dumps(meta,indent=2),encoding="utf-8")
    fm,ans=circuits(); Path("reports/feature_map_circuit.txt").write_text(str(fm.draw(output="text")),encoding="utf-8"); Path("reports/vqc_ansatz_circuit.txt").write_text(str(ans.draw(output="text")),encoding="utf-8")
    Path("artifacts/vqc_training_metadata.json").write_text(json.dumps({"loss_history":losses.get("VQC",[]),"maxiter":maxiter,"seed":42},indent=2),encoding="utf-8")
    print(comp.to_string(index=False)); print(f"\nValidated winner: {winner}; deployed: {deployed}; predictions: {len(preds)}")
if __name__=="__main__":
    ap=argparse.ArgumentParser(); ap.add_argument("--mode",choices=["smoke","full"],default="full"); main(ap.parse_args().mode)
