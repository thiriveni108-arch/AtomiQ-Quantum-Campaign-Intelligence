from __future__ import annotations
import time
import numpy as np
from scipy.optimize import minimize
from qiskit import QuantumCircuit,transpile
from qiskit.circuit.library import DiagonalGate
from qiskit_aer import AerSimulator
from .qubo_formulation import direct_penalized_energy
from .qaoa_standard import decode_counts

def build_cardinality_circuit(candidates,constraints,p,params,penalty,measure=True):
    n=len(candidates); qc=QuantumCircuit(n,n if measure else 0)
    for q in range(constraints.select_exactly): qc.x(q)
    energies=np.array([direct_penalized_energy(candidates,[(z>>i)&1 for i in range(n)],constraints,penalty) for z in range(1<<n)])
    for layer in range(p):
        qc.append(DiagonalGate(np.exp(-1j*params[layer]*energies)),range(n)); beta=params[p+layer]
        for parity in (0,1):
            for i in range(parity,n-1,2): qc.rxx(2*beta,i,i+1); qc.ryy(2*beta,i,i+1)
        qc.rxx(2*beta,n-1,0); qc.ryy(2*beta,n-1,0)
    if measure: qc.measure(range(n),range(n))
    return qc,energies

def run_cardinality_qaoa(candidates,constraints,p=1,seed=42,shots=256,maxiter=10,penalty=None):
    penalty=float(sum(abs(c.expected_net_value) for c in candidates)+1 if penalty is None else penalty)
    backend=AerSimulator(seed_simulator=seed); evaluations=0
    def sample(params,s=shots):
        raw,_=build_cardinality_circuit(candidates,constraints,p,params,penalty); qc=transpile(raw,backend,optimization_level=1,seed_transpiler=seed)
        return decode_counts(backend.run(qc,shots=s).result().get_counts(),len(candidates)),qc
    def objective(params):
        nonlocal evaluations; evaluations+=1; counts,_=sample(params)
        return sum(direct_penalized_energy(candidates,z,constraints,penalty)*num for z,num in counts.items())/shots
    rng=np.random.default_rng(seed); t=time.perf_counter(); opt=minimize(objective,rng.uniform(0,np.pi,2*p),method="COBYLA",options={"maxiter":maxiter,"rhobeg":.5})
    counts,qc=sample(opt.x,shots*4); return counts,qc,{"parameters":opt.x.tolist(),"optimizer_iterations":int(opt.nfev),"circuit_evaluations":evaluations+1,"runtime_seconds":time.perf_counter()-t,"shots":shots*4,"penalty":penalty}

def verify_weight_preservation(candidates,constraints,beta=.37):
    qc,_=build_cardinality_circuit(candidates,constraints,1,[0.,beta],1.,measure=False); from qiskit.quantum_info import Statevector
    sv=Statevector(qc); bad=sum(abs(a)**2 for i,a in enumerate(sv.data) if i.bit_count()!=constraints.select_exactly)
    return float(bad)
