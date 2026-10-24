"""Scorer and CSV validator. Protected after Phase 1.

  evaluate.py selfcheck               exact vs exact gives corr^2 = 1 for every truth file
  evaluate.py validate FILE.csv ...   schema check against kit/problems.json
  evaluate.py score FILE.csv ...      corr^2 and MAE against bench/truth (where truth exists)
"""
import csv
import json
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
PROBLEMS = {p["grading_qasm_ids"][0].rsplit("_", 1)[0].removeprefix("Duke_"): p
            for p in json.loads((ROOT / "kit/problems.json").read_text())["data"]["problems_list"]}


def ids(circuit):
    return PROBLEMS[circuit]["grading_qasm_ids"]


def corr2(pred, truth):
    """Platform metric: Pearson corr^2, 0 for negative or undefined correlation."""
    a, b = np.asarray(pred, float), np.asarray(truth, float)
    if a.std() == 0 or b.std() == 0:
        return 0.0
    r = float(np.corrcoef(a, b)[0, 1])
    return r * r if r > 0 else 0.0


def read_csv(path):
    rows = [r for r in csv.reader(Path(path).read_text().splitlines()) if r]
    if rows and rows[0] == ["circuit_id", "value"]:
        rows = rows[1:]
    return rows


def validate(path):
    """Returns (circuit, {id: value}) or raises ValueError naming the problem."""
    rows = read_csv(path)
    if any(len(r) != 2 for r in rows):
        raise ValueError("every row must be circuit_id,value")
    got = {}
    for cid, v in rows:
        if cid in got:
            raise ValueError(f"duplicate id {cid}")
        x = float(v)
        if not math.isfinite(x):
            raise ValueError(f"non-finite value for {cid}")
        got[cid] = x
    circuits = {c for c in PROBLEMS if set(ids(c)) == set(got)}
    if len(circuits) != 1:
        raise ValueError("ids do not match exactly one problem's grading_qasm_ids")
    c = circuits.pop()
    if len(set(got.values())) == 1:
        raise ValueError("all values equal: scores 0 and looks like a probe")
    return c, got


def truth(circuit):
    p = ROOT / "bench/truth" / f"{circuit}.json"
    return json.loads(p.read_text())["values"] if p.exists() else None


def score(pred, ref):
    keys = sorted(ref)
    a, b = [pred[k] for k in keys], [ref[k] for k in keys]
    return corr2(a, b), float(np.mean(np.abs(np.subtract(a, b))))


def main(argv):
    cmd, args = argv[0], argv[1:]
    if cmd == "selfcheck":
        assert abs(corr2([1, 2, 3], [2, 4, 6]) - 1) < 1e-12 and corr2([1, 2, 3], [3, 2, 1]) == 0
        assert corr2([1, 1, 1], [1, 2, 3]) == 0
        for c in PROBLEMS:
            t = truth(c)
            if t is not None:
                assert set(t) == set(ids(c)), c
                r, mae = score(t, t)
                print(f"{c}: exact-vs-exact corr2={r:.12f} mae={mae:.1e}")
                assert abs(r - 1) < 1e-12 and mae == 0
        print("selfcheck ok")
    elif cmd in ("validate", "score"):
        bad = 0
        for f in args:
            try:
                c, pred = validate(f)
            except ValueError as e:
                print(f"INVALID {f}: {e}")
                bad += 1
                continue
            line = f"valid {f}: {c}, {len(pred)} ids"
            t = truth(c) if cmd == "score" else None
            if t is not None:
                r, mae = score(pred, t)
                line += f", corr2={r:.6f}, mae={mae:.2e}, points={r * PROBLEMS[c]['points']:.1f}"
            print(line)
        sys.exit(1 if bad else 0)
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:] or ["help"])
