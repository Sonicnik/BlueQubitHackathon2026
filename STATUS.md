# Status

Updated 2026-10-24, ~1:45 p.m. ET. Target: G2 and G4 (see PLAN.md). Spend so far: **$0.00** of $27. Outstanding jobs: none.

## Candidates ready to submit

| File | Method | Proxy accuracy (same remote method on a sample with exact answers) | Cost | Confidence |
|---|---|---|---|---|
| `candidates/G2_v1.csv` (+ `.md` note) | mps.cpu, χ=32 | S2 (16-q chain): corr² 1.0000, MAE 0.0009 | $0.00 | Moderate. Same family, but G2 is 36 q and 18 layers, so the truncation error is larger and unmeasured. The profile looks physical: ~0 near butterfly 18, rising to ~1 at the chain ends. |
| `candidates/G4_v1.csv` (+ `.md` note) | mps.cpu, χ=32 | S3 (30-q grid, Clifford+Rz): corr² 0.43, MAE 0.26 | $0.00 | **Low.** Values reach 0.96, but the challenge says G4's true values are mostly within ±0.1. MPS isn't converged on the grid. Submit only as an early placeholder. |

Both pass `evaluate.py validate`. Job IDs are in each `.md` note and in `ledger/jobs.jsonl`. Agreement between approximations is not accuracy; these are single-rung estimates.

## Findings that change the plan

- MPS and Pauli-path jobs at these sizes have **cost $0.00** in practice (82 jobs so far), even though `estimate` says $0.20 to $0.91 per ID. The submit-time quote for MPS was also $0.00.
- Pauli-path at 1e-3 returned exactly 0.0 on G4, and its submit-time quote was $25 / 100 h. It's unused until the controller fix in QUESTIONS.md #2 is decided.
- Remote MPS χ=32 is far better than local qiskit-aer MPS at the same χ on S2 (corr² 1.00 vs 0.96). Local MPS is a pessimistic proxy for the remote one.

## Next (Phase 3 and the loop)

1. G4 is the priority (1,000 pts, low confidence). Probe whether larger χ (64, 128, 256) is still free and finishes. Check convergence on S3 and on Haar-grid surrogates.
2. G2: a χ=64 rung to confirm convergence (expected free).
3. Build the Phase 3 surrogates (Haar chain and Haar grid at exact-solvable sizes) and the `evaluate.py benchmark` command.
