"""Free local MPS calibration on the open samples (qiskit-aer matrix_product_state)."""
import json, sys, time
import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import SparsePauliOp
from qiskit_aer import AerSimulator

def z(n, q):
    return SparsePauliOp("I" * (n - 1 - q) + "Z" + "I" * q)

def mps_value(path, chi):
    qc = QuantumCircuit.from_qasm_file(path)
    n, q = qc.num_qubits, int(path.rsplit("_", 1)[1].split(".")[0])
    qc.save_expectation_value(z(n, q), list(range(n)))
    sim = AerSimulator(method="matrix_product_state", matrix_product_state_max_bond_dimension=chi,
                       matrix_product_state_truncation_threshold=1e-16)
    return float(np.real(sim.run(qc, shots=1).result().data()["expectation_value"]))

if __name__ == "__main__":
    c, chis = sys.argv[1], [int(x) for x in sys.argv[2:]]
    truth = json.load(open(f"bench/truth/{c}.json"))["values"]
    ids = sorted(truth, key=lambda s: int(s.rsplit("_", 1)[1]))
    t = np.array([truth[i] for i in ids])
    for chi in chis:
        t0 = time.time()
        p = np.array([mps_value(f"kit/samples/{c}/{i}.qasm", chi) for i in ids])
        r = np.corrcoef(p, t)[0, 1]
        print(f"{c} chi={chi}: corr2={max(r, 0) ** 2:.4f} mae={np.abs(p - t).mean():.4f} time={time.time() - t0:.0f}s", flush=True)
        print("  pred", np.round(p, 3).tolist(), flush=True)
    print("  true", np.round(t, 3).tolist())
