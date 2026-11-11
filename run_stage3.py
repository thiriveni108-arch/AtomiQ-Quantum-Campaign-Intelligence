from __future__ import annotations
import argparse,json
from pathlib import Path
import pandas as pd
from src.simulation.stage3_pipeline import load_demo,load_official,OfficialStage3Blocked
from src.simulation.exact_probability import poisson_binomial
from src.simulation.quantum_sampler import build_subscription_circuit,ideal_statevector_distribution,run_shots
from src.simulation.quantum_sampler import run_noisy_shots
from src.simulation.classical_monte_carlo import run_classical_monte_carlo

def main(mode="demo"):
    records=load_demo() if mode=="demo" else load_official(); p=[r.predicted_probability for r in records]
    exact=poisson_binomial(p); ideal=ideal_statevector_distribution(p)
    if max(abs(exact["distribution"]-ideal["distribution"]))>1e-12: raise RuntimeError("Classical and ideal quantum distributions disagree")
    runs=[]; full_quantum_runs=[]; mc_runs=[]; full_mc_runs=[]; dist_rows=[]
    for i,shots in enumerate((1024,4096,16384)):
        r=run_shots(p,shots,seed=42+i); r["seed"]=42+i; r["exact_probability"]=exact["probability_at_least_3"]; r["absolute_error"]=abs(r["estimated_probability"]-r["exact_probability"])
        for k,(count,freq) in enumerate(zip(r["counts_by_subscriptions"],[x/shots for x in r["counts_by_subscriptions"]])):
            dist_rows.append({"shots":shots,"seed":42+i,"subscriptions":k,"count":count,"estimated_probability":freq,"exact_probability":float(exact["distribution"][k])})
        full_quantum_runs.append(r); runs.append({k:v for k,v in r.items() if k not in ("raw_counts","counts_by_subscriptions")})
        mc=run_classical_monte_carlo(p,shots,seed=42+i); mc["exact_probability"]=exact["probability_at_least_3"]; mc["absolute_error"]=abs(mc["estimated_probability"]-mc["exact_probability"])
        full_mc_runs.append(mc); mc_runs.append({k:v for k,v in mc.items() if k!="counts_by_subscriptions"})
    prefix="stage3_demo" if mode=="demo" else "stage3_official"; Path("results").mkdir(exist_ok=True); Path("reports").mkdir(exist_ok=True)
    pd.DataFrame(runs).to_csv(f"results/{prefix}_shot_comparison.csv",index=False); pd.DataFrame(dist_rows).to_csv(f"results/{prefix}_distribution.csv",index=False)
    pd.DataFrame(mc_runs).to_csv(f"results/{prefix}_monte_carlo_comparison.csv",index=False)
    noisy=run_noisy_shots(p); noisy["exact_probability"]=exact["probability_at_least_3"]; noisy["absolute_error"]=abs(noisy["estimated_probability"]-noisy["exact_probability"])
    pd.DataFrame([noisy]).drop(columns=["counts_by_subscriptions"]).to_csv(f"results/{prefix}_noise_comparison.csv",index=False)
    qc=build_subscription_circuit(p,True); fig=qc.draw(output="mpl",fold=-1); fig.savefig(f"reports/{prefix}_circuit.png",dpi=180,bbox_inches="tight")
    result={"mode":mode,"official":mode=="official","assumption":"independent Bernoulli subscription outcomes","customers":[r.__dict__ for r in records],
      "rotation_angles_radians":[float(x) for x in __import__('src.simulation.quantum_sampler',fromlist=['rotation_angles']).rotation_angles(p)],
      "exact_distribution":[float(x) for x in exact["distribution"]],"exact_probability_at_least_3":exact["probability_at_least_3"],
      "ideal_statevector_distribution":[float(x) for x in ideal["distribution"]],"ideal_probability_at_least_3":ideal["probability_at_least_3"],
      "maximum_classical_statevector_difference":float(max(abs(exact["distribution"]-ideal["distribution"]))),
      "circuit":{"qubits":qc.num_qubits,"depth":qc.depth(),"size":qc.size(),"gate_counts":dict(qc.count_ops())},
      "shot_runs":full_quantum_runs,"classical_monte_carlo_runs":full_mc_runs,"controlled_noise_run":noisy}
    Path(f"results/{prefix}_probability.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
    if mode=="official": Path("stage3_result.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
    print(json.dumps(result,indent=2))
if __name__=="__main__":
    a=argparse.ArgumentParser(); a.add_argument("--mode",choices=["demo","official"],default="demo")
    try: main(a.parse_args().mode)
    except OfficialStage3Blocked as e: raise SystemExit(str(e))
