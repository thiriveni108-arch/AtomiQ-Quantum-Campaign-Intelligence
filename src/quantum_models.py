from __future__ import annotations
import numpy as np
from qiskit.circuit.library import zz_feature_map, real_amplitudes
from qiskit.primitives import StatevectorSampler
from qiskit_machine_learning.kernels import FidelityStatevectorKernel
from qiskit_machine_learning.algorithms.classifiers import VQC
from qiskit_machine_learning.optimizers import COBYLA
from sklearn.svm import SVC
from sklearn.calibration import CalibratedClassifierCV

def circuits(reps=1):
    fm = zz_feature_map(feature_dimension=4, reps=reps, entanglement="linear")
    ansatz = real_amplitudes(num_qubits=4, reps=1, entanglement="linear")
    return fm, ansatz

def circuit_metadata(reps=1):
    fm, ansatz = circuits(reps)
    def m(c):
        d=c.decompose(); return {"qubits":c.num_qubits,"depth":d.depth(),"size":d.size(),"gate_counts":dict(d.count_ops())}
    return {"feature_map":m(fm),"ansatz":m(ansatz),"combined":m(fm.compose(ansatz))}

def qsvc(reps=1):
    fm,_=circuits(reps)
    kernel=FidelityStatevectorKernel(feature_map=fm, cache_size=512, auto_clear_cache=False, shots=None)
    base = SVC(kernel=kernel.evaluate, class_weight="balanced", random_state=42)
    # Sigmoid calibration uses only inner training folds; no outer validation labels leak.
    return CalibratedClassifierCV(base, method="sigmoid", cv=3, ensemble=False), kernel

def vqc(maxiter=30, reps=1, seed=42, callback=None):
    fm,ansatz=circuits(reps)
    rng=np.random.default_rng(seed)
    return VQC(feature_map=fm, ansatz=ansatz, loss="cross_entropy", optimizer=COBYLA(maxiter=maxiter),
               initial_point=rng.uniform(-0.1,0.1,ansatz.num_parameters), sampler=StatevectorSampler(seed=seed), callback=callback)
