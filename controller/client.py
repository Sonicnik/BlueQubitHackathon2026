"""Spend controller: the only code that touches the BlueQubit token.

Every job goes through `Controller.run`, which ledgers it (committed -> submitted -> completed|failed)
in an append-only JSONL file, refuses anything that would push committed spend over the cap,
returns cached results for repeated configs, and reconciles jobs left outstanding by a crash or timeout.
Strategy code gets a `Proxy`, never the controller or the SDK client.
"""
from __future__ import annotations

import hashlib
import json
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

CAP_USD = 30.00  # raised by the user 2026-10-25 ~10:25 ET (was 27.00)
CONCURRENCY = 4
RETRIES = 2
ROOT = Path(__file__).resolve().parent.parent
LEDGER = ROOT / "ledger" / "jobs.jsonl"
PENDING = {"PENDING", "QUEUED", "RUNNING"}


class BudgetExceeded(Exception):
    pass


class JobFailed(Exception):
    pass


class JobPending(Exception):
    """Job still running when the wait timed out; it stays outstanding in the ledger."""


def config_key(cid, device, options=None, pauli_sum=None, circuit=None) -> str:
    """circuit: optional QuantumCircuit for our own (non-hidden) circuits; cid is then just its name."""
    src = None
    if circuit is not None:
        from qiskit import qasm2
        src = hashlib.sha256(qasm2.dumps(circuit).encode()).hexdigest()
    blob = json.dumps([cid, device, options or {}, pauli_sum] + ([src] if src else []), sort_keys=True)
    return hashlib.sha256(blob.encode()).hexdigest()[:24]


class BQBackend:
    """Thin adapter over the bluequbit SDK. Costs in USD."""

    def __init__(self):
        import bluequbit
        from bluequbit.api import jobs

        self._jobs = jobs
        self.bq = bluequbit.init()
        os.environ.pop("BLUEQUBIT_API_TOKEN", None)  # keep it out of anything spawned later

    def estimate(self, cid, device, options, pauli_sum):
        # bq.estimate() drops options/pauli_sum; the same endpoint accepts them (costs in cents)
        d = self._jobs.submit_jobs(self.bq._backend_connection, cid, device, pauli_sum=pauli_sum,
                                   options=options, estimate_only=True)
        if d.get("error_message"):
            raise JobFailed(d["error_message"])
        return (d.get("estimated_cost") or 0) / 100.0

    def submit(self, cid, device, options, pauli_sum, name):
        from bluequbit.exceptions import BQJobNotCompleteError
        try:
            jr = self.bq.run(cid, device=device, asynchronous=True, job_name=name,
                             pauli_sum=pauli_sum, options=options)
        except BQJobNotCompleteError as e:
            raise JobFailed(f"{e.run_status}: {e.error_message}") from None
        return jr.job_id, jr.estimated_cost or 0.0  # submit-time quote (USD), can far exceed estimate_only

    def cancel(self, job_id):
        try:
            self.bq.cancel(job_id)
        except Exception:  # already terminal, or cancel timed out; the reconcile below records the real state
            pass

    @staticmethod
    def _view(jr):
        return {"job_id": jr.job_id, "status": jr.run_status, "cost": jr.cost or 0.0,
                "value": jr.expectation_value if jr.run_status == "COMPLETED" else None,
                "error": jr.error_message, "name": jr.job_name}

    def get(self, job_id):
        return self._view(self.bq.get(job_id))

    def find_by_name(self, name, since):
        import datetime
        after = datetime.datetime.fromtimestamp(since, datetime.timezone.utc)  # SDK rejects a bare float
        hits = [self._view(j) for j in self.bq.search(created_later_than=after) if j.job_name == name]
        return hits[0] if hits else None


