from __future__ import annotations
from .exact_solver import selection_values

def summarize_counts(counts,candidates,constraints,exact_best,n_decision):
    total=sum(counts.values()); feasible=[]; optimum=0
    exact_ids=tuple(sorted(exact_best["selected_ids"]))
    for z,n in counts.items():
        r=selection_values(candidates,z[:n_decision],constraints)
        if r["feasible"]:
            feasible.append((r,n))
            if tuple(sorted(r["selected_ids"]))==exact_ids: optimum+=n
    feasible.sort(key=lambda x:(-x[0]["objective"],tuple(sorted(x[0]["selected_ids"]))))
    best=feasible[0][0] if feasible else None; gap=None if best is None else exact_best["objective"]-best["objective"]
    return {"best_measured_feasible_objective":None if best is None else best["objective"],"best_selected_ids":None if best is None else best["selected_ids"],
      "absolute_optimality_gap":gap,"relative_optimality_gap":None if gap is None or abs(exact_best["objective"])<1e-12 else gap/abs(exact_best["objective"]),
      "feasible_shot_probability":sum(n for _,n in feasible)/total,"exact_optimum_sampling_probability":optimum/total,"sampled_feasible":bool(feasible)}
