from src.optimization.exact_solver import Candidate,Constraints
from src.optimization.qaoa_constrained import verify_weight_preservation

def test_xy_mixer_preserves_exact_six():
    c=[Candidate(f"D{i}",.5,1,10,1) for i in range(10)]; assert verify_weight_preservation(c,Constraints())<1e-12
