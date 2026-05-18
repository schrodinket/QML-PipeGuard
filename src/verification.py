"""
algorithm 1 of the paper: dual-mode verifier.

each round picks a random pauli from the family, requests an
empirical estimate, computes the deviation against the reference
fingerprint, and either halts (beyond tolerance) or logs a drift
event (within tolerance).
"""

import random
from dataclasses import dataclass

from .integrity import AuditLog


@dataclass
class VerifierConfig:
    eps: float
    confidence: float = 0.95
    halt_on_violation: bool = True


def run_verifier(reference_fp, candidate_fp, observables, cfg, seed=42):
    """run the dual-mode verifier across all observables in the family.

    reference_fp, candidate_fp: dicts mapping pauli string -> float.
    observables: list of pauli strings to test (one per round).
    cfg: VerifierConfig.

    returns the audit log. if halt_on_violation is True, the loop
    stops at the first beyond-tolerance observable.
    """
    rng = random.Random(seed)
    log = AuditLog()

    # shuffle so the order is random across runs
    order = list(observables)
    rng.shuffle(order)

    for i, p in enumerate(order):
        ref = reference_fp[p]
        meas = candidate_fp[p]
        ev = log.commit(
            round_idx=i,
            pauli=p,
            measured=meas,
            reference=ref,
            epsilon=cfg.eps,
        )
        if ev.kind == "beyond_tolerance" and cfg.halt_on_violation:
            break

    return log


def summarize_log(log, eps):
    """produce a short summary of what the verifier saw."""
    n = len(log.events)
    n_violations = len(log.beyond_tolerance_events())
    n_drift = len(log.within_tolerance_events())

    if log.events:
        worst = max(e.deviation for e in log.events)
        worst_p = max(log.events, key=lambda e: e.deviation).pauli
    else:
        worst, worst_p = 0.0, None

    return {
        "n_rounds": n,
        "n_violations": n_violations,
        "n_drift_events": n_drift,
        "worst_deviation": worst,
        "worst_pauli": worst_p,
        "epsilon": eps,
        "head_hash": log.head_hash(),
        "halted": n_violations > 0,
    }
