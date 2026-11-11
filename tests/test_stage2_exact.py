from src.optimization.exact_solver import Candidate,Constraints,exact_solve

def cs(values=None):
    values=values or list(range(10,0,-1)); return [Candidate(f"D{i:02}",1,0,values[i],1) for i in range(10)]
def test_exact_enumerates_210_and_optimum():
    r=exact_solve(cs(),Constraints(6,25,22)); assert r["enumerated_combinations"]==210 and r["feasible_combinations"]==210 and r["best"]["selected_ids"]==["D00","D01","D02","D03","D04","D05"]
def test_infeasible_and_negative_values():
    bad=[Candidate(f"D{i}",0,5,1,5) for i in range(10)]; assert exact_solve(bad,Constraints(6,1,1))["status"]=="infeasible"
def test_tie_break_is_lexicographic():
    r=exact_solve(cs([1]*10),Constraints(6,25,22)); assert r["best"]["selected_ids"]==["D00","D01","D02","D03","D04","D05"]
def test_zero_and_extreme_probabilities():
    c=cs(); c[0]=Candidate("D00",0,0,100,1); c[1]=Candidate("D01",1,0,100,1); assert exact_solve(c)["best"]["objective"]>=100
