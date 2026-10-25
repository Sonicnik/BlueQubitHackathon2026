"""Run one G4 config on chosen IDs in parallel (controller concurrency), printing each value as it lands.

Run: .venv/bin/python strategy/variant.py '<json cfg>' tag q [q ...]
"""
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from controller.client import CONCURRENCY, Controller  # noqa: E402
from strategy import zq  # noqa: E402

cfg, tag, qs = json.loads(sys.argv[1]), sys.argv[2], [int(x) for x in sys.argv[3:]]
c = Controller(poll=10)


def one(q):
    try:
        v = c.run(f"Duke_G4_{q}", pauli_sum=zq(38, q), tag=tag, timeout=4 * 3600, **cfg)
    except Exception as e:
        v = repr(e)[:120]
    print(f"Duke_G4_{q} value={v}", flush=True)


with ThreadPoolExecutor(CONCURRENCY) as ex:
    list(ex.map(one, qs))
print("spent", round(c.spent(), 2), flush=True)
