"""The four PLAN.md Phase 1 controller tests, on a fake backend (no network, no spend).

Run: .venv/bin/python -m unittest controller.test_controller -v
"""
import tempfile
import unittest
from pathlib import Path

from controller.client import BudgetExceeded, Controller, JobPending, Proxy


class FakeBackend:
    def __init__(self, cost=1.0, polls_until_done=0, quote=0.0):
        self.cost, self.polls_until_done, self.quote = cost, polls_until_done, quote
        self.jobs, self.submits, self.cancelled = {}, 0, []

    def estimate(self, cid, device, options, pauli_sum):
        return self.cost

    def submit(self, cid, device, options, pauli_sum, name):
        self.submits += 1
        jid = f"job{self.submits}"
        self.jobs[jid] = {"name": name, "polls": 0, "value": 0.5}
        return jid, self.quote

    def cancel(self, job_id):
        self.cancelled.append(job_id)
        self.jobs[job_id]["cancelled"] = True

    def get(self, job_id):
        j = self.jobs[job_id]
        if j.get("cancelled"):
            return {"job_id": job_id, "status": "CANCELED", "cost": 0.0, "value": None, "error": None, "name": j["name"]}
        j["polls"] += 1
        done = j["polls"] > self.polls_until_done
        return {"job_id": job_id, "status": "COMPLETED" if done else "RUNNING", "cost": self.cost if done else 0.0,
                "value": j["value"] if done else None, "error": None, "name": j["name"]}

    def find_by_name(self, name, since):
        assert isinstance(since, (int, float))  # controller passes epoch seconds; BQBackend converts for the SDK
        for jid, j in self.jobs.items():
            if j["name"] == name:
                return {"job_id": jid}
        return None


class ControllerTests(unittest.TestCase):
    def setUp(self):
        self.ledger = Path(tempfile.mkdtemp()) / "jobs.jsonl"

    def ctl(self, fb, cap=27.0):
        return Controller(backend=fb, ledger=self.ledger, cap=cap, poll=0)

    def test_cap_refuses_over_cap_request(self):
        fb = FakeBackend(cost=10.0)
        c = self.ctl(fb, cap=25.0)
        c.run("A", "cpu")
        c.run("B", "cpu")
        with self.assertRaises(BudgetExceeded):
            c.run("C", "cpu")
        self.assertEqual(fb.submits, 2)
        self.assertAlmostEqual(c.remaining(), 5.0)

    def test_inflight_jobs_count_against_cap(self):
        fb = FakeBackend(cost=10.0, polls_until_done=10**9)
        c = self.ctl(fb, cap=25.0)
        for cid in "AB":
            with self.assertRaises(JobPending):
                c.run(cid, "cpu", timeout=0)
        with self.assertRaises(BudgetExceeded):
            c.run("C", "cpu", timeout=0)

    def test_killed_process_resumes_from_ledger(self):
        fb = FakeBackend(polls_until_done=10**9)
        with self.assertRaises(JobPending):
            self.ctl(fb).run("A", "mps.cpu", {"mps_bond_dimension": 64}, timeout=0)
        # "kill": drop the controller, start a fresh one on the same ledger
        fb.polls_until_done = 0
        c2 = self.ctl(fb)
        self.assertEqual(c2.reconcile_all(), {next(iter(c2.state)): 0.5})
        self.assertEqual(c2.run("A", "mps.cpu", {"mps_bond_dimension": 64}), 0.5)
        self.assertEqual(fb.submits, 1)

    def test_committed_but_unsent_job_is_found_by_name(self):
        fb = FakeBackend()
        c = self.ctl(fb)
        c._commit("k-placeholder", "A", "cpu", None, None, None, None)  # crash right after commit
        key = "k-placeholder"
        fb.jobs["jobX"] = {"name": key, "polls": 0, "value": 0.25}  # it did reach the platform
        self.assertEqual(self.ctl(fb).reconcile_all(), {key: 0.25})

    def test_repeated_config_returns_cached_result(self):
        fb = FakeBackend()
        p = Proxy(self.ctl(fb))
        self.assertEqual(p.run("A", "cpu", pauli_sum=[("IZ", 1.0)]), 0.5)
        self.assertEqual(p.run("A", "cpu", pauli_sum=[("IZ", 1.0)]), 0.5)
        self.assertEqual(self.ctl(fb).run("A", "cpu", pauli_sum=[("IZ", 1.0)]), 0.5)  # also across restarts
        self.assertEqual(fb.submits, 1)
        p.run("A", "cpu", pauli_sum=[("ZI", 1.0)])  # different config is a new job
        self.assertEqual(fb.submits, 2)

    def test_outstanding_job_reconciled_after_timeout(self):
        fb = FakeBackend(cost=2.0, polls_until_done=3)
        c = self.ctl(fb)
        with self.assertRaises(JobPending):
            c.run("A", "gpu", timeout=0)
        self.assertAlmostEqual(c.remaining(), 25.0)  # estimate reserved while in flight
        self.assertEqual(c.run("A", "gpu"), 0.5)  # same config waits on the same job
        self.assertEqual(fb.submits, 1)
        self.assertAlmostEqual(c.remaining(), 25.0)

    def test_low_estimates_tighten_later_reservations(self):
        fb = FakeBackend(cost=1.0)
        c = self.ctl(fb, cap=10.0)
        fb.estimate = lambda *a: 0.5  # platform estimate runs at half the real cost
        c.run("A", "pauli-path")
        fb.polls_until_done = 10**9
        with self.assertRaises(JobPending):
            c.run("B", "pauli-path", timeout=0)
        self.assertAlmostEqual(c.remaining(), 10.0 - 1.0 - 1.0)  # B reserved at 2x its estimate

    def test_own_circuit_keyed_by_content(self):
        from qiskit import QuantumCircuit
        fb = FakeBackend()
        c = self.ctl(fb)
        a, b = QuantumCircuit(2), QuantumCircuit(2)
        b.x(0)
        c.run("sur", "mps.cpu", circuit=a)
        c.run("sur", "mps.cpu", circuit=a)
        self.assertEqual(fb.submits, 1)
        c.run("sur", "mps.cpu", circuit=b)  # same name, different circuit: new job
        self.assertEqual(fb.submits, 2)

    def test_submit_quote_over_cap_cancels_job(self):
        fb = FakeBackend(cost=0.2, quote=25.0)  # estimate_only says $0.20, the platform quotes $25 at submit
        c = self.ctl(fb, cap=10.0)
        with self.assertRaises(BudgetExceeded):
            c.run("G4", "pauli-path")
        self.assertEqual(fb.cancelled, ["job1"])
        self.assertAlmostEqual(c.remaining(), 10.0)  # cancelled at $0, reservation released

    def test_submit_quote_raises_reservation(self):
        fb = FakeBackend(cost=0.2, quote=3.0, polls_until_done=10**9)
        c = self.ctl(fb, cap=10.0)
        with self.assertRaises(JobPending):
            c.run("G4", "pauli-path", timeout=0)
        self.assertEqual(fb.cancelled, [])
        self.assertAlmostEqual(c.remaining(), 7.0)  # reserved at the $3 quote, not the $0.20 estimate

    def test_proxy_hides_controller(self):
        p = Proxy(self.ctl(FakeBackend()))
        self.assertFalse(hasattr(p, "backend") or hasattr(p, "bq"))


if __name__ == "__main__":
    unittest.main()
