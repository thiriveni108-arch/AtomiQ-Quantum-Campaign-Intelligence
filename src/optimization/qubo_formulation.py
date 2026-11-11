from __future__ import annotations
from dataclasses import dataclass
import numpy as np
from .exact_solver import Constraints,selection_values

def bounded_binary_weights(limit):
    weights=[]; total=0; p=1
    while total+p<=limit:
        weights.append(p); total+=p; p*=2
    if total<limit: weights.append(limit-total)
    return weights

@dataclass
class QUBO:
    linear: np.ndarray
    quadratic: dict
    constant: float
    n_decision: int
    cost_slack_weights: list
    capacity_slack_weights: list
    penalty: float
    def energy(self,z):
        z=np.asarray(z,int); return float(self.constant+self.linear@z+sum(q*z[i]*z[j] for (i,j),q in self.quadratic.items()))
    @property
    def n_qubits(self): return len(self.linear)

def add_square(linear,quadratic,constant,indices,weights,target,penalty):
    constant+=penalty*target*target
    for i,w in zip(indices,weights): linear[i]+=penalty*(w*w-2*target*w)
    for a in range(len(indices)):
        for b in range(a+1,len(indices)):
            key=(indices[a],indices[b]); quadratic[key]=quadratic.get(key,0)+2*penalty*weights[a]*weights[b]
    return constant

def build_slack_qubo(candidates,constraints=Constraints(),penalty=None):
    values=np.array([c.expected_net_value for c in candidates]); costs=[c.contact_cost for c in candidates]; caps=[c.capacity_units for c in candidates]
    penalty=float(sum(abs(values))+1 if penalty is None else penalty)
    cw=bounded_binary_weights(constraints.budget); hw=bounded_binary_weights(constraints.capacity)
    n=len(candidates)+len(cw)+len(hw); linear=np.zeros(n); linear[:len(candidates)]=-values; quadratic={}; constant=0.
    decision=list(range(len(candidates))); ci=list(range(len(candidates),len(candidates)+len(cw))); hi=list(range(len(candidates)+len(cw),n))
    constant=add_square(linear,quadratic,constant,decision,[1]*len(candidates),constraints.select_exactly,penalty)
    constant=add_square(linear,quadratic,constant,decision+ci,costs+cw,constraints.budget,penalty)
    constant=add_square(linear,quadratic,constant,decision+hi,caps+hw,constraints.capacity,penalty)
    return QUBO(linear,quadratic,constant,len(candidates),cw,hw,penalty)

def encode_with_slack(candidates,bits,constraints,qubo):
    cost=sum(c.contact_cost*b for c,b in zip(candidates,bits)); cap=sum(c.capacity_units*b for c,b in zip(candidates,bits))
    def encode(value,weights):
        # exhaustive tiny register guarantees an exact bounded representation when one exists
        for z in range(1<<len(weights)):
            b=[(z>>i)&1 for i in range(len(weights))]
            if sum(w*x for w,x in zip(weights,b))==value: return b
        return [0]*len(weights)
    return list(bits)+encode(max(0,constraints.budget-cost),qubo.cost_slack_weights)+encode(max(0,constraints.capacity-cap),qubo.capacity_slack_weights)

def direct_penalized_energy(candidates,bits,constraints,penalty):
    r=selection_values(candidates,bits,constraints)
    return -r["objective"]+penalty*(r["selected_count"]-constraints.select_exactly)**2+penalty*max(0,r["total_cost"]-constraints.budget)**2+penalty*max(0,r["total_capacity"]-constraints.capacity)**2
