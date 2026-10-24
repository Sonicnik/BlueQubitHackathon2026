# Current plan: local autoresearch for the BlueQubit challenge

Agreed October 24, 2026. This records the selected plan; it does not authorize paid jobs or final submission.

## Goal and approach

Build a local research workflow that lets an agent freely rewrite prediction strategies to improve quantum echo estimates within the event's compute and time limits. Adapt Karpathy's experiment loop; its original language-model training stack is not required.

Use the local computer for strategy code, control, evaluation, and saved results. Use BlueQubit for hidden-circuit simulations through the registered team account. Start with one working agent; consider independent agents only after the complete workflow is reliable.

The strategy may change; the requested observable, official evaluator, reference answers, credentials, and spending controls remain protected. Reference answers may evaluate sample predictions, but must not be used as prediction inputs. Measure numerical error and official score separately.

## Procedure

Step 1 is done (October 24). Steps 2–7 are pending. Package checks alone do not complete step 2.

### 1. Inspect the released kit and reconcile our notes

Obtain the official kit and inspect its README, helpers, samples, scorer, template, and current rules. Record the exact API, observable, scoring, submission format, permitted simulation options, compute limits, and deadline. Preserve organizer originals.

**Done when:** the challenge contract is recorded from official materials and outdated local claims are corrected.

### 2. Verify the existing environment

Check dependency compatibility, the selected agent's authentication, and required network access. Install or change packages only where needed.

**Done when:** required imports and local checks pass, authentication/access are established without exposing secrets, and compatible versions are recorded.

### 3. Establish the execution boundary

Give the researcher an isolated working copy where it can rewrite strategy code. Keep the evaluator, reference files, credentials, and spending controller outside its writable area. Use enforceable file/process/network boundaries; Markdown instructions and a Python virtual environment alone do not provide isolation.

**Done when:** strategy edits work, protected components resist modification, and simulation requests go through a controller that enforces allowed operations, concurrency, and spending commitments.

### 4. Prove one complete experiment works

Run small correctness checks for echo construction, a known observable, and qubit indexing. After spending authorization, run an affordable sample experiment, retrieve its result, score it, and save provenance.

**Done when:** one reproducible experiment connects strategy execution to a valid prediction, evaluation, and persisted job/cost record.

### 5. Implement the research loop

Run hypothesis → strategy revision → correctness checks → simulation → evaluation → retain or reject. Include checkpoints, restart recovery, duplicate-job prevention, and explicit stopping conditions. Reconcile outstanding jobs before retrying. Preserve useful accuracy/cost tradeoffs and a complete baseline candidate early.

**Done when:** changes can be evaluated and retained or reverted without losing results, bypassing controls, or repeating already submitted work.

### 6. Write and test the handoff documents

Document tested setup and launch commands, editable boundaries, evaluation, budgets, resume behavior, result locations, and submission preparation. Keep one source of truth for each instruction.

**Done when:** a fresh agent can follow the documentation and reproduce the baseline without relying on this conversation.

### 7. Launch a short supervised trial

Observe the full loop, inspect its research decisions and failure recovery, and verify spending accounting. Extend the run or add independent agents only after this trial succeeds. Multiple agents must share one job ledger and total budget.

**Done when:** the trial finishes within its limits with reproducible results and a clear continuation or stop decision.

## Current evidence and open decisions

- Local checks on October 24: Python 3.11.7; BlueQubit 0.19.0b1, Qiskit 2.6.1, and NumPy 2.4.6 installed and imported successfully.
- Codex and Claude Code executables are present; authentication and unattended operation have not been tested.
- Step 1 is done. The kit is the challenge page plus three sample QASM zips, saved read-only in `kit/`. There is no README, scorer, or template. The contract is recorded in [CHALLENGE_SUMMARY.md](CHALLENGE_SUMMARY.md). The event runs until Oct 25, 11:30 a.m. ET.
- Remote job execution and account credits remain unverified. Registration/"Join", coupon redemption, and the API token are the user's actions.
- Open decisions: agent and usage allowance, permitted total spend (≤ $30 event credit), concurrency, execution isolation, and local machine vs. the BlueQubit Hybrid machine.
- No paid experiment or final submission was performed as part of documenting this plan.

## References

- [Challenge contract](CHALLENGE_SUMMARY.md)
- [Agent operating rules](AGENTS.md)
- [Karpathy autoresearch](https://github.com/karpathy/autoresearch)
- [BlueQubit SDK](https://app.bluequbit.io/sdk-docs/bluequbit.sdk.html)
