# Physics and numerical reference

Background only: derive competition conventions from the released kit.

## Core distinctions

- A pure state is a normalized complex vector; amplitudes determine probabilities through squared magnitudes.
- An expectation is `<psi|O|psi>`. For Pauli Z on qubit j: `P(j=0) - P(j=1)`; it is signed, not a probability.
- Distinguish evolution U, the constructed echo, and its measured observable. U's ordinary output distribution is not automatically the target.
- U† reverses U: reverse gate order and invert each gate.
- The tutorial uses B(t) = U† B U, M = Z_q, and OTOC(2) = `<(B(t) M)^4>` in the all-zero state. Its chronological echo is `U, B, U†, M, U, B, U†`, followed by Z_q measurement. Each q changes the echo. This is tutorial background, not an established kit specification; OTOC(2) is not an OTOC(1) prediction squared.
- Qiskit Pauli labels put qubit 0 at the right: `IIZ` measures Z on qubit 0. Check the wrapper mapping too.

## Approximation pitfalls

| Method | Main issue |
| --- | --- |
| Exact statevector | Complex128 state storage is `16 * 2^n` bytes; 30 qubits needs 16 GiB before temporary storage. |
| MPS | Bond dimension bounds retained correlations; entanglement, geometry, and ordering affect truncation error. |
| Pauli propagation | Many discarded small coefficients can collectively affect the observable. |

Reversal does not restore information lost to approximation. Increased precision or agreement between methods does not by itself prove hidden accuracy. Validate against exact samples and report score, numerical error, runtime, and cost.

## Read when needed

- Echo construction and algorithms: [BlueQubit OTOC tutorial](https://app.bluequbit.io/tutorial/otoc-tutorial). Its `otoc_tools.py` is distinct from the competition helpers.
- States and expectations: [IBM Quantum information](https://quantum.cloud.ibm.com/learning/en/courses/basics-of-quantum-information/single-systems/quantum-information), [Statevector reference](https://quantum.cloud.ibm.com/docs/en/api/qiskit/quantum_info.Statevector).
- Indexing: [IBM bit ordering](https://quantum.cloud.ibm.com/docs/en/guides/bit-ordering).
- Entanglement and Schmidt decomposition: [IBM purifications](https://quantum.cloud.ibm.com/learning/en/courses/general-formulation-of-quantum-information/purifications-and-fidelity/purifications).
- Job options/results: [BlueQubit SDK](https://app.bluequbit.io/sdk-docs/bluequbit.sdk.html). Confirm installed/kit compatibility; use direct expectations where supported rather than reconstructing them from capped counts.
- Research loop: [Karpathy autoresearch](https://github.com/karpathy/autoresearch).