class Controller:
    def __init__(self, backend=None, ledger=LEDGER, cap=CAP_USD, poll=5.0):
        self.ledger = Path(ledger)
        self.ledger.parent.mkdir(parents=True, exist_ok=True)
        self.cap, self.poll = cap, poll
        self._backend = backend
        self._lock = threading.RLock()
        self.state = {}  # key -> latest merged record
        if self.ledger.exists():
            for line in self.ledger.read_text().splitlines():
                if line.strip():
                    r = json.loads(line)
                    self.state.setdefault(r["key"], {}).update(r)

    @property
    def backend(self):
        if self._backend is None:
            self._backend = BQBackend()
        return self._backend

    def _append(self, rec):
        with self._lock:
            rec = {"t": time.time(), **rec}
            with self.ledger.open("a") as f:
                f.write(json.dumps(rec) + "\n")
                f.flush()
                os.fsync(f.fileno())
            self.state.setdefault(rec["key"], {}).update(rec)

    # --- money ---------------------------------------------------------------
    def spent(self):
        """Actual cost of terminal jobs plus estimates of committed/in-flight ones."""
        tot = 0.0
        for r in self.state.values():
            if r["event"] in ("completed", "failed"):
                tot += r.get("cost") or 0.0
            else:
                tot += r.get("est_reserved", 0.0)
        return tot

    def remaining(self):
        return self.cap - self.spent()

    def _overrun(self, device):
        """Worst actual/estimate ratio seen on this device (>=1), so estimates that run low tighten the cap."""
        ratios = [r["cost"] / r["est"] for r in self.state.values()
                  if r.get("device") == device and r["event"] == "completed" and r.get("est")]
        return max([1.0, *ratios])

    # --- jobs ----------------------------------------------------------------
    def estimate(self, cid, device, options=None, pauli_sum=None):
        return self.backend.estimate(cid, device, options, pauli_sum)

    def run(self, cid, device, options=None, pauli_sum=None, timeout=None, tag=None, circuit=None):
        key = config_key(cid, device, options, pauli_sum, circuit)
        target = cid if circuit is None else circuit
        with self._lock:
            r = self.state.get(key)
            if r and r["event"] == "completed":
                return r["value"]
            outstanding = bool(r) and r["event"] in ("committed", "submitted")
            if not outstanding:
                self._commit(key, cid, device, options, pauli_sum, tag, r, target)
        if outstanding:
            return self._wait(key, timeout)
        return self._submit(key, target, device, options, pauli_sum, timeout)

    def _commit(self, key, cid, device, options, pauli_sum, tag, r, target=None):
        if r and r.get("attempt", 0) > RETRIES:
            raise JobFailed(f"{cid} {device} already failed {r['attempt']} times: {r.get('error')}")
        est = self.backend.estimate(cid if target is None else target, device, options, pauli_sum)
        reserve = est * self._overrun(device)
        if self.spent() + reserve > self.cap + 1e-9:
            raise BudgetExceeded(f"{cid} {device} needs ${reserve:.2f}, remaining ${self.remaining():.2f}")
        self._append({"key": key, "event": "committed", "cid": cid, "device": device,
                      "options": options, "pauli_sum": pauli_sum, "est": est,
                      "est_reserved": reserve, "tag": tag, "attempt": (r or {}).get("attempt", 0) + 1})

    def _submit(self, key, cid, device, options, pauli_sum, timeout):
        last = None
        for _ in range(RETRIES + 1):
            try:
                job_id, quote = self.backend.submit(cid, device, options, pauli_sum, key)
                break
            except Exception as e:  # network or platform refusal; nothing was charged
                last = e
                time.sleep(self.poll)
        else:
            self._append({"key": key, "event": "failed", "cost": 0.0, "error": str(last)})
            raise JobFailed(str(last))
        self._append({"key": key, "event": "submitted", "job_id": job_id, "quote": quote})
        self._apply_quote(key, quote)
        return self._wait(key, timeout)

    def _apply_quote(self, key, quote):
        """Raise the reservation to the platform's submit-time quote; cancel at once if that crosses the cap."""
        with self._lock:
            r = self.state[key]
            # user-approved 2026-10-25 10:22 ET: CPU pauli-path is always quoted $25 but has cost $0 in every run;
            # keep its estimate as the reservation. The cap on actual charges still applies.
            if quote <= r.get("est_reserved", 0.0) or r.get("device") == "pauli-path":
                return
            if self.spent() - r.get("est_reserved", 0.0) + quote <= self.cap + 1e-9:
                self._append({"key": key, "event": "submitted", "est_reserved": quote})
                return
        self.backend.cancel(r["job_id"])
        j = self.backend.get(r["job_id"])
        self._append({"key": key, "event": "failed", "cost": j["cost"],
                      "error": f"cancelled: submit quote ${quote:.2f} would cross the cap ({j['status']})"})
        raise BudgetExceeded(f"{r['cid']} {r['device']} quoted ${quote:.2f} at submit; cancelled")

    def _wait(self, key, timeout):
        start = time.time()
        while True:
            v = self._reconcile(key)
            if v is not None:
                return v
            if timeout is not None and time.time() - start > timeout:
                raise JobPending(self.state[key].get("job_id"))
            time.sleep(self.poll)

    def _reconcile(self, key):
        """Refresh one outstanding job. Returns its value once completed, None while pending."""
        r = self.state[key]
        if r["event"] == "completed":
            return r["value"]
        if r["event"] == "committed":  # crashed between commit and submit: was it sent?
            hit = self.backend.find_by_name(key, since=r["t"] - 120)
            if hit is None:
                self._append({"key": key, "event": "failed", "cost": 0.0, "error": "never submitted"})
                raise JobFailed("never submitted; rerun to retry")
            self._append({"key": key, "event": "submitted", "job_id": hit["job_id"]})
        j = self.backend.get(self.state[key]["job_id"])
        if j["status"] in PENDING:
            return None
        if j["status"] == "COMPLETED":
            self._append({"key": key, "event": "completed", "value": j["value"], "cost": j["cost"]})
            return j["value"]
        self._append({"key": key, "event": "failed", "cost": j["cost"], "error": f'{j["status"]}: {j["error"]}'})
        raise JobFailed(f'{j["status"]}: {j["error"]}')

    def reconcile_all(self):
        """Resume: settle every outstanding job in the ledger. Returns {key: value|None|error}."""
        out = {}
        for key, r in list(self.state.items()):
            if r["event"] in ("committed", "submitted"):
                try:
                    out[key] = self._reconcile(key)
                except JobFailed as e:
                    out[key] = f"failed: {e}"
        return out

    def run_many(self, specs, timeout=None):
        """specs: list of dicts of run() kwargs. Bounded concurrency; returns values or exceptions in order."""
        def one(s):
            try:
                return self.run(timeout=timeout, **s)
            except Exception as e:
                return e
        with ThreadPoolExecutor(CONCURRENCY) as ex:
            return list(ex.map(one, specs))


class Proxy:
    """What strategy code is allowed to see."""

    def __init__(self, controller):
        self.__c = controller

    def estimate(self, cid, device, options=None, pauli_sum=None):
        return self.__c.estimate(cid, device, options, pauli_sum)

    def run(self, cid, device, options=None, pauli_sum=None, timeout=None, tag=None, circuit=None):
        return self.__c.run(cid, device, options, pauli_sum, timeout, tag, circuit)

    def run_many(self, specs, timeout=None):
        return self.__c.run_many(specs, timeout)

    def get(self, cid, device, options=None, pauli_sum=None, circuit=None):
        """Ledger record for a config, or None."""
        return dict(self.__c.state.get(config_key(cid, device, options, pauli_sum, circuit)) or {}) or None

    @property
    def remaining(self):
        return self.__c.remaining()
