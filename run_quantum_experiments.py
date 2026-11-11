from __future__ import annotations
import argparse,json,platform,sys
from pathlib import Path
import joblib,numpy as np,pandas as pd,pennylane as qml,torch
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from src.preprocessing import FEATURES,quantum_preprocessor
from src.quantum_experiments import run_experiments,equivalence_diagnostics
from src.pennylane_models import circuit_texts
from src.quantum_models import circuits,circuit_metadata

def main(mode="full"):
    cfg=json.loads(Path("configs/pennylane_experiments.json").read_text())
    if mode=="smoke":
        cfg["trainable_kernel"].update({"depths":[1],"learning_rates":[.03],"initialization_seeds":[42],"iterations":2,"alignment_sample_cap":24})
        cfg["data_reuploading"].update({"epochs":3,"patience":2,"initialization_seeds":[42]})
    for d in ["reports/quantum_circuits","reports/quantum_training_curves","artifacts/quantum_experiments"]: Path(d).mkdir(parents=True,exist_ok=True)
    tr=pd.read_excel("bank_campaign_participant_release-1.xlsx",sheet_name="Stage1_Train"); X=tr[FEATURES]; y=tr.y.map({"no":0,"yes":1}).to_numpy()
    # Equivalence uses an identical fold-fitted representation and a deterministic 20-row subset.
    Xt=quantum_preprocessor(4,42).fit_transform(X.iloc[:200],y[:200]); eq=equivalence_diagnostics(Xt[:20],y[:20],"results/kernel_equivalence_metrics.json")
    folds,oof,art=run_experiments(X,y,cfg); folds.to_csv("results/quantum_fold_metrics.csv",index=False)
    summaries=pd.DataFrame([{"model":k.replace("__summary",""),**v} for k,v in art.items() if k.endswith("__summary")])
    base=pd.read_csv("results/model_comparison.csv"); base=base.rename(columns={"train_seconds":"runtime_seconds"})
    cols=["model","pr_auc","roc_auc","precision_at_10","recall_at_10","brier","log_loss","runtime_seconds"]
    comp=pd.concat([base[cols],summaries[cols]],ignore_index=True); comp.to_csv("results/quantum_model_comparison.csv",index=False)
    joblib.dump({"config":cfg,"artifacts":art,"oof":oof},"artifacts/quantum_experiments/experiment_artifacts.joblib")
    for n,t in circuit_texts().items(): Path(f"reports/quantum_circuits/{n}.txt").write_text(t,encoding="utf-8")
    fm,ans=circuits(); Path("reports/quantum_circuits/qiskit_qsvc.txt").write_text(str(fm.draw(output="text")),encoding="utf-8")
    Path("reports/quantum_circuits/qiskit_vqc.txt").write_text(str(fm.compose(ans).draw(output="text")),encoding="utf-8")
    complexity={"qiskit":circuit_metadata(),"pennylane_qsvc":{"qubits":4,"depth":11,"gates":17,"counts":{"Hadamard":4,"PhaseShift":7,"CNOT":6},"trainable_parameters":0},
      "pennylane_trainable_d1":{"qubits":4,"depth":7,"gates":19,"counts":{"Hadamard":4,"RY":8,"RZ":4,"CNOT":3},"trainable_parameters":8},
      "pennylane_trainable_d2":{"qubits":4,"depth":13,"gates":34,"trainable_parameters":16},
      "pennylane_reuploading":{"qubits":4,"depth":12,"gates":24,"counts":{"RY":8,"Rot":8,"CNOT":8},"trainable_parameters":24}}
    Path("reports/quantum_circuits/complexity.json").write_text(json.dumps(complexity,indent=2),encoding="utf-8")
    for name,records in art.items():
        if name.endswith("__summary") or not records: continue
        fig,ax=plt.subplots()
        for i,r in enumerate(records):
            if "alignment" in r: ax.plot(range(1,len(r["alignment"])+1),r["alignment"],label=f"fold {i+1}")
            elif "history" in r: ax.plot([z["epoch"] for z in r["history"]],[z["validation_loss"] for z in r["history"]],label=f"fold {i+1}")
        ax.set(xlabel="Iteration / epoch",ylabel="Alignment / validation loss",title=name); ax.legend(); fig.tight_layout()
        safe="".join(c if c.isalnum() else "_" for c in name.lower()); fig.savefig(f"reports/quantum_training_curves/{safe}.png",dpi=140); plt.close(fig)
    Path("artifacts/quantum_experiments/environment.json").write_text(json.dumps({"python":sys.version,"platform":platform.platform(),"pennylane":qml.__version__,"torch":torch.__version__},indent=2),encoding="utf-8")
    print(comp.sort_values("pr_auc",ascending=False).to_string(index=False)); print("\nEquivalence",eq)
if __name__=="__main__":
    a=argparse.ArgumentParser(); a.add_argument("--mode",choices=["smoke","full"],default="full"); main(a.parse_args().mode)
