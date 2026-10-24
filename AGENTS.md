# Duke Quantum Hackathon: rules and boundaries

Updated October 24, 2026. This file is the single source of truth for rules, spending, secrets, and submissions. Official page, rules, and organizer announcements override it: [challenge page](https://app.bluequbit.io/hackathons/2GMaAenu3iSsIC6Z), [official rules](https://app.bluequbit.io/hackathons/2GMaAenu3iSsIC6Z?tab=rules).

## Competition rules

- Online entrants compete individually. In-person DuQuantum teams have at most four people.
- Use one registered BlueQubit account for the whole event. Other tools may simulate the open samples.
- Run hidden circuits only through supported BlueQubit methods, by ID. Reconstructing hidden circuit structure is out of bounds.
- Stay inside the event budget: no extra accounts, outside credits, or other teams' resources.
- Keep work and results inside the permitted entrant or declared team. Produce submissions during the event.
- Commercial AI assistants and standard simulators are allowed. Private clusters and inaccessible proprietary tools may violate fairness.
- Submit genuine estimates with required method notes. Probing submissions (one-hot, mostly constant, or built to extract hidden answers) lead to disqualification.
- Ask organizers about ambiguity: rhik@bluequbit.io, Discord #duke-2026.

## Spending

- **Authorized total: $27.00** of the $30 event credit. The remaining $3 is a reserve.
- The spend controller enforces the cap. Commit each job's estimated cost at submission and reconcile on completion. Queued and in-flight jobs count.
- Free jobs are ledgered but do not count against the cap.
- Call `estimate` before every paid job. Record the estimate and the actual cost.
- Bound concurrency (default 4) and retries (default 2).
- Any need to exceed the cap, redeem a coupon, upgrade a plan, or add balance goes to the user through `QUESTIONS.md`.

## Secrets and protected files

- Only the controller process reads `BLUEQUBIT_API_TOKEN`. Strategy code, subprocesses it spawns, logs, commits, and chat never contain it.
- Protected, not editable by the research agent after Phase 1: `controller/`, `evaluate.py`, `bench/truth/`, `ledger/`, `kit/`. Make them read-only (`chmod -R a-w`) once tested.
- Reference answers evaluate predictions and never feed them.
- Edit work happens in `strategy.py` and `strategy/`. A Python virtual environment isolates dependencies, not permissions. Treat the boundary as best effort, and report any breach.

## Submissions

The user performs every platform submission. The agent prepares and validates files.

- **Format:** `circuit_id,value`, one row per ID, optional header, exact case-sensitive IDs, finite values. Validate against `kit/problems.json` before handing a CSV over.
- **Candidates:** each CSV is a complete, genuine estimate from a distinct strategy or fidelity level, with a method note saying what was run and what is uncertain.
- **Selection:** each problem allows 20 submissions and the best counts. Use scores as a selector among genuine candidates at checkpoints, and record every score in the ledger next to its candidate. Never hill-climb on submission scores per iteration, and never submit a variation whose purpose is to learn the hidden values.
- **Slots per problem:** about 6 for strategy-family selection, about 10 for refined candidates late in the run, 4 held back.
- **Timing:** earlier good submissions help the tie-break. Hand over a complete baseline CSV for every problem as soon as one exists.
- **Report:** outstanding jobs, remaining credit, and uncertainty with every handover. Acceptance needs a verified platform response.

## Correctness

- Derive the target and labels from the kit, not from tutorial assumptions. Check echo order, inverse cancellation, one known expectation, and qubit mapping (q0 is the rightmost Pauli-string character).
- Score samples locally as Pearson corr² against our own exact S1 to S3 values, and report numerical error separately for each sample.
- Prefer direct expectation values (`pauli_sum`) over reconstructing from counts.
- Agreement between approximations does not establish accuracy. Say so in method notes.
