# Questions for the user

## Open

1. **Team status and account (asked 2026-10-24, ~1:30 p.m. ET).** A teammate is running the same problems and sharing results through `grace/` in the repo. AGENTS.md says online entrants compete alone and that any result sharing disqualifies them. An in-person team may use only one account and one budget ("no extra accounts"). Your instruction for now: assume $27 on your own account, for G2 and G4. Until this is settled, this loop **does not read or use `grace/`** (it isn't pulled locally) and computes its own exact references for S1 to S3. Please confirm that you're a declared in-person team, and whether two accounts is allowed (rhik@bluequbit.io, Discord #duke-2026).

2. **Controller gap: submit-time cost quote (found 2026-10-24, ~1:20 p.m. ET).** The controller reserves the `estimate_only` cost before submitting. For Pauli-path that was $0.20, but the platform's quote at submission was **$25.00 with 100 h allowed runtime** (job RVY2LylDiQ8iFc7i, G4 at 1e-3). The job ended in under a minute at $0.00, but a long Pauli-path job could have charged up to $25. For MPS it went the other way: the estimate said $0.27 to $0.30 and the submit quote and actual cost were both $0.00.
   - Proposed fix to `controller/client.py` (a protected file, so it's your call): after submitting, read the job's submit-time `estimated_cost`. Raise the reservation to it, and cancel the job at once if that would cross the cap. About 10 lines plus one test.
   - Meanwhile the strategy uses no Pauli-path jobs.
