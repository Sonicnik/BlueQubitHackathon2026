"""Phase 0 environment check: one free S1 run per qubit vs local exact, plus estimates."""
import json, time
import bluequbit
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector, SparsePauliOp

bq = bluequbit.init()
out = {"bluequbit": bluequbit.__version__}

info = bq.get_circuit_info("Duke_S1_0")
out["S1_info"] = {"n": info.num_qubits, "ops": dict(info.count_ops), "d2q": info.depth_2q}
n = info.num_qubits
rows = []
for q in range(n):
    qc = QuantumCircuit.from_qasm_file(f"kit/samples/S1/Duke_S1_{q}.qasm")
    z = "I" * (n - 1 - q) + "Z" + "I" * q
    exact = float(Statevector(qc).expectation_value(SparsePauliOp(z)).real)
    est = bq.estimate(f"Duke_S1_{q}", device="cpu")
    job = bq.run(f"Duke_S1_{q}", device="cpu", pauli_sum=[(z, 1.0)])
    rows.append({"q": q, "exact": exact, "remote": job.expectation_value, "cost": job.cost,
                 "est_cost": est.estimated_cost, "job_id": job.job_id})
out["S1"] = rows

for cid in ["Duke_S3_0", "Duke_G1_0", "Duke_G2_0", "Duke_G3_0", "Duke_G4_0"]:
    i = bq.get_circuit_info(cid)
    d = {"n": i.num_qubits, "ops": dict(i.count_ops), "d1q": i.depth_1q, "d2q": i.depth_2q}
    for dev in ["cpu", "gpu", "mps.cpu", "mps.gpu", "pauli-path"]:
        try:
            e = bq.estimate(cid, device=dev)
            d[dev] = {"ms": e.estimated_runtime, "cost": e.estimated_cost,
                      "warn": e.warning_message, "err": e.error_message}
        except Exception as ex:
            d[dev] = {"exception": f"{type(ex).__name__}: {ex}"[:300]}
    out[cid] = d
print(json.dumps(out, indent=1, default=str))
