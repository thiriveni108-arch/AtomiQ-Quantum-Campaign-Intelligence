from __future__ import annotations
import argparse,json
from pathlib import Path
import numpy as np,pandas as pd
from qiskit.quantum_info import Statevector
from src.optimization.exact_solver import Constraints,exact_solve,selection_values
from src.optimization.stage2_pipeline import load_demo,load_official,OfficialIntegrationBlocked
from src.optimization.qubo_formulation import build_slack_qubo
from src.optimization.qaoa_standard import run_standard_qaoa,build_standard_circuit
from src.optimization.qaoa_constrained import run_cardinality_qaoa,build_cardinality_circuit,verify_weight_preservation
from src.optimization.optimization_metrics import summarize_counts

def ideal_metrics(qc,candidates,constraints,exact,n_decision):
    sv=Statevector(qc.remove_final_measurements(inplace=False)); probs=sv.probabilities(); feasible=optimal=0.; target=tuple(sorted(exact["selected_ids"]))
    for i,p in enumerate(probs):
        if p<1e-14: continue
        bits=[(i>>q)&1 for q in range(n_decision)]; r=selection_values(candidates,bits,constraints)
        if r["feasible"]:
            feasible+=p
            if tuple(sorted(r["selected_ids"]))==target: optimal+=p
    return float(feasible),float(optimal)

def workbook_constraints(workbook):
    d=pd.read_excel(workbook,sheet_name="Stage2_Constraints")
    vals={str(r.symbol):r.value for _,r in d.iterrows()}
    return Constraints(int(vals["K"]),int(vals["C"]),int(vals["H"]))

