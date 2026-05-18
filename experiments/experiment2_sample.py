"""
experiment 2: empirical validation of theorem 4 on the aer
simulator. measures the detection success rate at N, N/10, N/100
shots over many trials, with no qpu cost.

defaults to noiseless aer (formula tracks pure shot noise).
pass --noise <fake_backend> to repeat the trials with a noise
model; useful to see how hardware noise widens the gap between
the formula and reality.
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.channels import (
    honest_channel, sneaky_channel, with_pauli_measurement,
)
from src.observables import (
    complete_family, frame_bound,
)
from src.sample_complexity import (
    compute_N, shots_per_observable, detection_margin,
)
from src.verification import VerifierConfig, run_verifier
from src.ibm_runtime import (
    submit_batch_aer, expectation_from_counts, save_json,
)


X_I = np.array([0.4, 1.2])
X_J = np.array([1.1, 0.3])

N_TRIALS = 20

OUTDIR = Path(__file__).resolve().parent.parent / "results"


def fingerprint(channel_fn, family, shots, noise_backend=None):
    circs = []
    for p in family:
        ch = channel_fn(X_I, X_J)
        circs.append(with_pauli_measurement(ch, p))
    counts_list, _, _ = submit_batch_aer(
        circs, shots=shots, noise_backend=noise_backend,
    )
    return {p: expectation_from_counts(c)
            for p, c in zip(family, counts_list)}


def trial(shots_per_obs, family, eps, noise_backend=None):
    fp_h = fingerprint(honest_channel, family, shots_per_obs, noise_backend)
    fp_s = fingerprint(sneaky_channel, family, shots_per_obs, noise_backend)
    cfg = VerifierConfig(eps=eps, halt_on_violation=False)
    log = run_verifier(fp_h, fp_s, family, cfg, seed=None)
    return len(log.beyond_tolerance_events()) > 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--delta", type=float, default=0.5)
    ap.add_argument("--eps", type=float, default=0.1)
    ap.add_argument("--eta", type=float, default=0.05)
    ap.add_argument("--trials", type=int, default=N_TRIALS)
    ap.add_argument("--noise", default=None,
                    help="fake backend for noise model (e.g. fake_fez)")
    args = ap.parse_args()

    family = complete_family()
    k = len(family)
    C = frame_bound(family)

    N_full = compute_N(args.delta, args.eps, k, args.eta, B=1.0, C=C)
    n_full = shots_per_observable(N_full, k)
    n_tenth = max(1, n_full // 10)
    n_hundredth = max(1, n_full // 100)

    gamma = detection_margin(args.delta, args.eps, C)

    if args.noise:
        print(f"noise model: {args.noise}")
    else:
        print("noise model: none (ideal simulation)")
    print(f"detection margin gamma = {gamma:.4f}")
    print(f"theorem 4 says N_full = {N_full}, n_per_obs = {n_full}")
    print(f"running {args.trials} trials at each of "
          f"n={n_full}, {n_tenth}, {n_hundredth}")
    print()

    results = {}
    for label, n_per in [("N", n_full),
                         ("N_over_10", n_tenth),
                         ("N_over_100", n_hundredth)]:
        successes = 0
        for t in range(args.trials):
            if trial(n_per, family, args.eps, args.noise):
                successes += 1
            if (t + 1) % 5 == 0:
                print(f"  {label}: {t+1}/{args.trials} trials, "
                      f"{successes} successes so far")
        rate = successes / args.trials
        results[label] = {
            "shots_per_obs": n_per,
            "trials": args.trials,
            "successes": successes,
            "detection_rate": rate,
        }
        print(f"{label}: {successes}/{args.trials} = {rate:.2%} detection")
        print()

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    tag = args.noise if args.noise else "ideal"
    out_path = OUTDIR / f"experiment2_sample_{tag}_{timestamp}.json"
    save_json({
        "experiment": "sample_complexity_validation",
        "noise_backend": args.noise,
        "delta": args.delta,
        "eps": args.eps,
        "eta": args.eta,
        "k": k,
        "C": C,
        "gamma": gamma,
        "N_theorem": N_full,
        "trials_per_setting": args.trials,
        "results": results,
    }, out_path)


if __name__ == "__main__":
    main()
