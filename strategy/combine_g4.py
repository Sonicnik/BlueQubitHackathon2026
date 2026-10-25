"""Build candidates/G4_<ver>.csv from ledger results at one threshold (level 3), GPU or CPU, by ID.
IDs without a result at that threshold fall back to the v3 (3e-4) value and are listed in the note.

Run: .venv/bin/python strategy/combine_g4.py 1e-4 v4
"""
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
th, ver = float(sys.argv[1]), sys.argv[2]
state = {}
for line in (ROOT / "ledger/jobs.jsonl").read_text().splitlines():
    r = json.loads(line)
    state.setdefault(r["key"], {}).update(r)
got, jobs = {}, []
for r in state.values():
    o = r.get("options") or {}
    if (str(r.get("cid", "")).startswith("Duke_G4_") and r["event"] == "completed" and r.get("device", "").startswith("pauli-path")
            and o.get("pauli_path_truncation_threshold") == th and o.get("pauli_path_circuit_transpilation_level") == 3):
        got.setdefault(r["cid"], (r["value"], r["device"], r.get("job_id")))
v3 = {row[0]: float(row[1]) for row in list(csv.reader((ROOT / "candidates/G4_v3.csv").read_text().splitlines()))[1:]}
ids = sorted(v3, key=lambda s: int(s.rsplit("_", 1)[1]))
vals = {i: got[i][0] if i in got else v3[i] for i in ids}
fallback = [i for i in ids if i not in got]
out = ROOT / "candidates" / f"G4_{ver}"
out.with_suffix(".csv").write_text("circuit_id,value\n" + "".join(f"{i},{vals[i]!r}\n" for i in ids))
zeros = sum(1 for i in ids if vals[i] == 0.0)
out.with_suffix(".md").write_text(
    f"# G4 {ver}\n\nPauli-path on BlueQubit GPU (pauli-path.gpu), truncation threshold {th:g}, "
    f"circuit transpilation level 3, one job per ID, <Z_q> via pauli_sum. Finer than v3 (3e-4, scored 267/1000) to keep more "
    f"of the small interference terms; {zeros} of 38 values are still exactly 0. Truncated Pauli propagation; agreement "
    f"between thresholds is not proof of accuracy.\n\n"
    f"IDs at {th:g}: {len(got)}/38. Fallback to v3 (3e-4) for: {', '.join(fallback) or 'none'}.\n\n"
    f"Job IDs: {', '.join(f'{i}:{got[i][2]}' for i in ids if i in got)}\n")
print(f"{out}.csv: {len(got)}/38 at {th:g}, {zeros} zeros, fallback {len(fallback)}")
