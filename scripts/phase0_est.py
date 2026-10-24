"""Probe estimate with options/pauli_sum via the same POST /jobs estimate_only path the SDK uses."""
import json, bluequbit
from bluequbit.api import jobs
bq = bluequbit.init()
conn = bq._backend_connection
def est(cid, dev, n, options=None, ps=True):
    z = "I" * (n - 1) + "Z"
    try:
        d = jobs.submit_jobs(conn, cid, dev, pauli_sum=[(z, 1.0)] if ps else None, options=options, estimate_only=True)
        return {k: d.get(k) for k in ("estimate_ms", "estimated_cost", "error_message", "warning_message")}
    except Exception as e:
        return f"{type(e).__name__}: {e}"[:300]
res = {}
for cid, n in [("Duke_S3_0", 30), ("Duke_G4_0", 38)]:
    for dev, opt in [("mps.cpu", {"mps_bond_dimension": 64}), ("mps.cpu", {"mps_bond_dimension": 512}),
                     ("mps.gpu", {"mps_bond_dimension": 512}), ("mps.gpu", {"mps_bond_dimension": 2048}),
                     ("pauli-path", {"pauli_path_truncation_threshold": 1e-3}),
                     ("pauli-path", {"pauli_path_truncation_threshold": 1e-4}),
                     ("pauli-path.gpu", {"pauli_path_truncation_threshold": 1e-4})]:
        res[f"{cid} {dev} {opt}"] = est(cid, dev, n, opt)
print(json.dumps(res, indent=1))
