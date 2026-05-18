"""
2-qubit qsvm channels: honest (zz feature map with inversion test)
and sneaky (same plus s-gate insertion before measurement).

the inversion test computes |<phi(x_i)|phi(x_j)>|^2 as the
probability of measuring |00> after applying U_phi(x_i) then
U_phi(x_j)^dagger.
"""

import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit.library import ZZFeatureMap


N_QUBITS = 2


def feature_map(reps=2):
    """zz feature map with feature_dimension=2."""
    return ZZFeatureMap(feature_dimension=N_QUBITS, reps=reps)


def encode(x):
    """prepare |phi(x)> from a 2-d classical input x."""
    fm = feature_map()
    qc = QuantumCircuit(N_QUBITS, name=f"enc({x[0]:.2f},{x[1]:.2f})")
    qc.compose(fm.assign_parameters(np.asarray(x, dtype=float)),
               inplace=True)
    return qc


def honest_channel(x_i, x_j):
    """inversion test: U_phi(x_i) followed by U_phi(x_j)^dagger.
    measuring |00> gives the kernel value k(x_i, x_j)."""
    qc = QuantumCircuit(N_QUBITS, name="honest")
    qc.compose(encode(x_i), inplace=True)
    qc.compose(encode(x_j).inverse(), inplace=True)
    return qc


def sneaky_channel(x_i, x_j):
    """same as honest, but with an s-gate inserted on every qubit
    just before measurement. preserves <Z> on the output but
    rotates <X> and <Y>, so the sneaky fingerprint hides under a
    z-only contract."""
    qc = honest_channel(x_i, x_j)
    qc.name = "sneaky"
    for q in range(N_QUBITS):
        qc.s(q)
    return qc


def with_pauli_measurement(channel, pauli_string):
    """append basis-rotation + measurement for a multi-qubit pauli.
    pauli_string is a length-2 string over 'IXYZ'."""
    if len(pauli_string) != N_QUBITS:
        raise ValueError(f"pauli string length {len(pauli_string)} "
                         f"!= n_qubits {N_QUBITS}")
    qc = channel.copy()
    qc.add_register(*[])  # no-op, just to keep things explicit
    classical_bits = sum(1 for p in pauli_string if p != "I")
    if classical_bits == 0:
        # identity on all qubits, measure nothing
        return qc

    qc_meas = QuantumCircuit(N_QUBITS, classical_bits)
    qc_meas.compose(qc, qubits=range(N_QUBITS), inplace=True)

    c = 0
    for q, p in enumerate(pauli_string):
        if p == "X":
            qc_meas.h(q)
        elif p == "Y":
            qc_meas.sdg(q)
            qc_meas.h(q)
        elif p == "Z":
            pass  # already in z basis
        else:
            continue  # identity, skip
        qc_meas.measure(q, c)
        c += 1

    return qc_meas
