# qml-pipeguard

Companion code for the paper *QML-PipeGuard: Drift-Aware Behavioral Fingerprinting for Quantum Machine Learning Pipeline Integrity* (Yeniaras, 2026).

This repository implements the dual-mode verification protocol of the paper and the three experiments reported in Section 6, on a 2-qubit ZZFeatureMap QSVM pipeline. Two experiments run on IBM Quantum hardware (Heron r2, `ibm_fez` by default), one runs on the Aer simulator.

## Layout

```
qml-pipeguard/
  src/                       core modules
    integrity.py             observable contract + sha-256 audit log
    channels.py              honest and sneaky 2-qubit channels
    observables.py           weak and complete pauli families
    verification.py          dual-mode verifier (algorithm 1)
    sample_complexity.py     theorem 4 sample-budget calculator
    ibm_runtime.py           ibm quantum service helpers
  experiments/
    precheck_simulator.py    aer-only sanity check before any qpu run
    experiment1_detection.py hardware: sneaky vs honest on full pauli family
    experiment2_sample.py    simulator: theorem 4 empirical validation
    experiment3_drift.py     hardware: drift across three timepoints
  analysis/
    analyze_results.py       print short tables from json outputs
    plot_figures.py          paper-ready figures from json outputs
    frame_bound.py           numerical frame-bound constants for pauli families
  results/                   experiment outputs land here (gitignored)
```

## Install

```
git clone https://github.com/schrodinket/qml-pipeguard.git
cd qml-pipeguard
pip install -r requirements.txt
```

Tested on Python 3.10+ with the package versions in `requirements.txt`.

## Set your IBM Quantum token

For the hardware experiments only. Get a free token at <https://quantum.ibm.com>, then on Windows PowerShell:

```powershell
$env:IBM_QUANTUM_TOKEN = "your-token-here"
```

On Linux or macOS:

```
export IBM_QUANTUM_TOKEN="your-token-here"
```

The token is never written to disk by this code; it stays in the environment.

## Run order

The recommended path has three levels: ideal simulator first, then a noisy simulator that mimics IBM Heron r2, then real hardware. Open-plan QPU time is scarce; both simulator levels are free.

### Level 1: ideal simulator (logic check)

Confirms the channels and observables are wired correctly. No QPU cost, takes under a minute.

```
python experiments/precheck_simulator.py
```

If you see `precheck PASSED` you are ready for the next step.

Sample complexity validation belongs here too, also pure Aer:

```
python experiments/experiment2_sample.py
```

### Level 2: noisy simulator (hardware preview)

Same scripts, but Aer pulls a noise model from the IBM `fake_fez` backend (Heron r2 calibration data). This is the closest you can get to a hardware result without paying. Still free.

```
python experiments/precheck_simulator.py --noise fake_fez
python experiments/experiment1_detection.py --simulator --noise fake_fez
python experiments/experiment3_drift.py --simulator --noise fake_fez
python experiments/experiment2_sample.py --noise fake_fez
```

The output filenames carry the noise tag (`aer_fake_fez`) so they don't collide with the ideal runs.

Inspect at this level:

```
python analysis/analyze_results.py results/experiment*_aer_fake_fez_*.json results/experiment2_sample_fake_fez_*.json
python analysis/plot_figures.py results/experiment*_aer_fake_fez_*.json results/experiment2_sample_fake_fez_*.json --outdir results/figures_noisy
```

If the noisy simulator looks like it caught the sneaky channel on the complete family, the hardware run is worth doing.

### Level 3: real hardware

Set the token, drop both flags:

```powershell
$env:IBM_QUANTUM_TOKEN = "your-token-here"
```

```
python experiments/experiment1_detection.py --backend ibm_fez
python experiments/experiment3_drift.py --backend ibm_fez
```

Default parameters are `delta=0.5`, `eps=0.15`, `eta=0.05`. The shot count per circuit is derived from Theorem 4. Override with `--shots N` if you want a smaller or bigger budget.

### Inspect the hardware results

```
python analysis/analyze_results.py results/experiment*_ibm_fez_*.json
python analysis/plot_figures.py results/experiment*_ibm_fez_*.json --outdir results/figures
```

Available fake backends for the noise model: `fake_fez`, `fake_brisbane`, `fake_kyoto`, `fake_sherbrooke`.

## Numerical verification of frame-bound constants

The frame-bound constant `C(O_A)` controls the sample budget in Theorem 4 and its corollaries. For the local Pauli family on a single qubit, the analytic value is `C = sqrt(3)`; for extended Pauli families on two qubits (Tier 2 with diagonal correlations, Tier 3 with the full Pauli set), the values are obtained by numerical optimization (random sign-pattern search with SLSQP). The script `analysis/frame_bound.py` reproduces the tabulated values reported in Appendix A.3 of the paper:

