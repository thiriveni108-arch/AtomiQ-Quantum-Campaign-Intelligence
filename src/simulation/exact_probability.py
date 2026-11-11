from __future__ import annotations
import math
import numpy as np

def validate_probabilities(probabilities, expected_n=6):
    p=np.asarray(probabilities,dtype=float)
    if p.shape!=(expected_n,): raise ValueError(f"Expected exactly {expected_n} probabilities")
    if not np.all(np.isfinite(p)): raise ValueError("Probabilities must be finite")
    if np.any((p<0)|(p>1)): raise ValueError("Probabilities must lie in [0, 1]")
    return p

def poisson_binomial(probabilities):
    """Stable O(n^2) dynamic program for independent non-identical Bernoulli trials."""
    p=validate_probabilities(probabilities); dist=np.zeros(len(p)+1); dist[0]=1.
    for pi in p:
        nxt=np.zeros_like(dist)
        nxt[:-1]+=dist[:-1]*(1-pi)
        nxt[1:]+=dist[:-1]*pi
        dist=nxt
    if not np.isclose(dist.sum(),1.,atol=1e-12): raise ArithmeticError("Poisson-binomial distribution failed normalization")
    return {"distribution":dist,"probability_at_least_3":float(dist[3:].sum())}
