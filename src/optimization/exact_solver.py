from __future__ import annotations
from dataclasses import dataclass,asdict
from itertools import combinations
import math,time

@dataclass(frozen=True)
class Candidate:
    customer_id: str
    predicted_probability: float
    contact_cost: int
    expected_deposit_value: float
    capacity_units: int
    @property
    def expected_net_value(self): return self.predicted_probability*self.expected_deposit_value-self.contact_cost

@dataclass(frozen=True)
class Constraints:
    select_exactly: int=6
    budget: int=25
    capacity: int=22

def validate_candidates(candidates, expected_n=10):
    if len(candidates)!=expected_n: raise ValueError(f"Expected exactly {expected_n} candidates, got {len(candidates)}")
    ids=[c.customer_id for c in candidates]
    if any(not isinstance(i,str) or not i.strip() for i in ids) or len(set(ids))!=len(ids): raise ValueError("customer_id values must be non-empty and unique")
    for c in candidates:
        if not math.isfinite(c.predicted_probability) or not 0<=c.predicted_probability<=1: raise ValueError(f"Invalid probability for {c.customer_id}")
        if c.contact_cost<0 or int(c.contact_cost)!=c.contact_cost: raise ValueError(f"Invalid contact cost for {c.customer_id}")
        if c.capacity_units<0 or int(c.capacity_units)!=c.capacity_units: raise ValueError(f"Invalid capacity for {c.customer_id}")
        if not math.isfinite(c.expected_deposit_value) or c.expected_deposit_value<0: raise ValueError(f"Invalid deposit value for {c.customer_id}")

def selection_values(candidates,bits,constraints):
    chosen=[c for c,b in zip(candidates,bits) if b]
    cost=sum(c.contact_cost for c in chosen); cap=sum(c.capacity_units for c in chosen); value=sum(c.expected_net_value for c in chosen)
    feasible=len(chosen)==constraints.select_exactly and cost<=constraints.budget and cap<=constraints.capacity
    return {"selected_ids":[c.customer_id for c in chosen],"objective":float(value),"total_cost":int(cost),"total_capacity":int(cap),"selected_count":len(chosen),"feasible":bool(feasible)}

def exact_solve(candidates,constraints=Constraints()):
    validate_candidates(candidates,len(candidates)); t=time.perf_counter(); records=[]
    for idx in combinations(range(len(candidates)),constraints.select_exactly):
        bits=[int(i in idx) for i in range(len(candidates))]; records.append({"bits":bits,**selection_values(candidates,bits,constraints)})
    feasible=[r for r in records if r["feasible"]]
    # Objective descending, then lexicographically ascending sorted customer IDs.
    feasible.sort(key=lambda r:(-round(r["objective"],12),tuple(sorted(r["selected_ids"]))))
    return {"status":"optimal" if feasible else "infeasible","best":feasible[0] if feasible else None,
            "enumerated_combinations":len(records),"feasible_combinations":len(feasible),"runtime_seconds":time.perf_counter()-t,"records":records}
