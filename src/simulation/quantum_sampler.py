from __future__ import annotations
import time
import numpy as np
from qiskit import QuantumCircuit,transpile
from qiskit.quantum_info import Statevector
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel,depolarizing_error,ReadoutError
from .exact_probability import validate_probabilities

def rotation_angles(probabilities):
    p=validate_probabilities(probabilities); return 2*np.arcsin(np.sqrt(p))

def build_subscription_circuit(probabilities,measure=True):
    p=validate_probabilities(probabilities); qc=QuantumCircuit(6,6 if measure else 0,name="independent_subscriptions")
    for i,theta in enumerate(rotation_angles(p)): qc.ry(float(theta),i)
    if measure: qc.measure(range(6),range(6))
    return qc

def distribution_from_counts(counts):
    total=sum(counts.values()); dist=np.zeros(7,dtype=int)
    for bitstring,n in counts.items(): dist[bitstring.replace(" ","").count("1")]+=n
    return dist,dist/total

def run_shots(probabilities,shots,seed=42):
    backend=AerSimulator(seed_simulator=seed); qc=build_subscription_circuit(probabilities,True)
    tqc=transpile(qc,backend,optimization_level=1,seed_transpiler=seed); t=time.perf_counter()
    counts=backend.run(tqc,shots=shots).result().get_counts(); runtime=time.perf_counter()-t
    counts_by_k,freq=distribution_from_counts(counts); successes=int(counts_by_k[3:].sum()); estimate=successes/shots
    se=float(np.sqrt(estimate*(1-estimate)/shots))
    return {"shots":shots,"successful_outcomes":successes,"estimated_probability":estimate,"standard_error":se,
      "normal_95_half_width":1.96*se,"runtime_seconds":runtime,"counts_by_subscriptions":counts_by_k.tolist(),"raw_counts":dict(counts)}

def documented_noise_model(one_qubit_depolarizing=.005,readout_error=.01):
    noise=NoiseModel(); noise.add_all_qubit_quantum_error(depolarizing_error(one_qubit_depolarizing,1),["ry"])
    noise.add_all_qubit_readout_error(ReadoutError([[1-readout_error,readout_error],[readout_error,1-readout_error]]))
    return noise

def run_noisy_shots(probabilities,shots=4096,seed=142,one_qubit_depolarizing=.005,readout_error=.01):
    noise=documented_noise_model(one_qubit_depolarizing,readout_error); backend=AerSimulator(noise_model=noise,seed_simulator=seed)
    qc=transpile(build_subscription_circuit(probabilities,True),backend,optimization_level=1,seed_transpiler=seed); t=time.perf_counter()
    counts=backend.run(qc,shots=shots).result().get_counts(); runtime=time.perf_counter()-t; by_k,_=distribution_from_counts(counts)
    estimate=float(by_k[3:].sum()/shots); se=float(np.sqrt(estimate*(1-estimate)/shots))
    return {"shots":shots,"seed":seed,"estimated_probability":estimate,"standard_error":se,"normal_95_half_width":1.96*se,"runtime_seconds":runtime,
      "counts_by_subscriptions":by_k.tolist(),"one_qubit_depolarizing":one_qubit_depolarizing,"readout_error":readout_error}

def ideal_statevector_distribution(probabilities):
    qc=build_subscription_circuit(probabilities,False); probs=Statevector(qc).probabilities(); dist=np.zeros(7)
    for basis,p in enumerate(probs): dist[basis.bit_count()]+=p
    return {"distribution":dist,"probability_at_least_3":float(dist[3:].sum())}
