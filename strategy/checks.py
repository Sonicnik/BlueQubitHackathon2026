"""Loop correctness checks (program.md step 3): qubit mapping, known expectation, inverse cancellation. Free, local.

Run: .venv/bin/python strategy/checks.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # project root, so `strategy` is strategy.py
from qiskit import QuantumCircuit
from qiskit.quantum_info import SparsePauliOp, Statevector
import strategy
from bench.surrogates.gen import build_u, exact

# qubit mapping: zq(n, q) must measure qiskit qubit q (q0 = rightmost character)
qc = QuantumCircuit(3)
qc.x(1)
for q, want in enumerate([1, -1, 1]):
    got = Statevector(qc).expectation_value(SparsePauliOp(strategy.zq(3, q)[0][0])).real
    assert abs(got - want) < 1e-12, (q, got)
# known expectation: zq on a kit sample reproduces the stored exact value
t = json.load(open("bench/truth/S1.json"))["values"]["Duke_S1_2"]
s1 = QuantumCircuit.from_qasm_file("kit/samples/S1/Duke_S1_2.qasm")
assert abs(Statevector(s1).expectation_value(SparsePauliOp(strategy.zq(4, 2)[0][0])).real - t) < 1e-10
# inverse cancellation on a surrogate U
u, n = build_u("grid", (2, 3), 4, seed=1)
assert abs(exact(u.compose(u.inverse()), n, 0) - 1) < 1e-9
# every configured circuit has a surrogate or is a sample
assert set(strategy.SURROGATE_OF.values()) == set(strategy.CONFIG)
print("checks ok")
