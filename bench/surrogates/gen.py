"""Surrogate echo circuits for the G families, at sizes with exact local answers.

Echo (as in the kit QASM): U, x b, U^dagger, z q, U, x b, U^dagger. U = L brickwork layers of Haar 2q gates,
each compiled to u3+cz (3 CZ), like the samples. Layers cycle through the layout's edge matchings.

  .venv/bin/python -m bench.surrogates.gen [family ...]    writes bench/surrogates/<family>/*.qasm and bench/truth/surrogates/<family>.json
"""
import json
from pathlib import Path

import numpy as np
from qiskit import QuantumCircuit, qasm2, transpile
from qiskit.circuit.library import UnitaryGate
from qiskit.quantum_info import SparsePauliOp, random_unitary
from qiskit_aer import AerSimulator

ROOT = Path(__file__).resolve().parents[2]

# name: (layout, size, U layers, butterfly). Chain mirrors G2 (L = n/2, butterfly mid). Grid mirrors G4 (b=0) with
# layers cut to 10 so values sit in G4's regime (80% within +-0.1); 16 layers on 4x5 scrambles to ~0.
FAMILIES = {
    "chain20": ("chain", 20, 10, 10),
    "grid4x5": ("grid", (4, 5), 10, 0),
    "grid4x6": ("grid", (4, 6), 10, 0),  # H0: larger G4 proxy; 12 layers gives identical values (extra layers miss qubit 0)
}


def matchings(layout, size):
    if layout == "chain":
        return [[(i, i + 1) for i in range(s, size - 1, 2)] for s in (0, 1)], size
    r, c = size
    idx = lambda i, j: i * c + j
    h = [[(idx(i, j), idx(i, j + 1)) for i in range(r) for j in range(s, c - 1, 2)] for s in (0, 1)]
    v = [[(idx(i, j), idx(i + 1, j)) for i in range(s, r - 1, 2) for j in range(c)] for s in (0, 1)]
    return [h[0], v[0], h[1], v[1]], r * c


def build_u(layout, size, layers, seed):
    ms, n = matchings(layout, size)
    rng = np.random.default_rng(seed)
    u = QuantumCircuit(n)
    for l in range(layers):
        for a, b in ms[l % len(ms)]:
            u.append(UnitaryGate(random_unitary(4, seed=int(rng.integers(2**31)))), [a, b])
    return transpile(u, basis_gates=["u3", "cz"], optimization_level=1, seed_transpiler=seed), n


def echo(u, n, b, q):
    qc = QuantumCircuit(n)
    ui = u.inverse()
    for part in (u, "x", ui, "z", u, "x", ui):
        if part == "x":
            qc.x(b)
        elif part == "z":
            qc.z(q)
        else:
            qc.compose(part, inplace=True)
    return qc


def exact(qc, n, q):
    c = qc.copy()
    c.save_expectation_value(SparsePauliOp("I" * (n - 1 - q) + "Z" + "I" * q), list(range(n)))
    return float(np.real(AerSimulator(method="statevector").run(c).result().data()["expectation_value"]))


def load(family):
    """[(name, QuantumCircuit, n, q)] for a family, from the written QASM."""
    files = sorted((ROOT / "bench/surrogates" / family).glob("*.qasm"), key=lambda f: int(f.stem.rsplit("_", 1)[1]))
    out = []
    for f in files:
        qc = QuantumCircuit.from_qasm_file(str(f))
        out.append((f.stem, qc, qc.num_qubits, int(f.stem.rsplit("_", 1)[1])))
    return out


if __name__ == "__main__":
    import sys
    import time
    for fam in sys.argv[1:] or FAMILIES:
        layout, size, layers, b = FAMILIES[fam]
        t0 = time.time()
        u, n = build_u(layout, size, layers, seed=sum(map(ord, fam)))
        uu = u.compose(u.inverse())  # inverse cancellation check: U U^dagger leaves |0...0>, so <Z_q> = 1
        assert abs(exact(uu, n, n // 2) - 1) < 1e-9
        d = ROOT / "bench/surrogates" / fam
        d.mkdir(parents=True, exist_ok=True)
        vals = {}
        for q in range(n):
            qc = echo(u, n, b, q)
            (d / f"{fam}_{q}.qasm").write_text(qasm2.dumps(qc))
            vals[f"{fam}_{q}"] = exact(qc, n, q)
        t = ROOT / "bench/truth/surrogates"
        t.mkdir(parents=True, exist_ok=True)
        (t / f"{fam}.json").write_text(json.dumps({"source": "local exact statevector (qiskit-aer)", "layout": layout,
                                                   "size": size, "layers": layers, "butterfly": b,
                                                   "cz_total": qc.count_ops().get("cz", 0), "values": vals}, indent=1))
        print(fam, n, "qubits", qc.count_ops().get("cz"), "CZ", f"{time.time() - t0:.0f}s", np.round(list(vals.values()), 3).tolist(), flush=True)
