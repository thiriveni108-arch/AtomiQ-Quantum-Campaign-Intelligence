import numpy as np,pytest
from src.simulation.exact_probability import poisson_binomial,validate_probabilities

def test_all_zero_and_all_one():
    assert poisson_binomial([0]*6)["probability_at_least_3"]==0
    assert poisson_binomial([1]*6)["probability_at_least_3"]==1
def test_exactly_three_certain(): assert poisson_binomial([1,1,1,0,0,0])["probability_at_least_3"]==1
def test_half_analytical():
    r=poisson_binomial([.5]*6); assert r["probability_at_least_3"]==42/64 and np.isclose(r["distribution"].sum(),1)
def test_mixed_normalizes(): assert np.isclose(poisson_binomial([.01,.2,.4,.6,.8,.99])["distribution"].sum(),1)
@pytest.mark.parametrize("p",[[0]*5,[-.1]*6,[1.1]*6,[float('nan')]*6])
def test_invalid_probabilities(p):
    with pytest.raises(ValueError): validate_probabilities(p)
