import numpy as np
from src.optimization.exact_solver import Candidate,Constraints
from src.optimization.qubo_formulation import build_slack_qubo,encode_with_slack,direct_penalized_energy
from src.optimization.qaoa_standard import decode_counts

def fixture(): return [Candidate(f"D{i}",.1*i,i%4+1,10+i,i%3+1) for i in range(10)]
def test_qubo_matches_direct_penalty_all_decisions():
    c=fixture(); con=Constraints(); q=build_slack_qubo(c,con)
    for z in range(1<<10):
        b=[(z>>i)&1 for i in range(10)]; encoded=encode_with_slack(c,b,con,q)
        assert abs(q.energy(encoded)-direct_penalized_energy(c,b,con,q.penalty))<1e-7
def test_slack_ranges_and_qubit_overhead():
    q=build_slack_qubo(fixture()); assert sum(q.cost_slack_weights)==25 and sum(q.capacity_slack_weights)==22 and q.n_qubits==20
def test_endian_decoding():
    assert next(iter(decode_counts({"0000000001":1},10)))==(1,0,0,0,0,0,0,0,0,0)
