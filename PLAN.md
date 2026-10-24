# Plan: local autoresearch for the BlueQubit Duke challenge

Revised October 24, 2026. Run the phases in order. Each phase ends with a check the agent can run. Rules, spending, and submissions live in [AGENTS.md](AGENTS.md). The challenge contract lives in [CHALLENGE_SUMMARY.md](CHALLENGE_SUMMARY.md). The loop itself lives in [program.md](program.md).

## Goal

Maximize the sum of corr² x points over S1 to S3 (100 each) and G1 to G4 (300, 600, 800, 1000). The event ends Sunday October 25, 11:30 a.m. ET. Freeze at 10:30 a.m. ET. Aim for about 20 hours of unattended refinement after the baseline exists.

**Target change (Oct 24, ~1:30 p.m. ET, user decision):** this loop works on **G2 (600) and G4 (1,000) only**, with the full $27 cap on this account. A teammate's run covers S1 to S3, G1 and G3. S1 to S3 stay here as exact local references for scoring. G3 is optional if time and budget remain.

## Architecture

BlueQubit runs the simulators remotely by ID. Our code runs on the user's Mac.

| Part | Path | Editable by research agent |
| --- | --- | --- |
| Spend controller (the only holder of the token) | `controller/` | no |
| Scorer and exact references | `evaluate.py`, `bench/truth/` | no |
| Job ledger | `ledger/` | no (append through the controller) |
| Strategy | `strategy.py`, `strategy/` | yes |
| Surrogate circuits | `bench/surrogates/` (generator editable, truth not) | generator only |
| Experiment log | `results.tsv`, git history | append |

The strategy decides device and options per circuit, the cost ladder, and post-processing. Its interface:

```python
def predict(circuit: str, client) -> dict[str, float]:
    """Return {circuit_id: estimate} for every ID of the circuit, using client.run / client.estimate only."""
```

`client` is the controller's proxy. It exposes `estimate`, `run`, `get`, and a read-only view of the remaining budget.

## Why the metric is layered

Only S1 to S3 have exact answers (computed locally). G1 to G4, worth 2,700 points, have none. So:

1. **Proxy loop (free, local):** S1 to S3 plus self-generated surrogate circuits from the G families at exactly solvable sizes. Score corr² and error against exact values, against cost.
2. **Convergence on G (paid, controlled):** correlation between successive fidelity levels and sensitivity to truncation. Agreement between approximations is a consistency signal, not accuracy.
3. **Submission scores (user-submitted checkpoints):** a selector among genuine candidates, governed by [AGENTS.md](AGENTS.md).

## Phases

### Phase 0: verify the environment (about 30 min)

Check on the Mac: Python 3.11+, `bluequbit`, `qiskit`, `numpy` import; `BLUEQUBIT_API_TOKEN` is set in the controller shell only. Run `get_circuit_info("Duke_S1_0")` and one free S1 job; compare the result to a local exact value. Test `estimate` on one larger circuit. Test whether `device="gpu"` is accepted on this plan using `estimate` only. Record versions and findings in `NOTES_RUN.md`.

**Done when:** the free S1 job matches the local exact value for all 4 qubits (qubit order confirmed), and `NOTES_RUN.md` lists plan limits and GPU availability.

### Phase 1: controller, ledger, evaluator, exact references (about 2 h)

Build the protected parts. Compute exact S1, S2 values locally (statevector). Attempt S3 (30 qubits, Clifford plus some Rz) with a feasible exact method; if none works within an hour, mark S3 truth unavailable in `NOTES_RUN.md` and continue without faking it. Test the controller: spend cap refuses an over-cap request, a killed process resumes from the ledger, a repeated config returns the cached result, an outstanding job ID is reconciled after a simulated timeout.

**Done when:** all four controller tests pass, the evaluator reproduces corr² = 1 on exact-versus-exact, and protected paths are read-only.

### Phase 2: first strategy and baseline CSVs (about 1 h)

Write `strategy.py` v1. Start cheap: `cpu` exact for S1 and S2; for S3 and G1 to G4 a first rung on `mps.cpu` or `pauli-path` chosen from `estimate` output, then a second rung at double the fidelity. Combine rungs by the simplest rule that works on the proxies. Produce a complete CSV for each of the seven problems with a method note. *Narrowed by the target change: G2 and G4 only.*

**Done when:** schema-valid G2 and G4 CSVs exist in `candidates/`, S1 to S3 corr² of the chosen methods are reported against exact values, and `STATUS.md` lists the CSVs ready for the user to submit.

### Phase 3: surrogate benchmark (about 1 h)

Generate random circuits matching each G family (Haar 2q 1D chain, Haar 2q grid, Clifford 2q plus some Rz grid; echo structure from `CHALLENGE_SUMMARY.md`) at sizes with exact answers, plus intermediate sizes where only a high-fidelity reference exists (labeled as such). Wire them into `evaluate.py`.

**Done when:** `evaluate.py benchmark` prints corr² and error per family for strategy v1, in under 5 minutes of wall time.

### Phase 4: autonomous loop

Follow [program.md](program.md) until the freeze time.

**Done when:** it is 10:30 a.m. ET on October 25 or the budget is exhausted.

### Phase 5: freeze and handover

Validate every final CSV, write method notes, and summarize known remaining credit, outstanding jobs, and uncertainty in `STATUS.md`.

**Done when:** seven validated CSVs with method notes are in `final/` and the user has been told where they are.

## Open items to settle in Phase 0

- GPU access on the Free plan (billing page lists GPU under paid plans; the event page says credit-funded GPU is available).
- Hybrid machine time limit (Free plan shows 15 min; the event page says 24 h). The loop runs on the Mac regardless.
- Whether `estimate` and `get_circuit_info` are free.
