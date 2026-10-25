"""H4 on grid4x7: score pauli-path.gpu L3 at 3e-4, at 1e-4, and the mean of their standardized vectors against exact
truth (decision rule pre-registered in results.tsv), then build G4_v5 with the same rule if the mean wins.

Run: .venv/bin/python strategy/ensemble_eval.py
"""
import csv
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from evaluate import corr2  # noqa: E402

state = {}
for line in (ROOT / "ledger/jobs.jsonl").read_text().splitlines():
    r = json.loads(line)
    state.setdefault(r["key"], {}).update(r)


def vec(prefix, th, n):
    got = {}
    for r in state.values():
        o = r.get("options") or {}
        if (str(r.get("cid", "")).startswith(prefix) and r["event"] == "completed" and r.get("device") == "pauli-path.gpu"
                and o.get("pauli_path_truncation_threshold") == th and o.get("pauli_path_circuit_transpilation_level") == 3
                and o.get("pauli_path_weight_cutoff") is None):
            got[int(r["cid"].rsplit("_", 1)[1])] = r["value"]
    return np.array([got[q] for q in range(n)]) if len(got) == n else None


def standardize(v):
    return (v - v.mean()) / v.std() if v.std() > 1e-12 else None  # near-constant vectors only add noise


truth = json.loads((ROOT / "bench/truth/surrogates/grid4x7.json").read_text())["values"]
t = np.array([truth[f"grid4x7_{q}"] for q in range(28)])
a, b = vec("grid4x7_", 3e-4, 28), vec("grid4x7_", 1e-4, 28)
assert a is not None and b is not None, "grid4x7 runs incomplete"
cands = {"3e-4": a, "1e-4": b, "mean_std": (standardize(a) + standardize(b)) / 2}
scores = {k: corr2(v, t) for k, v in cands.items()}
for k, s in scores.items():
    print(f"grid4x7 {k}: corr2={s:.4f}  zeros={int((cands[k] == 0).sum())}")
best = max(scores, key=scores.get)
print("pre-registered pick:", best)

if best == "mean_std":
    v3, v4 = (np.array([float(r[1]) for r in list(csv.reader((ROOT / f"candidates/G4_{v}.csv").read_text().splitlines()))[1:]])
              for v in ("v3", "v4"))
    ids = [f"Duke_G4_{q}" for q in range(38)]
    m = (standardize(v3) + standardize(v4)) / 2
    (ROOT / "candidates/G4_v5.csv").write_text("circuit_id,value\n" + "".join(f"{i},{x!r}\n" for i, x in zip(ids, m)))
    (ROOT / "candidates/G4_v5.md").write_text(
        "# G4 v5\n\nPauli-path on BlueQubit GPU (pauli-path.gpu), circuit transpilation level 3, one job per ID, <Z_q> via "
        "pauli_sum, run at truncation thresholds 3e-4 and 1e-4; each 38-value vector standardized (zero mean, unit "
        "variance) and averaged, because Pauli-path truncation error is non-monotonic in the threshold (arXiv 2507.10771). "
        f"Chosen by a rule fixed in advance on a 28-qubit, 16-layer Haar-grid echo surrogate with exact answers: corr2 "
        f"3e-4 {scores['3e-4']:.3f}, 1e-4 {scores['1e-4']:.3f}, mean {scores['mean_std']:.3f}. Values are on a standardized "
        "scale (Pearson correlation ignores scale and offset). Truncated simulation; not proof of accuracy.\n\n"
        "Source vectors: candidates/G4_v3.csv and candidates/G4_v4.csv (job IDs in their notes).\n")
    print("wrote candidates/G4_v5.csv")
