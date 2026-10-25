# Status: final handover

Updated 2026-10-25, 10:05 a.m. ET (freeze 10:30, submissions close 11:30). Spend: **$8.20 actual** of the $27 cap (GPU jobs at $0.20; every CPU job was $0). Outstanding jobs: none.

## Submit these

| Problem | File | Method note (paste the first paragraph) | Evidence | Confidence |
|---|---|---|---|---|
| G2 | `final/G2.csv` (= `candidates/G2_v2.csv`) | `final/G2.md` | mps.cpu chi=128. The 30-q Haar-chain surrogate scored corr2 0.73 / 0.87 / 0.96 at chi 32 / 64 / 128; v1 (chi=32) scored 342/600 on the platform. corr(v1, v2) = 0.94, with the transition region sharpened. | Moderate to good. Should beat 342; 600 is not assured. |
| G4 | `final/G4.csv` (= `candidates/G4_v3.csv`) | `final/G4.md` | pauli-path.gpu, threshold 3e-4, transpilation level 3. 12 of 38 IDs are exactly 0; the rest are within ±0.06, matching G4's stated regime. Level 2 gave all zeros; MPS (chi 32-256) stuck at 0.5-0.6 and v1 scored 0/1000. | Low. Partial signal only; it has not been scored against exact values on a G4-hard surrogate. |

## Earlier candidates

- `candidates/G2_v1`: scored 342/600. `candidates/G4_v1`: scored 0/1000 (recorded in `ledger/submissions.tsv`).
- `candidates/G4_v2` (mps chi=64) was stopped at 13/38 and never written.

## Not done (time ran out)

- G4 at threshold 1e-4, level 3 (next rung): GPU jobs run one at a time, and the Mac stopped between ~2:40 and 10:00 a.m., so it never ran.
- Scoring the G4 method on `grid4x7` (28 q, 16 layers, exact truth now in `bench/truth/surrogates/grid4x7.json`).
- Open in QUESTIONS.md #1: team and account rules.
