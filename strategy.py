"""Strategy: which device/options per circuit, and how rungs combine. The research agent edits this file.

  .venv/bin/python strategy.py G2 [G4 ...]   run the configured rung(s), write candidates/<c>_<version>.csv + .md
"""
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VERSION = "v1"
N = {"S1": 4, "S2": 16, "S3": 30, "G1": 30, "G2": 36, "G3": 36, "G4": 38}

# One rung per circuit for the baseline; see NOTES_RUN.md Phase 2 for why.
CONFIG = {
    "G2": {"device": "mps.cpu", "options": {"mps_bond_dimension": 32}},
    "G4": {"device": "mps.cpu", "options": {"mps_bond_dimension": 32}},
}

# Pauli-path is avoided for now: at 1e-3 it returned exactly 0.0 on G4, and the platform quoted $25 / 100 h at submit.
NOTES = {
    "G2": "MPS (mps.cpu) at bond dimension 32 on BlueQubit, one job per ID, <Z_q> via pauli_sum. Truncation error unknown "
          "on the hidden circuit; local MPS on the same-family sample S2 gives corr2 0.96 at chi=32 and 0.999 at chi=64.",
    "G4": "MPS (mps.cpu) at bond dimension 32 on BlueQubit, one job per ID, <Z_q> via pauli_sum. A 2D grid strains MPS, so "
          "chi=32 is likely far from converged; treat as a baseline only.",
}


def zq(n, q):
    return [("I" * (n - 1 - q) + "Z" + "I" * q, 1.0)]  # q0 is the rightmost character


def predict(circuit: str, client) -> dict[str, float]:
    n, cfg = N[circuit], CONFIG[circuit]
    specs = [dict(cid=f"Duke_{circuit}_{q}", pauli_sum=zq(n, q), tag=f"{circuit}-{VERSION}", **cfg) for q in range(n)]
    vals = client.run_many(specs, timeout=6 * 3600)
    bad = {s["cid"]: repr(v) for s, v in zip(specs, vals) if not isinstance(v, float)}
    if bad:
        raise RuntimeError(f"{len(bad)} jobs did not complete: {bad}")
    return {s["cid"]: v for s, v in zip(specs, vals)}


def write_candidate(circuit, pred, client, note):
    out = ROOT / "candidates"
    out.mkdir(exist_ok=True)
    stem = out / f"{circuit}_{VERSION}"
    ids = sorted(pred, key=lambda s: int(s.rsplit("_", 1)[1]))
    stem.with_suffix(".csv").write_text("circuit_id,value\n" + "".join(f"{i},{pred[i]!r}\n" for i in ids))
    cfg = CONFIG[circuit]
    recs = [client.get(i, cfg["device"], cfg["options"], zq(N[circuit], int(i.rsplit("_", 1)[1]))) for i in ids]
    cost = sum(r.get("cost") or 0 for r in recs)
    stem.with_suffix(".md").write_text(
        f"# {circuit} {VERSION}\n\n{note}\n\nConfig: `{json.dumps(CONFIG[circuit])}`. Jobs: {len(recs)}, cost ${cost:.2f}. "
        f"Written {time.strftime('%Y-%m-%d %H:%M %Z')}.\n\nJob IDs: {', '.join(r.get('job_id', '?') for r in recs)}\n")
    return stem


if __name__ == "__main__":
    from controller.client import Controller, Proxy

    client = Proxy(Controller(poll=15))
    for c in sys.argv[1:]:
        p = predict(c, client)
        print(c, write_candidate(c, p, client, NOTES.get(c, "")), "remaining", round(client.remaining, 2))
