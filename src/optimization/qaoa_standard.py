from __future__ import annotations
import time
import numpy as np
from scipy.optimize import minimize
from qiskit import QuantumCircuit,transpile
from qiskit_aer import AerSimulator

def apply_qubo_cost(qc,qubo,gamma):
    for i,l in enumerate(qubo.linear):
        if l: qc.rz(-gamma*l,i)
    for (i,j),q in qubo.quadratic.items():
        if q:
            qc.rz(-gamma*q/2,i); qc.rz(-gamma*q/2,j); qc.rzz(gamma*q/2,i,j)

def build_standard_circuit(qubo,p,params,measure=True):
    qc=QuantumCircuit(qubo.n_qubits,qubo.n_qubits if measure else 0); qc.h(range(qubo.n_qubits))
    for layer in range(p):
        apply_qubo_cost(qc,qubo,params[layer]); beta=params[p+layer]
        for q in range(qubo.n_qubits): qc.rx(2*beta,q)
    if measure: qc.measure(range(qubo.n_qubits),range(qubo.n_qubits))
    return qc

def decode_counts(counts,n):
    out={}
    for s,count in counts.items(): out[tuple(map(int,s.replace(' ','')[::-1][:n]))]=out.get(tuple(map(int,s.replace(' ','')[::-1][:n])),0)+count
    return out

def run_standard_qaoa(qubo,candidates,constraints,p=1,seed=42,shots=256,maxiter=10):
    backend=AerSimulator(method="statevector",seed_simulator=seed); evaluations=0
    def sample(params,eval_shots=shots):
        qc=transpile(build_standard_circuit(qubo,p,params),backend,optimization_level=1,seed_transpiler=seed)
        return decode_counts(backend.run(qc,shots=eval_shots).result().get_counts(),qubo.n_qubits),qc
    def objective(params):
        nonlocal evaluations; evaluations+=1; counts,_=sample(params)
        return sum(qubo.energy(z)*n for z,n in counts.items())/shots
    rng=np.random.default_rng(seed); x0=rng.uniform(0,np.pi,2*p); t=time.perf_counter()
    opt=minimize(objective,x0,method="COBYLA",options={"maxiter":maxiter,"rhobeg":.5})
    counts,qc=sample(opt.x,shots*4); runtime=time.perf_counter()-t
    return counts,qc,{"parameters":opt.x.tolist(),"optimizer_iterations":int(opt.nfev),"circuit_evaluations":evaluations+1,"runtime_seconds":runtime,"shots":shots*4}