def main(mode="demo",workbook="bank_campaign_participant_release-1.xlsx"):
    if mode=="official":
        candidates=load_official(workbook=workbook); cfg=json.loads(Path("configs/stage2_experiments.json").read_text())
    else: candidates,cfg=load_demo()
    if mode=="official": constraints=workbook_constraints(workbook)
    else:
        c=cfg["constraints"]; constraints=Constraints(c["select_exactly"],c["budget"],c["capacity"])
    exact=exact_solve(candidates,constraints); qubo=build_slack_qubo(candidates,constraints); rows=[]; circuits={}
    if exact["best"] is None: raise RuntimeError("Synthetic demo unexpectedly has no feasible solution")
    rows.append({"solver":"Exact enumeration","depth":0,"seed":cfg["seed_values"][0],"exact_objective":exact["best"]["objective"],
      "best_measured_feasible_objective":exact["best"]["objective"],"absolute_optimality_gap":0.,"relative_optimality_gap":0.,"feasible_shot_probability":1.,"exact_optimum_sampling_probability":1.,
      "circuit_depth":0,"gate_counts":"{}","total_qubits":0,"circuit_evaluations":0,"optimizer_iterations":0,"runtime_seconds":exact["runtime_seconds"]})
    for solver in ("standard","cardinality"):
      for p in cfg["depth_values"]:
       for seed in cfg["seed_values"]:
        if solver=="standard": counts,qc,meta=run_standard_qaoa(qubo,candidates,constraints,p,seed,cfg["optimization_shots"],cfg["optimizer_maxiter"]); nq=qubo.n_qubits
        else: counts,qc,meta=run_cardinality_qaoa(candidates,constraints,p,seed,cfg["optimization_shots"],cfg["optimizer_maxiter"],qubo.penalty); nq=len(candidates)
        sm=summarize_counts(counts,candidates,constraints,exact["best"],len(candidates))
        # A 20-qubit exact post-pass dominated the bounded demo runtime. Ideal
        # probabilities are computed for the 10-qubit cardinality formulation;
        # the standard slack formulation is reported from real finite shots only.
        if solver=="cardinality": ideal_f,ideal_o=ideal_metrics(qc,candidates,constraints,exact["best"],len(candidates))
        else: ideal_f,ideal_o=float("nan"),float("nan")
        name=f"{solver}_p{p}_seed{seed}"; circuits[name]=qc
        selected_set=set(sm.get("best_selected_ids") or []); decision_bitstring="".join("1" if c.customer_id in selected_set else "0" for c in candidates)
        rows.append({"solver":"Standard QAOA" if solver=="standard" else "Cardinality QAOA","depth":p,"seed":seed,"exact_objective":exact["best"]["objective"],**sm,
          "best_decision_bitstring":decision_bitstring,
          "ideal_feasible_probability":ideal_f,"ideal_exact_optimum_probability":ideal_o,"circuit_depth":qc.depth(),"gate_counts":json.dumps(dict(qc.count_ops())),"total_qubits":nq,**meta})
    prefix="stage2_demo" if mode=="demo" else "stage2_official"; Path("results").mkdir(exist_ok=True); Path("reports/stage2_circuits").mkdir(parents=True,exist_ok=True)
    out=pd.DataFrame(rows); out.to_csv(f"results/{prefix}_experiments.csv",index=False)
    summary=out.groupby("solver",as_index=False).agg(best_objective=("best_measured_feasible_objective","max"),mean_feasible_probability=("feasible_shot_probability","mean"),mean_optimum_probability=("exact_optimum_sampling_probability","mean"),mean_runtime_seconds=("runtime_seconds","mean"))
    summary.to_csv(f"results/{prefix}_solver_comparison.csv",index=False)
    for n,qc in circuits.items(): Path(f"reports/stage2_circuits/{n}.txt").write_text(str(qc.draw(output="text",fold=140)),encoding="utf-8")
    complexity={n:{"qubits":q.num_qubits,"depth":q.depth(),"size":q.size(),"gate_counts":dict(q.count_ops())} for n,q in circuits.items()}
    complexity["formulation"]={"decision_qubits":10,"cost_slack_qubits":len(qubo.cost_slack_weights),"capacity_slack_qubits":len(qubo.capacity_slack_weights),"standard_total_qubits":qubo.n_qubits,
      "cost_slack_weights":qubo.cost_slack_weights,"capacity_slack_weights":qubo.capacity_slack_weights,"penalty":qubo.penalty,"cardinality_bad_weight_probability":verify_weight_preservation(candidates,constraints)}
    Path("reports/stage2_circuit_complexity.json").write_text(json.dumps(complexity,indent=2),encoding="utf-8")
    quantum_rows=out[out.solver!="Exact enumeration"].to_dict("records"); feasible_quantum=[r for r in quantum_rows if r.get("sampled_feasible")]
    best_quantum=max(feasible_quantum,key=lambda r:r["best_measured_feasible_objective"]) if feasible_quantum else None
    selected=set(exact["best"]["selected_ids"]); artifact={"mode":mode,"official":mode=="official","top_10_inputs":[c.__dict__ for c in candidates],
      "selected_customers":[{"customer_id":c.customer_id,"predicted_probability":c.predicted_probability} for c in candidates if c.customer_id in selected],
      "exact":{k:v for k,v in exact.items() if k!="records"},"best_quantum_result":best_quantum,"quantum_experiments":quantum_rows,
      "qubo":{"penalty":qubo.penalty,"n_qubits":qubo.n_qubits,"cost_slack_weights":qubo.cost_slack_weights,"capacity_slack_weights":qubo.capacity_slack_weights}}
    Path(f"results/{prefix}_exact_solution.json").write_text(json.dumps(artifact,indent=2),encoding="utf-8")
    if mode=="official":
        Path("results/stage2_official_selection.json").write_text(json.dumps(artifact,indent=2),encoding="utf-8")
        Path("stage2_result.json").write_text(json.dumps(artifact,indent=2),encoding="utf-8")
    print(out.to_string(index=False)); print("\nExact optimum",exact["best"])
if __name__=="__main__":
    a=argparse.ArgumentParser(); a.add_argument("--mode",choices=["demo","official"],default="demo")
    try: main(a.parse_args().mode)
    except OfficialIntegrationBlocked as e: raise SystemExit(str(e))
