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

## Phase 2 (2026-10-24, ~1:15 to 1:45 p.m. ET)

- Probes: G2_0 mps.cpu χ=32 gave 0.9996, G4_0 mps.cpu χ=32 gave 0.270, and G4_0 pauli-path 1e-3 gave exactly 0.0. All cost $0.00 and finished in under 48 s. The submit-time quote was $0.00 for MPS but **$25.00 and 100 h allowed** for pauli-path (QUESTIONS.md #2).
- Baselines: G2 and G4 at mps.cpu χ=32, 74 jobs, all $0.00. CSVs are in `candidates/`.
- Proxy check of the same remote method: S2 corr² 1.0000 (MAE 9e-4), S3 corr² 0.43 (MAE 0.26). The grid is where MPS fails.
- Local qiskit-aer MPS (installed qiskit-aer 0.18.0 in `.venv`) on S2: corr² 0.36 / 0.85 / 0.84 / 0.96 / 0.999 at χ = 4 / 8 / 16 / 32 / 64. On the 30-qubit S3 it crashed with a BLAS `zgemm` parameter error.
- `estimate_only` costs are not what's charged. They read high for MPS and low for pauli-path relative to the submit-time quote.

## Phase 3 (2026-10-24, ~1:55 to 2:15 p.m. ET)

- `bench/surrogates/gen.py`: Haar 2q echo circuits compiled to u3+cz, with the same echo order as the kit. Inverse cancellation is asserted on each generated U.
  - `chain20`: 20 q, 10 layers, butterfly 10; mirrors G2's L = n/2 with a mid-chain butterfly.
  - `grid4x5`: 20 q, 10 layers, butterfly 0. 16 layers on a 4×5 grid scrambles every value to ≤0.006, so 10 layers puts it in G4's regime (std 0.08, 80% within ±0.1).
  - Exact truth comes from local Aer statevector and lives in `bench/truth/surrogates/` (locked again).
- `evaluate.py benchmark` runs `strategy.estimate` remotely through the controller on the surrogates (remote MPS behaves differently from local), then scores corr² and MAE. First run took ~3 min at $0.00; cached reruns take ~2 s.
- **Protected-file changes made for Phase 3:**
  - `evaluate.py` gained the `benchmark` command.
  - `controller/client.py` now takes `circuit=` (our own QuantumCircuit), keyed by a QASM hash. One new test, 9/9 pass.
  - Everything is locked read-only again.
- `strategy/checks.py` (program.md step 3) checks qubit mapping, a known S1 expectation and inverse cancellation. It passes.
- Baseline benchmark (strategy v1, mps.cpu χ=32): chain20 corr² 0.985 (MAE 0.030), grid4x5 corr² 0.129 (MAE 0.216). Logged in `results.tsv`.
- Caveat: surrogates are 20 q against 36 to 38 q on G. Benchmark gains are evidence, not proof, for G.

## Phase 4, H0 (2026-10-24, ~2:35 to 2:55 p.m. ET)

- Platform scores reported by the user: G2_v1 342/600 (corr² 0.57) and G4_v1 0/1000. Recorded in `ledger/submissions.tsv`. The chain20 proxy (0.985) overstated G2.
- **Controller fix (approved, QUESTIONS.md #2):** `BQBackend.submit` now returns the submit-time `estimated_cost`. `Controller._apply_quote` raises the reservation to that quote. If the quote would cross the cap, it cancels the job, records the real cancelled cost and raises `BudgetExceeded`. There's a new `BQBackend.cancel`, and two tests (11/11 pass). The controller is locked again.
  - Consequence: a $25 Pauli-path quote reserves $25, so only one such job can be in flight under the $27 cap.
- **New surrogate `grid4x6`:** 24 q, Haar, 10 layers, butterfly 0. Values std ≈ 0.08, 86% within ±0.1. Exact truth (local Aer) is in `bench/truth/surrogates/grid4x6.json`. This was a one-time unlock to add the file; it's locked again.
  - 12 layers give values identical to 10, because the extra layers never touch qubit 0 and cancel in U† X₀ U. Expect the same depth saving on G4 (butterfly 0).
- Benchmark (strategy v1, mps.cpu χ=32): chain20 0.985, grid4x5 0.129, **grid4x6 0.472** (MAE 0.300). 24 jobs, $0, max submit quote $0.
- MPS χ probe on G4_0: 0.270 / 0.098 / 0.058 at χ = 32 / 64 / 128. Values shrink toward G4's ±0.1 regime as χ grows. All $0.
