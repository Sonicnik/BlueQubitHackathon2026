# Run notes

## Phase 0 (2026-10-24, ~12:50 p.m. ET)

Raw outputs: `scripts/phase0_out.json`, `scripts/phase0_est_out.json`. Scripts: `scripts/phase0.py`, `scripts/phase0_est.py`.

### Versions (Mac, 16 GB RAM, 10 cores)

Python 3.11.7 (`.venv`), bluequbit 0.19.0b1, qiskit 2.6.1, numpy 2.4.6.

### S1 free job vs local exact (qubit order confirmed)

`pauli_sum` string `"I"*(n-1-q) + "Z" + "I"*q` (q0 rightmost). Local value: qiskit `Statevector` of `kit/samples/S1/Duke_S1_{q}.qasm`.

| q | local exact | remote `cpu` | job | cost |
|---|---|---|---|---|
| 0 | -0.3621922 | -0.3621923 | zWzRl9Xh1gjur3od | $0.00 |
| 1 | -0.2326674 | -0.2326674 | gwL8L8uBC5BYtZHS | $0.00 |
| 2 | 0.1025039 | 0.1025041 | kuXXN3EII7ensu07 | $0.00 |
| 3 | -0.1093710 | -0.1093709 | GUmCsQ1juqGHfDFw | $0.00 |

Agreement ~2e-7 (remote looks single precision).

### Circuit info (free) and estimates (free)

`get_circuit_info` and `estimate` cost nothing and need no job. `estimate(id, device)` takes no options; the same POST `/jobs` with `estimate_only=True` (SDK `bluequbit.api.jobs.submit_jobs`) does accept `options` and `pauli_sum`. Server returns cents; the SDK divides by 100.

| Circuit | n | CZ | depth_2q | cpu | gpu | mps.cpu χ=64 | pauli-path (any threshold) |
|---|---|---|---|---|---|---|---|
| S3 | 30 | 1568 | 128 | **$0.00**, est 90 s | $0.20, 8 s | $0.39 | $0.20 (runtime est "100 ms", a placeholder) |
| G1 | 30 | 5568 | 384 | **$0.00**, est 218 s | $0.20, 14 s | — | — |
| G2 | 36 | 3780 | 216 | refused (>34 q) | refused (36 q) | — | — |
| G3 | 36 | 2872 | 192 | refused | refused | — | — |
| G4 | 38 | 3024 | 192 | refused | refused | $0.79 | $0.20; pauli-path.gpu $0.67 |

More MPS (per ID): S3 mps.cpu χ=512 $14.80; mps.gpu χ=512 $10.39; G4 mps.gpu χ=512 $21.06. No-option MPS estimates ($4 to $13) are at the default χ. MPS cost scales roughly χ³ and is unaffordable above χ≈64 for 110 G IDs.

### Plan limits and GPU

- GPU: `estimate(device="gpu")` is accepted (no plan error) for ≤34-ish qubits; refused for 36 and 38 qubits on size, not plan. Not yet confirmed by a real run.
- cpu statevector accepts up to 34 qubits and is estimated free at 30 qubits. If a real run confirms $0.00, S3 and G1 are exactly solvable for free.
- SDK constants: queued CPU jobs limit 10, max 50 jobs per `run`, MPS χ max 2048 (cpu) / 4000 (gpu), 2q-gate limits mps.cpu 10,000 and pauli-path 6,000. Terminal states include `HACKATHON_PARALLEL_JOBS_LIMIT` and `HACKATHON_GPU_QUOTA_COOLDOWN`.
- No balance endpoint in the SDK. Spend is tracked from the ledger and `job.cost`; `bq.search()` lists our jobs for reconciliation.
- Hybrid machine time limit: not checked (the loop runs on the Mac).

### Differences from the docs

- `BLUEQUBIT_API_TOKEN` is set in the agent's general shell, not only the controller shell. The controller will be the only code that calls `bluequbit.init()`; strategy code gets a proxy object.
- `estimate` gives no useful Pauli-path runtime (flat "100 ms", flat $0.20 CPU / $0.67 GPU). The real Pauli-path cost is unknown until one run.
- Budget arithmetic: 110 IDs on G2 to G4 at the $0.20 Pauli-path minimum is $22 for one rung. Two rungs on all of them don't fit in $27.

## Phase 1 (2026-10-24, ~1:00 p.m. ET)

- `controller/client.py`: the only `bluequbit.init()` caller. It pops `BLUEQUBIT_API_TOKEN` from `os.environ` after init, so later subprocesses don't inherit it. Strategy code gets `Proxy` (`estimate`, `run`, `run_many`, `get` = ledger record, `remaining`).
  - Cap $27 counts actual cost for terminal jobs plus reserved estimates for committed and in-flight jobs.
  - Reservations are scaled by the worst actual/estimate ratio seen per device, because the Pauli-path estimates look like placeholders.
  - Concurrency 4; at most 2 retries per submit and 3 attempts per config. The job name is the config hash, so a crash between commit and submit can be found with `search`.
- `ledger/jobs.jsonl`: append-only, fsync'd, one line per event.
- `controller/test_controller.py` (stdlib unittest; pytest isn't installed): 8 tests on a fake backend, all passing. They cover the four PLAN.md tests (over-cap refusal, kill and resume, cached repeat, reconcile after timeout), plus in-flight jobs counting against the cap, commit-without-submit recovery, overrun scaling, and the proxy hiding the backend.
- Real adapter check: S1 ×4 through the controller match local exact to 2e-7.
- **30-qubit `cpu` is free in practice:** `Duke_S3_0` completed in ~70 s at $0.00 (job PpPXkKjbFLV5rPXM). S3 truth therefore comes from remote exact statevector (`bench/remote_truth.py`), labelled as such. A local exact S3 isn't feasible: 16 GiB statevector on a 16 GB Mac, and 308 non-Clifford u3 gates per file rule out stabilizer methods.
- `evaluate.py selfcheck | validate | score`: corr² follows the platform rule (0 for negative or undefined correlation). The validator rejects wrong or missing IDs, duplicates, non-finite values and all-equal files.
- S3 references: 30/30 remote exact `cpu` jobs, $0.00 total, values in [-0.81, 1.00]. `evaluate.py selfcheck` gives corr² = 1 on S1, S2 and S3.
- Locked read-only (`chmod -R a-w`): `controller/`, `evaluate.py`, `bench/truth/`, `kit/`. A test write was refused. `ledger/` stays writable for the controller (best effort: same Unix user). Phase 3 must unlock `evaluate.py` and `bench/truth/` once, to add the benchmark command and surrogate truth, then lock them again.
- Target narrowed to G2 and G4 by the user (see PLAN.md). The team and account question is in QUESTIONS.md.
- Ledger total after Phase 1: $0.00 (all jobs free).
