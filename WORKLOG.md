# Work log: DuQuHack autoresearch (G2 and G4)

What was built, run, found and decided, in order. Raw details are in `NOTES_RUN.md` (run notes), `results.tsv` (experiments), `ledger/jobs.jsonl` (every platform job), `ledger/submissions.tsv` (platform scores) and `STATUS.md` (current state). Times are ET.

## Outcome

| Problem | Best file | Method | Platform score |
|---|---|---|---|
| G2 | `final/G2.csv` (= `candidates/G2_v2.csv`) | mps.cpu, bond dimension 128 | v1 (χ=32) scored 342/600; v2 score not recorded here |
| G4 | `candidates/G4_v3.csv` (= `final/G4.csv`) | pauli-path.gpu, threshold 3e-4, transpilation level 3 | **267/1000** |
| G4 | `candidates/G4_v4.csv` | same at threshold 1e-4 | 136/1000 |
| G4 | `candidates/G4_v1.csv` | mps.cpu, bond dimension 32 | 0/1000 |

Spend: about $16.60 actual before the `grid4x7` test (below), which adds up to about $11.20. The cap is $30, raised from $27 by the user on Oct 25.

---

## Oct 24: build

### Phase 0: environment (~12:50 p.m.)
- Python 3.11.7, bluequbit 0.19.0b1, qiskit 2.6.1, numpy 2.4.6. Mac: 16 GB RAM, 10 cores.
- Four free S1 `cpu` jobs matched local exact values to ~2e-7, which confirms qubit order (q0 is the rightmost Pauli character).
- `get_circuit_info` and `estimate` are free. `estimate()` drops options, but the same endpoint (`jobs.submit_jobs(..., estimate_only=True)`) accepts bond dimension, threshold and `pauli_sum`.
- `cpu` statevector runs up to 34 qubits and is free at 30. `cpu` and `gpu` refuse 36 and 38 qubits, so G2 to G4 need MPS or Pauli-path.
- The token was set in the general shell, not only the controller's. This was noted and mitigated.

### Phase 1: protected infrastructure
- `controller/client.py`: the only holder of the token.
  - Enforces the cap, counting in-flight reservations, at concurrency 4 with at most 2 retries.
  - Caches repeated configs and resumes from the ledger after a crash or timeout.
  - Strategy code sees only a `Proxy`.
- `controller/test_controller.py`: unit tests on a fake backend. 12 pass now.
- `evaluate.py`: corr² (platform rule), MAE, a CSV validator against `kit/problems.json`, `selfcheck`, and later `benchmark`.
- Exact references:
  - S1 and S2 by local statevector (`bench/make_truth.py`).
  - S3 (30 q) from 30 free remote `cpu` jobs (`bench/remote_truth.py`). Local was impossible: 16 GiB of memory, and 308 non-Clifford gates rule out stabilizer methods.
- Protected paths set read-only. Pushed to GitHub as `e4b4bd2`, merged as `861a1ad`. A rebase failed on the read-only files and was recovered without loss.

### Target change
The user narrowed the work to G2 and G4 on a $27 budget, because a teammate covered the other problems. The team and account rules question went into `QUESTIONS.md` #1 and is still open.

### Phase 2: baselines
- Probes:
  - G2_0 at mps.cpu χ=32 gave 0.9996, and G4_0 at mps.cpu χ=32 gave 0.270.
  - G4_0 on Pauli-path at 1e-3 gave exactly 0.0, with a **$25 quote at submit** against the $0.20 estimate.
- `candidates/G2_v1` and `G4_v1`: mps.cpu χ=32, 74 jobs, $0.
- The same method on the samples: S2 corr² 1.00, S3 (grid) 0.43. Pushed as `8cd6a46`.

### Phase 3: surrogate benchmark
- `bench/surrogates/gen.py`: Haar echo circuits compiled to u3+cz, in the kit's echo order, with an inverse-cancellation check.
  - `chain20`: 20 q, 10 layers, butterfly 10.
  - `grid4x5`: 20 q, 10 layers, butterfly 0. 16 layers scrambled every value to ≤0.006.
- `evaluate.py benchmark` runs the strategy remotely on the surrogates. The controller was extended to accept our own circuits.
- `strategy/checks.py`: qubit mapping, a known S1 value, and inverse cancellation.
- Baseline: chain20 corr² 0.985, grid4x5 0.129. Pushed as `8570f5b`.

### Platform feedback (user-submitted)
G2_v1 scored 342/600 (corr² 0.57) and G4_v1 scored 0/1000. The chain20 proxy had overstated G2.

### Phase 4, H0
- **Controller fix (approved):** the controller reads the platform's submit-time quote, raises the reservation to it, and cancels any job that would cross the cap. Two tests.
- **`grid4x6`:** 24 q, 10 layers. 12 layers gave identical values, because layers that miss the butterfly qubit cancel in U† X U. MPS χ=32 corr² 0.47. Pushed as `611d253`.
- MPS χ ladder on G4_0: 0.270 / 0.098 / 0.058 at χ = 32 / 64 / 128.
- Paper check: four arXiv sources exist and match, and the Nature PDF is in `paper/`. Notes are in `NOTES_RUN.md`.

