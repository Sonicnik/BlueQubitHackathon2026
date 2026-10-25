# DuQuHack presentation script (7 minutes)

About 950 words. Fill in the `[ ]` brackets before presenting.

---

## Slide 1: Title (0:00 to 0:30)

Hi, I'm Sonic. This is our entry to the BlueQubit Duke challenge: estimating quantum echo signals on circuits too big to simulate exactly. The short version: we built an automated research loop that experiments on its own, and every dollar of compute it spends goes through a guard.

## Slide 2: The problem (0:30 to 1:20)

Each circuit is an echo: run a random circuit U, flip one "butterfly" qubit, run U backwards, poke a target qubit, then do it again. We have to predict the Z expectation on every qubit, a number between −1 and 1. Scoring is Pearson correlation squared with the true values, so the shape across qubits matters, not the scale.

This is the second-order OTOC from Google's Quantum Echoes experiment. Classical methods are known to struggle with it, because the signal comes from interference between many paths. The hardest problem, G4, is a 38-qubit 2D grid with 16 layers and the butterfly in a corner. The organizers tell us its true values are mostly within ±0.1.

## Slide 3: The system we built (1:20 to 2:30)

We never had ground truth for the graded circuits, so we built the infrastructure first.

- **A spend controller.** It's the only code that holds the API token. It enforces a hard budget cap and reserves money for jobs in flight. It also caught that the platform sometimes quotes $25 for a job the estimate API calls $0.20, and cancels anything that would cross the cap. Every job goes into an append-only ledger, so a crash or network drop resumes without paying twice.
- **Exact references.** S1 and S2 locally; S3 at 30 qubits using the platform's free CPU statevector.
- **Surrogate circuits.** Our own echo circuits that copy each graded family's structure at sizes we can solve exactly: 1D chains for G2, 2D grids for G4. That gives a free benchmark to score any idea against before touching the real circuits.
- **The loop itself:** one hypothesis, a correctness check, the benchmark, then keep or roll back, logged in git.

## Slide 4: G2, the 1D chain (2:30 to 3:30)

For G2 the right tool was a matrix product state, which fits a 1D chain naturally. Our first file used bond dimension 32 and scored 342 out of 600.

The lesson was that our first surrogate was too easy: at 20 qubits it said 0.985. So we built a 30-qubit chain with exact answers from the free platform CPU. That one behaved like the real problem: 0.73 at bond dimension 32, 0.87 at 64, 0.96 at 128. We resubmitted G2 at 128 [and scored ___ / 600]. Validating the proxy against reality before trusting it was the single most useful step.

## Slide 5: G4 and what failed (3:30 to 4:45)

G4 is where things got interesting, mostly by failing.

- **MPS** at bond dimension 32 scored zero. Raising it to 256 on GPU didn't help: some qubits settled at 0.55 to 0.6, where the truth is near 0.1. That matches a recent paper showing tensor networks can't feasibly simulate Google's echo experiment.
- **Pauli-path**, which tracks the observable backwards as a sum of Pauli strings, returned exactly zero on every qubit. Truncation dropped every term.

The breakthrough was transpilation level 3, a tip that came from my teammate's analysis. Level 3 removes gates outside the butterfly's light cone before simulating, since those cancel between U and U-dagger anyway. We'd seen exactly that cancellation in our own surrogates, where extra layers that missed the butterfly qubit changed nothing. With level 3 on the GPU, G4 went from 0 to 267 out of 1000.

## Slide 6: The surprise (4:45 to 5:40)

The obvious next step was a finer truncation threshold: keep more terms, get closer to the truth. 1e-4 instead of 3e-4 cut the exact zeros from 12 to 4. It scored 136, lower.

Several small values flipped sign between the two runs. The literature explains it: a practical guide to Pauli-path simulators reports that truncation error is non-monotonic, so a finer threshold can be worse and apparent convergence can be a false minimum.

Our response was to test, not guess. We fixed the decision rule first, then scored 3e-4, 1e-4 and an average of the two on a 28-qubit, 16-layer surrogate grid with exact answers [result: ___].

## Slide 7: Rules and integrity (5:40 to 6:30)

Two choices we made deliberately. First, we never tuned a file using hidden scores. Uploading variants and keeping whatever scores best is probing, so every candidate came from a simulation, with a method note and job IDs. Second, the budget. We stayed under the cap with about [$__] spent, mostly at 20 cents per GPU job.

The hard limits were practical: one GPU job at a time, CPU Pauli-path locked behind a paid top-up, and one night where the laptop went to sleep and we lost seven hours of compute.

## Slide 8: Takeaways (6:30 to 7:00)

Three things. Validate your proxy against reality before you trust it. For echo circuits, cancelling the gates outside the light cone matters more than raw precision. And on hard problems, finer is not always better: test it against exact answers before you believe it. Thank you.
