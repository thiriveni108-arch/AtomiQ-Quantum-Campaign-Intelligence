import numpy as np
from qiskit.quantum_info import Statevector
from src.quantum_models import circuits
from src.pennylane_models import equivalent_kernel,trainable_kernel,train_kernel_parameters,fixed_ry_cnot_kernel

def test_qiskit_pennylane_kernel_equivalence():
    rng=np.random.default_rng(42); X=rng.uniform(-np.pi,np.pi,(5,4)); fm,_=circuits()
    s=np.asarray([Statevector(fm.assign_parameters(x)).data for x in X]); q=np.abs(s@s.conj().T)**2; p=equivalent_kernel(X)
    assert np.max(np.abs(q-p))<1e-10
def test_kernel_psd_and_range():
    X=np.random.default_rng(2).normal(size=(6,4)); K=equivalent_kernel(X)
    assert np.all((K>=-1e-12)&(K<=1+1e-12)) and np.linalg.eigvalsh(K).min()>-1e-10
def test_trainable_kernel_smoke():
    X=np.random.default_rng(3).normal(size=(8,4)); y=np.array([0,1]*4)
    t,h=train_kernel_parameters(X,y,iterations=1,cap=8); K=trainable_kernel(X,X,t)
    assert t.shape==(1,4,2) and len(h)==1 and K.shape==(8,8)

def test_fixed_depth1_matches_zero_parameter_depth1_kernel():
    X=np.random.default_rng(7).normal(size=(6,4)); theta=np.zeros((1,4,2))
    assert np.allclose(fixed_ry_cnot_kernel(X),trainable_kernel(X,X,theta,depth=1),atol=1e-12)
