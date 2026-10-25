"""H1 pilot: a few G4 IDs on one config, printing value, submit quote, cost and runtime per job.

Run: .venv/bin/python strategy/pilot.py '<json cfg>' G4 q [q ...]
"""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from controller.client import Controller, config_key  # noqa: E402
from strategy import N, zq  # noqa: E402

cfg, circuit, qs = json.loads(sys.argv[1]), sys.argv[2], [int(x) for x in sys.argv[3:]]
c = Controller(poll=10)
for q in qs:
    cid, t0 = f"Duke_{circuit}_{q}", time.time()
    try:
        v = c.run(cid, pauli_sum=zq(N[circuit], q), tag=f"{circuit}-pilot", timeout=4 * 3600, **cfg)
    except Exception as e:
        v = repr(e)
    r = c.state.get(config_key(cid, cfg["device"], cfg.get("options"), zq(N[circuit], q)), {})
    print(f"{cid} value={v} quote=${r.get('quote')} cost=${r.get('cost')} t={time.time() - t0:.0f}s spent=${c.spent():.2f}", flush=True)
