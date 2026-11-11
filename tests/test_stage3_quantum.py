import numpy as np
from src.simulation.exact_probability import poisson_binomial
from src.simulation.quantum_sampler import build_subscription_circuit,ideal_statevector_distribution,distribution_from_counts

def test_statevector_matches_poisson_binomial():
    p=[.01,.2,.4,.6,.8,.99]; a=poisson_binomial(p); b=ideal_statevector_distribution(p); assert np.allclose(a["distribution"],b["distribution"],atol=1e-12)
def test_circuit_shape_and_gates():
    q=build_subscription_circuit([.5]*6); assert q.num_qubits==6 and q.count_ops()["ry"]==6 and q.count_ops()["measure"]==6
def test_bit_order_and_hamming_weight():
    counts={"000111":4,"111000":3,"111111":2,"000000":1}; n,f=distribution_from_counts(counts); assert n.tolist()==[1,0,0,7,0,0,2]
