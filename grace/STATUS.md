# STATUS

Last updated: 2026-10-24 12:58 — S1, S2, S3 CSVs ready; G1 exact finishing; G2/G3/G4 running (all jobs $0 so far).

## Spend
Total: **$0.00** / $27 (credits $30). Server audit (`python audit.py`) agrees: $0.00.
| group | spent | cap |
|-------|-------|-----|
| samples | $0.00 | $2 |
| G1 | $0.00 | $8 |
| G2 | $0.00 | $6 |
| G3 | $0.00 | $6 |
| G4 | $0.00 | $5 |
Every probe so far (cpu 30q, pauli-path 30–38q, mps.cpu chi=64) cost $0.00.
Note: pauli-path jobs report estimated_cost $25 (= 100 h allowed runtime); billing is on actual runtime. run.py `--max-runtime` cancels long jobs.
Account limit: max 5 concurrent jobs per tier (HACKATHON_PARALLEL_JOBS_LIMIT) — run.py requeues and waits.

## CSVs
| C | ready | method / progress |
|---|-------|-------------------|
| S1 | YES | exact cpu by ID; matches local qiskit Statevector to 1e-7 (ordering confirmed) |
| S2 | YES | exact cpu by ID |
| S3 | YES | exact cpu by ID (30/30). Reference: pauli-path 1e-3 corr2 = 0.78 vs exact |
| G1 | no | cpu exact 18/30, filling |
| G2 | no | mps.cpu chi=64 14/36 (22 rejected NOT_ENOUGH_FUNDS, refilling); chi=128 probe q18 = -0.0030 |
| G3 | no | pauli-path 1e-3 = 0.0 on all 36 (would score 0); 1e-4 q14 = 0.0 too. Probing 1e-5 and mps.cpu chi=64 |
| G4 | no | mps.cpu chi=64 probe q0 = 0.0978 (190 s, $0) -> full pass running; pauli-path 1e-4 q0 = 0.0 |

## Log
- INFRA: ledger.py, run.py, make_csv.py, compare.py, local_exact.py, audit.py. n = 4,16,30,30,36,36,38 confirmed.
- Phase 1: S1 exact cpu == local qiskit; S2 exact cpu 16/16. S1.csv, S2.csv written.
- Phase 2: G1 cpu probe $0.00, 59 s -> running all 30 exactly.
- Phase 3: S3 cpu probe $0.00, 55 s -> running all 30 exactly.
  - S3 pauli-path calibration vs exact (19 qubits so far): 1e-2 corr undefined (all ~0), 1e-3 corr2 = 0.50 (5 s/job), 1e-4 probe q0 0.1358 vs exact 0.1441 (80 s). Pauli-path is weak on S3; exact cpu is the S3 answer.
  - G3 pauli-path 1e-3 probe q0: 0.0, 12 s, $0. Full 1e-3 running; 1e-4 probe on q14 next.
- Phase 4: MPS validation on S2 vs exact: chi=64 corr2 = 1.0000 (max diff 3e-7); chi=16 corr2 = 0.989.
  - G2 mps.cpu chi=64 probe q18: -0.0079, 77 s, $0. Full chi=64 running; chi=128 probe next.
- Phase 5 prep: G4 pauli-path 1e-3 probe q0: 0.0, 13 s, $0 (too coarse for Haar). mps.cpu chi=64 and pauli-path 1e-4 probes queued.
- One G2 mps probe (job eyaryM0CsuHos5DQ, 12:42) came from this session's pre-fork branch; resumed and recorded, $0.

- 12:58 WARNING: 22 G2 mps.cpu chi=64 submissions were rejected at submit with NOT_ENOUGH_FUNDS: "too large for the free tier ... recommend a balance of at least $10". Not charged. Rejections come in time clusters, so the gate looks intermittent. run.py now pauses 60 s and requeues (max 4 tries per qubit). The message suggests the account may be on the free tier rather than holding $30 credits.
- S3.csv written (exact). G3 pauli-path at 1e-3/1e-4 returns exactly 0.0, so G3 needs a finer threshold or MPS.

## Next
Write G1.csv when cpu exact finishes; G3: read the 1e-5 / mps chi=64 probes on q14 and pick a method; G2: finish chi=64 pass -> G2.csv, then ladder 128/256/512; G4: finish chi=64 pass -> G4.csv, then a higher chi.
