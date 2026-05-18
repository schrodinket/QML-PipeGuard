"""
sample complexity formula from theorem 4 of the paper.

N >= 8 B^2 k log(2k/eta) / (delta/C - eps)^2

where:
  B = operator norm bound (1 for paulis)
  k = |O_A| size of the observable family
  delta = adversarial separation (diamond norm of channel diff)
  eps = contract tolerance
  eta = failure probability (1-eta confidence)
  C = frame-bound constant of the family
"""

import math


def detection_margin(delta, eps, C):
    """gamma = delta/C - eps. positive means detection is forceable."""
    return delta / C - eps


def compute_N(delta, eps, k, eta, B=1.0, C=2.0 * math.sqrt(2.0)):
    """total shot budget needed for confidence 1-eta detection."""
    gamma = detection_margin(delta, eps, C)
    if gamma <= 0:
        raise ValueError(
            f"detection margin non-positive: delta/C - eps = {gamma:.4f}. "
            f"need delta > C*eps for detection."
        )
    return math.ceil(8.0 * B * B * k * math.log(2.0 * k / eta) / (gamma ** 2))


def shots_per_observable(N, k):
    """uniform allocation across the family."""
    return math.ceil(N / k)
