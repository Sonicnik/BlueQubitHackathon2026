"""Score one device config on surrogate families (H1-H4 calibration); appends a row to results.tsv.

Run: .venv/bin/python strategy/calibrate.py '<json cfg>' family [family ...]
"""
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import strategy  # noqa: E402
from bench.surrogates.gen import load  # noqa: E402
from controller.client import Controller, Proxy  # noqa: E402
from evaluate import score  # noqa: E402

cfg, fams = json.loads(sys.argv[1]), sys.argv[2:]
client = Proxy(Controller(poll=5))
cells = []
for fam in fams:
    t0 = time.time()
    ref = json.loads((ROOT / "bench/truth/surrogates" / f"{fam}.json").read_text())["values"]
    pred = strategy.estimate(strategy.SURROGATE_OF[fam], load(fam), client, cfg)
    r, mae = score(pred, ref)
    spread = float(__import__("numpy").std(list(pred.values())))
    cells.append(f"{fam} corr2={r:.4f} mae={mae:.4f} std={spread:.4f} t={time.time() - t0:.0f}s")
    print(cells[-1], flush=True)
with open(ROOT / "results.tsv", "a") as f:
    f.write(f"{time.strftime('%Y-%m-%dT%H:%M')}\tcalibrate\t{json.dumps(cfg)}\t\t\t\t\t{27 - client.remaining:.2f}\t{'; '.join(cells)}\n")
print("remaining", round(client.remaining, 2))
