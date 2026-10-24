# G4 hypotheses

G4 is the largest prize (1,000 points). The first candidate (`mps.cpu`, chi=32) scores about 0 because its values reach 0.96 while true G4 values are mostly within +-0.1. Each item below is a testable hypothesis for the loop in [program.md](../program.md). Rules, spending, and submissions live in [AGENTS.md](../AGENTS.md); circuit facts live in [CHALLENGE_SUMMARY.md](../CHALLENGE_SUMMARY.md).

## Where the ideas come from

Ideas come from papers a collaborator's assistant summarized. Nobody has checked the summaries yet. Before building on a paper, fetch its abstract, confirm it exists, and note one line on what it actually says in `NOTES_RUN.md`. Treat every item as an experiment, not a result.

| Paper | Used for |
| --- | --- |
| Pauli Propagation: A Computational Framework for Simulating Quantum Systems (Rudolph et al., 2025, arXiv 2505.21606) | What Pauli-path truncation keeps and loses; H1, H2 |
| Benchmarking Zero-Setup Quantum Circuit Simulators (Mazumder et al., 2026, arXiv 2607.09882) | How BlueQubit MPS and Pauli-path runtime scale with settings; H1, H3 |
| Observation of constructive interference at the edge of quantum ergodicity (Google Quantum AI, Nature 2025) | The echo observable; why heavy truncation can lose signal |
| Tensor Networks with Belief Propagation Cannot Feasibly Simulate Google's Quantum Echoes Experiment (Bermejo et al., 2026, arXiv 2604.15427) | Reason to stop MPS climbing early; H3 |
| Observable Estimation in the Absence of Classical Verification (Barron et al., 2026, arXiv 2607.25998) | Convergence diagnostics without ground truth; H5 |

## Facts already measured (do not repeat)

- Pauli-path at threshold 1e-3 on G4 returned exactly 0.0 for the tested ID. Too coarse for values near 0.1.
- Pauli-path `estimate` is a flat placeholder. The submit-time quote was $25 with 100 h allowed for one job. MPS jobs so far cost $0.00.
- Remote `mps.cpu` chi=32 is much better than local qiskit-aer MPS at the same chi (S2 corr² 1.00 vs 0.96).
- The surrogate `grid4x5` is a Haar grid in G4's small-value regime, but it has 20 qubits against G4's 38. It is the best available proxy for G4.

## H0: prerequisites (do first)

1. **Controller fix.** The user approved the change from QUESTIONS.md #2, October 24. In `controller/client.py`, after submitting a job, read its submit-time `estimated_cost`, raise the reservation to it, and cancel the job at once if it would cross the cap. Add a test. This approval covers only this change; the other protected files stay read-only.
2. **Larger Haar-grid surrogate.** Add one family with 24 to 28 qubits (for example 4x6 or 4x7), Haar 2q gates, layers chosen so most values sit within +-0.1, butterfly qubit 0. Compute exact truth locally (25 qubits is about 0.5 GB; stay under 28).

**Done when:** the controller test for submit-time quotes passes, and `evaluate.py benchmark` reports the new family.

## H1: finer Pauli-path thresholds recover a stable pattern

Claim: thresholds around 3e-4, 1e-4, 3e-5, 1e-5 (the SDK minimum) give predictions that correlate with truth on the surrogate, and the same thresholds are affordable on G4.

1. **Calibrate on surrogates** (free or tiny): run `pauli-path` on `grid4x5` and the new family at each threshold. Record corr² and MAE against exact truth, runtime, and cost.
2. **Pilot on G4:** three IDs spread across the grid, the coarsest threshold that scored well on the surrogate. Record the submit-time quote, runtime, and prediction. Escalate only if the quote fits the cap.
3. **Full vector** only for the best affordable threshold, then one finer rung.

**Done when:** each rung has corr² (surrogate), cost, and runtime in `results.tsv`, and a G4 vector exists for the best rung that fits the budget, or the notes say why none does.

## H2: transpilation level changes the approximation

Claim: `pauli_path_circuit_transpilation_level` 1 and 3 give different truncation losses than the default 2, and one of them is better at a fixed threshold.

Compare levels 1, 2, 3 at one affordable threshold on both surrogates first.

**Done when:** a table of corr² by level exists for both surrogates, and the best level is used for the G4 rungs in H1.

## H3: a modest MPS ladder, with an early stop

Claim: chi 64 and 128 on `mps.cpu` improve on chi=32 for the surrogate grids. The tensor-network paper suggests echo states compress poorly, so this may fail.

Run chi 64 and 128 on both surrogates. Check the submit-time quote on one G4 ID before each rung. Stop climbing when surrogate corr² gains less than 0.05 per doubling.

**Done when:** a stop decision is recorded with the corr² gain per rung.

## H4: standardized ensemble of two methods

Claim: a mixture of standardized Pauli-path and MPS vectors with weight alpha in {0.25, 0.5, 0.75} beats either alone on the surrogates.

Standardize each vector (zero mean, unit variance) before mixing. Skip any vector whose variance is near zero, because standardization amplifies noise. Test on surrogates first; apply to G4 only if the surrogate gain is clear.

**Done when:** corr² by alpha is tabulated on both surrogates and a keep or reject decision is logged.

## H5: convergence diagnostics for G4 (no ground truth)

For every G4 vector pair at successive rungs, record: correlation between rungs, which qubits change most, and how much variation the vector retains. Agreement between rungs is evidence of stability and not proof of accuracy, so every G4 method note says so.

**Done when:** `STATUS.md` shows these three numbers for each G4 candidate.

## Not for now

Custom middle-out echo simulation and hybrid Pauli with Monte Carlo need circuit access, which the hidden G4 interface does not give. Try them only on open sample circuits, and only if H1 to H4 are exhausted.

## Order

H0, H1 (calibrate then pilot), H2, H3, H4, H5 throughout. Revisit the order if a surrogate result contradicts an earlier one, and log why.
