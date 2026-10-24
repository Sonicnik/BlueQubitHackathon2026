"""Exact references from the free remote cpu statevector (<=34 qubits), via the controller. Used for S3.

Run: .venv/bin/python -m bench.remote_truth S3 30
"""
import json, sys
from pathlib import Path
from controller.client import Controller

ROOT = Path(__file__).resolve().parent.parent
c, n = sys.argv[1], int(sys.argv[2])
ctl = Controller()
cids = [f"Duke_{c}_{q}" for q in range(n)]
specs = [{"cid": cid, "device": "cpu", "pauli_sum": [("I" * (n - 1 - q) + "Z" + "I" * q, 1.0)], "tag": f"truth-{c}"}
         for q, cid in enumerate(cids)]
vals = ctl.run_many(specs, timeout=1800)
bad = [(cid, v) for cid, v in zip(cids, vals) if not isinstance(v, float)]
assert not bad, bad
(ROOT / "bench/truth" / f"{c}.json").write_text(json.dumps(
    {"source": "remote exact statevector, device=cpu, via controller ledger", "values": dict(zip(cids, vals))}, indent=1))
print(c, len(vals), "spent", ctl.spent())
