# program.md: the autoresearch loop

Read after [PLAN.md](PLAN.md) Phase 3 is done. Boundaries, spending, secrets, and submissions are in [AGENTS.md](AGENTS.md). Do not restate them here.

## Loop

Repeat until 10:30 a.m. ET on October 25 or the budget is exhausted:

1. **Hypothesis.** Write one line in `results.tsv` naming the change and the expected effect (for example "extrapolate in 1/chi across two MPS rungs improves corr² on Haar-chain surrogates").
2. **Edit** `strategy.py` or `strategy/` only.
3. **Check correctness.** Run the unit checks (inverse cancellation, known expectation, qubit mapping). A failing check ends the iteration as rejected.
4. **Run.** Proxy benchmark first (about 5 minutes). Paid G runs only when the proxy improved or a new ladder rung is due.
5. **Evaluate.** Record corr² and mean absolute error per family, cost, and runtime.
6. **Keep or reject.** Keep when proxy corr² improves without a cost blow-up. Commit when kept; `git reset` when rejected. Log both.

## Priorities

Spend and attention follow points: G4 (1,000), G3 (800), G2 (600), G1 (300), then the samples (100 each, nearly solved). Climb a cost ladder per circuit and stop climbing when successive rungs agree.

Consider, in roughly this order: MPS bond-dimension ladder with extrapolation; Pauli-path threshold ladder with extrapolation; choosing device per family; combining MPS and Pauli-path estimates; ranking-preserving post-processing (the score ignores scale and offset, so shape and sign matter most).

## Keep a candidate ready

After every kept change that alters G predictions, write a complete schema-valid CSV to `candidates/` with its method note and ledger references, and add one line to `STATUS.md` (file name, what changed, proxy score, cost so far). The user submits from there.

## Resume

On start, read `results.tsv`, the ledger, and `STATUS.md`. Reconcile outstanding job IDs through the controller before submitting anything. Never repeat a configuration the ledger already holds.

## Ask without stopping

Write a question to `QUESTIONS.md` and continue with free, safe work when:

- an API or limit behaves differently from [PLAN.md](PLAN.md) assumptions,
- a decision would exceed the authorized spend or change the account,
- a rule is ambiguous,
- the proxy metric stops ranking strategies sensibly.

Keep the question to what you found, what you expected, and the options.

## Freeze (from 10:30 a.m. ET on October 25)

Stop experiments. Run [PLAN.md](PLAN.md) Phase 5.
