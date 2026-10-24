"""Exact local references for the open samples (qiskit Statevector). S3 (30 q) is not feasible locally."""
import json, sys
from pathlib import Path
from qiskit import QuantumCircuit
from qiskit.quantum_info import SparsePauliOp, Statevector

ROOT = Path(__file__).resolve().parent.parent
for c in sys.argv[1:] or ["S1", "S2"]:
    files = sorted((ROOT / "kit/samples" / c).glob("*.qasm"))
    out = {}
    for f in files:
        qc = QuantumCircuit.from_qasm_file(str(f))
        n, q = qc.num_qubits, int(f.stem.rsplit("_", 1)[1])
        z = "I" * (n - 1 - q) + "Z" + "I" * q  # q0 is the rightmost character
        out[f.stem] = float(Statevector(qc).expectation_value(SparsePauliOp(z)).real)
    (ROOT / "bench/truth" / f"{c}.json").write_text(json.dumps({"source": "local exact statevector", "values": out}, indent=1))
    print(c, len(out))
