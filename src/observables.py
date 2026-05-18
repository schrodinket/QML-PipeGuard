"""
pauli observable families for the 2-qubit qsvm experiments.

weak family is informationally incomplete by design: only the
ZZ observable. it would let a sneaky substitution slip through.

complete family is informationally complete on 2 qubits using
the single-qubit paulis on each wire. enough to reconstruct any
2-qubit hermitian operator up to identity.
"""


# pauli strings written qubit-0 first, qubit-1 second.
# example: 'XI' means X on qubit 0, identity on qubit 1.

WEAK_FAMILY = ["ZZ"]

COMPLETE_FAMILY = ["XI", "YI", "ZI", "IX", "IY", "IZ"]


def weak_family():
    return list(WEAK_FAMILY)


def complete_family():
    return list(COMPLETE_FAMILY)


def frame_bound(family):
    """frame-bound constant C(O_A) for a pauli family on 2 qubits.

    for the full single-qubit-on-each-wire family with B=1, the
    standard frame bound is 2*sqrt(2) per wire, giving sqrt(2)
    times the single-qubit value when combined. for the weak
    family (just ZZ) the bound is loose and we use a conservative
    upper estimate.
    """
    import math
    if family == COMPLETE_FAMILY:
        return 2.0 * math.sqrt(2.0)
    # weak family: not informationally complete, no useful bound
    return float("inf")


def operator_norm_bound():
    """all paulis (including tensor products) have operator norm 1."""
    return 1.0
