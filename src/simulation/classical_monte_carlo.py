from __future__ import annotations
import time
import numpy as np
from .exact_probability import validate_probabilities

def run_classical_monte_carlo(probabilities,samples,seed=42):
    p=validate_probabilities(probabilities); rng=np.random.default_rng(seed); t=time.perf_counter()
    outcomes=(rng.random((samples,6))<p).sum(axis=1); counts=np.bincount(outcomes,minlength=7); runtime=time.perf_counter()-t
    estimate=float(counts[3:].sum()/samples); se=float(np.sqrt(estimate*(1-estimate)/samples))
    return {"samples":samples,"seed":seed,"successful_outcomes":int(counts[3:].sum()),"estimated_probability":estimate,
      "standard_error":se,"normal_95_half_width":1.96*se,"runtime_seconds":runtime,"counts_by_subscriptions":counts.tolist()}