```
python analysis/frame_bound.py --tier 1    # ~2 seconds,  C is about 1.7321 = sqrt(3)
python analysis/frame_bound.py --tier 2    # ~30 seconds, C is about 2.21
python analysis/frame_bound.py --tier 3    # ~5 minutes,  C is about 3.73
python analysis/frame_bound.py             # all three tiers
```

Trial counts are tuned per tier; Tier 3 requires more random restarts (~500) to reach the global optimum because the objective has many local maxima at lower C values.

## Mapping to the paper

| Paper artifact | Generated by |
| --- | --- |
| Section 6.1, setup table | `experiments/precheck_simulator.py` (parameters) |
| Section 6.2, table of observable deviations | `experiments/experiment1_detection.py` |
| Section 6.2, figure of weak vs complete deviations | `analysis/plot_figures.py` on experiment 1 output |
| Section 6.3, sample complexity figure | `analysis/plot_figures.py` on experiment 2 output |
| Section 6.4, drift table and recommended tolerance | `experiments/experiment3_drift.py` |
| Appendix A.3, frame-bound constants for tiers 1-3 | `analysis/frame_bound.py` |
| Algorithm 1 implementation | `src/verification.py` |
| Theorem 4 sample budget formula | `src/sample_complexity.py` |
| Observable contract and audit log | `src/integrity.py` |


## Real QPU artifacts (Section 6.2, 6.4)

The directory `results/qpu_runs/` contains the raw outputs and summaries from the two real-hardware experiments reported in Sections 6.2 (detection) and 6.4 (drift) of the paper. Both jobs ran on the IBM Heron r2 processor (`ibm_fez`) through the IBM Quantum Open Plan.

### Detection experiment (Section 6.2)

| Field | Value |
| --- | --- |
| Backend | `ibm_fez` (IBM Heron r2, 156 qubits) |
| Job ID | `d884b8is46sc73f8v28g` |
| Date | 22 May 2026, 12:02 UTC |
| Plan | IBM Quantum Open Plan |
| Shots | 2,280 per circuit |
| Total circuits | 14 (honest + sneaky, 7-Pauli family) |
| Queue time | ≈ 15 seconds |
| QPU run time | ≈ 15 seconds |
| Total wall time | 30.7 seconds |

Headline numbers:

| Family | Worst observable deviation | Halt under contract |
| --- | --- | --- |
| Weak `{Z_1 Z_2}` | 0.001 | False |
| Complete `{X, Y, Z}` on each qubit | 0.489 | True |

The sneaky channel passes the weak contract (deviation well below ε_A = 0.15) and is caught by the complete contract (deviation roughly 3.3× the tolerance), reproducing the prediction of Theorem 1 on real hardware with a wide safety margin against shot noise.

### Drift experiment (Section 6.4)

| Field | Value |
| --- | --- |
| Backend | `ibm_fez` (IBM Heron r2, 156 qubits) |
| Job ID | `d884pu2s46sc73f8vn0g` |
| Date | 22 May 2026, 12:33 UTC |
| Plan | IBM Quantum Open Plan |
| Shots | 2,280 per circuit |
| Total circuits | 18 (3 timepoints × 6-Pauli complete family) |
| Queue time | ≈ 15 seconds |
| QPU run time | ≈ 15 seconds |
| Total wall time | 30.5 seconds |

Headline numbers:

| Quantity | Value |
| --- | --- |
| Pairwise drift t1 ↔ t2 | 0.067 |
| Pairwise drift t1 ↔ t3 | 0.067 |
| Pairwise drift t2 ↔ t3 | 0.046 |
| `d_drift_typ` | 0.067 |
| Tolerance interval | [0.067, 0.289] (non-empty) |
| Recommended ε_A from calibration | 0.178 |

The interval is non-empty, so the calibration procedure of Section 5.11 converges. The operational value `ε_A = 0.15` used in the detection experiment sits within the interval `[0.067, 0.289]` and just below the midpoint of `0.178`, reflecting an operational preference for a tighter tolerance (smaller `ε_A` enlarges γ and improves the safety margin against shot noise) while staying comfortably above the typical drift (`d_drift_typ / ε_A ≈ 0.45`).

### Files

- `results/qpu_runs/experiment1_ibm_fez_20260522_120209.json` — full output of the detection job, including raw shot counts, expectation estimates, and the audit log under both the weak and the complete contract.
- `results/qpu_runs/experiment3_drift_ibm_fez_20260522_123327.json` — full output of the drift job, including the three honest fingerprints, pairwise deviations, and the tolerance-interval calculation.

### Re-running the analysis without resubmitting

To regenerate the figures and tables from the archived JSON files without consuming any QPU time:

```
python analysis/analyze_results.py results/qpu_runs/experiment*_ibm_fez_*.json
python analysis/plot_figures.py results/qpu_runs/experiment*_ibm_fez_*.json --outdir results/figures
```




## License

MIT. See `LICENSE`.
