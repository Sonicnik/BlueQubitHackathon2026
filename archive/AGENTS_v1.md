# Duke Quantum Hackathon: agent guide

Updated October 24, 2026. Official kit, current rules, and organizer announcements govern competition requirements.

## Read by task

- **Setup or implementation:** follow [PLAN.md](PLAN.md), the selected seven-step plan. It is not evidence of implementation or authorization to spend.
- **Challenge requirements or submission:** read [CHALLENGE_SUMMARY.md](CHALLENGE_SUMMARY.md), then verify against the released kit.
- **Physics or numerical conventions:** consult [RESEARCH_READING_MAP.md](RESEARCH_READING_MAP.md).
- **Teaching:** use [MISSION.md](MISSION.md), [NOTES.md](NOTES.md), and [RESOURCES.md](RESOURCES.md).

The project contains preparation material and a tutorial notebook. Installed packages/imports do not establish a working competition pipeline. Preserve organizer files when the kit arrives.

## Competition boundaries

Rules inspected October 24: [official rules](https://app.bluequbit.io/hackathons/2GMaAenu3iSsIC6Z?tab=rules).

- Online entrants compete individually; in-person DuQuantum teams may have at most four people.
- All BlueQubit use and submissions during the event use one registered team account. Other tools may simulate open samples.
- Hidden circuits are accessed and simulated only through supported BlueQubit methods by ID. Do not attempt to reconstruct hidden circuit structure.
- Stay within the equal event budget; do not augment it through extra accounts, outside credits, or other teams' resources.
- Keep work/results within the permitted entrant or declared team. Competition submissions must be produced during the event.
- Commercial AI assistants and standard simulators are allowed; private clusters and inaccessible proprietary tools may violate the competition's fairness requirements.
- Submit genuine estimates, with required method notes. Scoring probes designed to extract hidden answers are prohibited.

## Autonomy, spending, and secrets

The user selected an agent that may freely rewrite strategy code. Protect the evaluator, observable contract, references, credentials, and spending controls with enforceable boundaries. Reference answers evaluate sample predictions; they are not prediction inputs.

Establish a spending ceiling before paid work, including concurrent/queued jobs and Hybrid machine time. Keep tokens out of source, logs, chat, and strategy-process environments. A virtual environment isolates dependencies, not permissions.

Track every experiment's code/configuration, circuit/observable IDs, software versions, seed if relevant, job ID/status, runtime, cost, predictions, and evaluation. Cache only matching complete configurations. A timeout may leave a remote job running: reconcile its ID/status before retrying. Bound retries and concurrency.

## Correctness and submission

- Derive the target and labels from the kit, not tutorial assumptions. Check echo order, inverse cancellation, a known expectation, and qubit mapping.
- No official local scorer or sample answers exist; score samples locally as Pearson corr² against our own exact S1–S3 values (the platform's formula). Also report numerical error and each sample separately. Agreement between approximations does not establish accuracy.
- Prefer supported direct expectations; partial top-outcome counts may not recover a full expectation.
- Validate the released CSV schema, exact ID coverage, finite values, and confirmed range. Save a reproducible candidate with provenance.
- Report outstanding jobs, known remaining credits, and uncertainty. Final platform submission remains the user's action unless explicitly authorized; acceptance requires a verified platform response.