### H1 and H3 calibration
- Pauli-path (CPU, level 2) on grid4x5: corr² 0.684 at 3e-4 and 0.684 at 1e-4.
- MPS χ=64: grid4x5 0.28, grid4x6 0.61.
- Platform limit found: **at most 5 small jobs at once**.
- `chain30`: 30 q, 15 layers, butterfly 15, with exact answers from free remote `cpu`. A 30-q local check was stopped before it could exhaust memory.

### G4 pilot and fixes
- Pauli-path 3e-4 (level 2) on G4 IDs 0, 21 and 37: all exactly 0.0. 1e-4 on G4_0: 0.0. The grid4x5 proxy was too easy.
- **Controller bug fixed:** crash recovery passed a float to `bq.search`. It's now a UTC datetime, verified on the real SDK.
- G4_v2 (mps χ=64) was stopped at 13/38, because it correlated 0.90 with v1, which scored 0.
- mps.gpu χ=256 (the first paid jobs, $0.20 each): G4_0 0.030, but G4_4 0.556 and G4_11 0.615, stuck far outside ±0.1. **MPS abandoned for G4**, consistent with arXiv 2604.15427.

## Oct 25: G2 finish, G4 work

### G2
- chain30 ladder: corr² 0.727 / 0.873 / 0.9625 at χ = 32 / 64 / 128.
- `candidates/G2_v2`: mps.cpu χ=128, 36 jobs, $0. It correlates 0.936 with v1, with a sharper transition region. The user then said G2 was done.

### G4 breakthrough: transpilation level 3
- From the teammate's analysis: `pauli_path_circuit_transpilation_level=3` removes gates outside the butterfly's light cone. Every earlier Pauli-path job had used the default level 2.
- Pilot on pauli-path.gpu at 3e-4, level 3: G4_0 0.0036, G4_21 0.0, G4_37 0.0236. Quote $0.67, cost $0.20, under a minute each.
- **`candidates/G4_v3`:** all 38 IDs, 12 exactly 0, max |v| 0.055. **Scored 267/1000.**
- Platform limit found: **only one GPU job at a time.**
- `grid4x7`: 28 q, G4's 16 layers, corner butterfly. Exact truth computed locally in single precision, about an hour.
- The Mac stopped running between about 2:40 and 10:00 a.m., probably asleep with the lid closed. Planned 1e-4 work was lost.
- Final handover at 10:05: `final/G2.csv` and `final/G4.csv`, pushed as `0263849`.

### After the handover
- The CPU Pauli-path quote was exempted from the guard (user-approved) and the cap raised to $30. But CPU Pauli-path on G4 was then **refused by the platform: "NOT_ENOUGH_FUNDS … please top up"**. It's a paid-balance feature, so G4 Pauli-path is GPU-only and serial.
- **`candidates/G4_v4`:** pauli-path.gpu at 1e-4, level 3, all 38 IDs. Zeros fell from 12 to 4 and the spread went from 0.014 to 0.028. It correlates 0.892 with v3, with several sign flips. **Scored 136/1000**, lower than v3. Pushed as `a2e3d51`.
- v5 trial with weight cutoff 12: G4_0 was identical to v3 to every digit, and at 84 s per job it couldn't finish before 11:30. Stopped after 1 ID.
- Research: Pauli-path truncation error is **non-monotonic** in the threshold (arXiv 2507.10771). That explains how a finer threshold can score lower. Truncated Pauli-path methods are known to struggle on OTOC(2).
- **Running now:** a test fixed in advance (`results.tsv`, 11:05). On `grid4x7` with exact answers it scores pauli-path.gpu level 3 at 3e-4, at 1e-4, and the mean of the two standardized vectors. The best of the three decides G4_v5 (`strategy/ensemble_eval.py`). It's 56 GPU jobs, about 2 minutes each, finishing around 1:15 p.m.

### Declined
Using Chrome to upload variants to a second account and iterate on the scores. That's tuning against hidden answers ("probing"), which the competition rules disqualify for and AGENTS.md forbids. The rules also allow only one account per entrant. Not done unless the organizers confirm in writing.

### Presentation
`presentation/script.md`: a 7-minute, 8-slide script with blanks for the G2_v2 score, the grid4x7 result and final spend.

---

## Lessons

1. Validate the proxy against reality before trusting it: chain20 said 0.985 where real G2 was 0.57.
2. Platform limits shape everything: 5 small jobs at a time, 1 GPU job at a time, submit quotes far above estimates, and CPU Pauli-path behind a top-up.
3. For echo circuits, cancelling gates outside the light cone (level 3) mattered more than precision.
4. A finer threshold is not automatically better, so test it against exact answers.
5. Keep the machine awake: a sleeping laptop cost about 7 hours.

## Open items
- `QUESTIONS.md` #1: team and account rules. G4's level-3 setting came from the teammate's analysis.
- The grid4x7 test result, and G4_v5 if the standardized mean wins.
