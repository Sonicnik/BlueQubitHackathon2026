"""Strategy: which device/options per circuit, and how rungs combine. The research agent edits this file.

  .venv/bin/python strategy.py G2 [G4 ...]   run the configured rung(s), write candidates/<c>_<version>.csv + .md
"""
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VERSION = {"G2": "v2", "G4": "v3"}
# shortcut: G4 runs one job at a time while a $25 Pauli-path reservation holds the cap; drop once H1 calibration ends
SERIAL = {"G4"}
N = {"S1": 4, "S2": 16, "S3": 30, "G1": 30, "G2": 36, "G3": 36, "G4": 38}

# One rung per circuit for the baseline; see NOTES_RUN.md Phase 2 for why.
CONFIG = {
    "G2": {"device": "mps.cpu", "options": {"mps_bond_dimension": 128}},
    "G4": {"device": "pauli-path.gpu",
           "options": {"pauli_path_truncation_threshold": 3e-4, "pauli_path_circuit_transpilation_level": 3}},
}

# Pauli-path is avoided for now: at 1e-3 it returned exactly 0.0 on G4, and the platform quoted $25 / 100 h at submit.
NOTES = {
    "G2": "MPS (mps.cpu) at bond dimension 128 on BlueQubit, one job per ID, <Z_q> via pauli_sum. On a 30-qubit Haar-chain "
          "echo surrogate with exact answers, corr2 was 0.73 / 0.87 at chi 32 / 64; G2 v1 (chi=32) scored 342/600. "
          "Still truncated; agreement between rungs is not proof of accuracy.",
    "G4": "Pauli-path on BlueQubit GPU (pauli-path.gpu), truncation threshold 3e-4, circuit transpilation level 3, one job "
          "per ID, <Z_q> via pauli_sum. Level 3 cancels gates outside the butterfly's light cone before propagation; at the "
          "default level 2 every tested ID returned exactly 0. Truncation drops the small interference terms that carry the "
          "OTOC(2) signal, so many IDs are expected to be 0 or near 0; treat as a partial-signal estimate. MPS (chi 32-256) "
          "was rejected: values stuck at 0.5-0.6 where G4 is mostly within +-0.1, and v1 (chi=32) scored 0/1000.",
}


def zq(n, q):
    return [("I" * (n - 1 - q) + "Z" + "I" * q, 1.0)]  # q0 is the rightmost character


# Benchmark surrogate -> the G circuit whose config it tests (bench/surrogates/gen.py FAMILIES).
SURROGATE_OF = {"chain20": "G2", "chain30": "G2", "grid4x5": "G4", "grid4x6": "G4"}


def predict(circuit: str, client) -> dict[str, float]:
    n = N[circuit]
    return estimate(circuit, [(f"Duke_{circuit}_{q}", None, n, q) for q in range(n)], client)


def estimate(circuit, items, client, cfg=None):
    """items: [(name, QuantumCircuit or None for a hidden id, n, q)] run with cfg (default CONFIG[circuit]). Returns {name: value}."""
    cfg = cfg or CONFIG[circuit]
    specs = [dict(cid=name, circuit=qc, pauli_sum=zq(n, q), tag=f"{circuit}-{VERSION[circuit]}" + ("-bench" if qc else ""), **cfg)
             for name, qc, n, q in items]
    if cfg["device"].startswith("pauli-path") or (circuit in SERIAL and items and items[0][1] is None):  # each job is quoted ~$25 at submit, so the cap admits one at a time
        vals = []
        for sp in specs:
            try:
                vals.append(client.run(timeout=6 * 3600, **sp))
            except Exception as e:
                vals.append(e)
    else:
        vals = client.run_many(specs, timeout=6 * 3600)
    bad = {s["cid"]: repr(v) for s, v in zip(specs, vals) if not isinstance(v, float)}
    if bad:
        raise RuntimeError(f"{len(bad)} jobs did not complete: {bad}")
    return {s["cid"]: v for s, v in zip(specs, vals)}


def write_candidate(circuit, pred, client, note):
    out = ROOT / "candidates"
    out.mkdir(exist_ok=True)
    stem = out / f"{circuit}_{VERSION[circuit]}"
    ids = sorted(pred, key=lambda s: int(s.rsplit("_", 1)[1]))
    stem.with_suffix(".csv").write_text("circuit_id,value\n" + "".join(f"{i},{pred[i]!r}\n" for i in ids))
    cfg = CONFIG[circuit]
    recs = [client.get(i, cfg["device"], cfg["options"], zq(N[circuit], int(i.rsplit("_", 1)[1]))) for i in ids]
    cost = sum(r.get("cost") or 0 for r in recs)
    stem.with_suffix(".md").write_text(
        f"# {circuit} {VERSION[circuit]}\n\n{note}\n\nConfig: `{json.dumps(CONFIG[circuit])}`. Jobs: {len(recs)}, cost ${cost:.2f}. "
        f"Written {time.strftime('%Y-%m-%d %H:%M %Z')}.\n\nJob IDs: {', '.join(r.get('job_id', '?') for r in recs)}\n")
    return stem


if __name__ == "__main__":
    from controller.client import Controller, Proxy

    client = Proxy(Controller(poll=15))
    for c in sys.argv[1:]:
        p = predict(c, client)
        print(c, write_candidate(c, p, client, NOTES.get(c, "")), "remaining", round(client.remaining, 2))
