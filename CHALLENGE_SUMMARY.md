# BlueQubit Duke challenge: essentials

Updated October 24, 2026, from the [official challenge page](https://app.bluequbit.io/hackathons/2GMaAenu3iSsIC6Z) (Overview, Rules and Problems tabs, read about 11:40 a.m. ET). The page and organizer announcements govern; re-check them if anything here looks off.

## What the "kit" is

There is no README, scorer, or template package. The kit is:

- The challenge page itself: Overview (task, quick start, agent notes, scoring), Rules, and Problems.
- Three sample zips, saved read-only under [kit/](kit/): `kit/downloads/sample_S{1,2,3}.zip`, unzipped into `kit/samples/S{1,2,3}/`, with 50 QASM files in total.
- `kit/problems.json`: the public problem list from `GET /api/v1/competitions/2GMaAenu3iSsIC6Z/problems` (IDs, points, descriptions).
- The BlueQubit SDK (`bluequbit>=0.19.0b1`). Hidden circuits run only by ID.

No reference answers are published for any circuit, samples included. The platform's scorer is the only official scorer. Samples S1–S3 are small enough to compute exactly ourselves, which gives local ground truth.

## Task

There are seven circuits, each a separate problem, with one ID per qubit: `Duke_<circuit>_<q>`, q = 0 … n−1. For each ID, run its circuit from |0…0⟩ and estimate ⟨Z⟩ on qubit q, a value in [−1, 1]. Qubit q is `q[q]` in the QASM register. Keep that order, because swapping qubits ruins the score.

Echo structure, verified in the sample QASM: U → `x q[b]` → U† → `z q[q]` → U → `x q[b]` → U†, with no measurements. Here b is the butterfly qubit. Each ID is a different circuit file; only the `z` target changes between IDs of the same circuit. Gate set: `u3`, `cz`, `x`, `z`.

| # | Circuit | Qubits | Layout | Gates in U | U layers | Butterfly | CZ total (depth) | Points | Access |
|---|---|---|---|---|---|---|---|---|---|
| 1 | S1 | 4 | 1D chain | Haar 2q | 4 | 0 | 72 (48) | 100 | QASM + ID |
| 2 | S2 | 16 | 1D chain | Haar 2q | 12 | 0 | 1,080 (144) | 100 | QASM + ID |
| 3 | S3 | 30 | 5×6 grid | Clifford 2q + some Rz | 16 | 14 | 1,568 (128) | 100 | QASM + ID |
| 4 | G1 | 30 | 1D chain | Haar 2q | 32 | 0 | 5,568 (384) | 300 | ID only |
| 5 | G2 | 36 | 1D chain | Haar 2q | 18 | 18 | 3,780 (216) | 600 | ID only |
| 6 | G3 | 36 | 6×6 grid | Clifford 2q + some Rz | 24 | 14 | 2,872 (192) | 800 | ID only |
| 7 | G4 | 38 | 6×6 grid + qubits 36–37 below 30–31 | Haar 2q | 16 | 0 | 3,024 (192) | 1,000 | ID only |

Grid indexing: qubit = row × 6 + col. G4's values are small (mostly within ±0.1), and no rescaling is needed. CZ counts for S1–S3 were checked against the downloaded files.

## Running by ID (official snippet)

```python
bq = bluequbit.init()                                  # reads BLUEQUBIT_API_TOKEN
n = bq.get_circuit_info(f"Duke_{c}_0").num_qubits      # free
z = "I" * (n - 1 - q) + "Z" + "I" * q                  # q0 is the RIGHTMOST character
job = bq.run(f"Duke_{c}_{q}", device="cpu", pauli_sum=[(z, 1.0)])
job.expectation_value
```

Available devices are `cpu` (exact, small circuits only), `gpu`, `mps.cpu`, `mps.gpu`, and `pauli-path`; options are in the [SDK docs](https://app.bluequbit.io/sdk-docs/bluequbit.sdk.html). `get_circuit_info` also returns `depth_2q`.

## Submission and scoring

- Submit one CSV per problem on that problem's Submissions tab, with a short method note. Rows are `circuit_id,value`, one per ID, in any order. An optional `circuit_id,value` header is allowed. IDs are case-sensitive, and values can be any finite number. The file name doesn't matter.
- A file with a missing or wrong ID is rejected before submission and doesn't use an attempt.
- Each problem allows up to 20 submissions, and the best one counts. The score appears right away.
- Score = corr² × points, where corr is the Pearson correlation with the exact values over that problem's IDs. Scale and offset don't matter. A negative correlation, or all-equal values, scores 0. The maximum total is 3,000.
- Ties are broken by time penalty: the sum, over your best submission per problem, of the time since the start. Earlier good submissions help.

## Rules snapshot

| Item | Requirement |
|---|---|
| Event | Oct 24, 11:30 a.m. ET to Oct 25, 2026, 11:30 a.m. ET (submissions must be received by then). |
| Account | One registered account per team. Online entrants compete alone; in-person Duke teams can have up to 4 people. No multiple accounts. |
| Budget | $30 credit per participant via the coupon on the Overview page (Account → Billing → Redeem Coupon). Small jobs are free. Track spending on the usage page. Credits from outside the event are not allowed. |
| Compute | Hybrid mode: a SMALL machine can stay on for 24 h and comes with the SDK, token, and Claude Code preinstalled. LARGE machines have a limit of 6+ hours (see the usage page). GPU is available via `bq.run(device="gpu")` with limited availability. Working on your own computer is also allowed. |
| Hidden circuits | Access and simulate only through BlueQubit, by ID, using the platform's methods. Exploiting bugs or loopholes is prohibited; report them instead. |
| Genuine estimates | Probing submissions (one-hot, mostly constant, or built to extract answers) lead to disqualification. Method notes are required and get reviewed. |
| Tools | AI assistants are encouraged. Standard simulators are fine. Private clusters and unreleased internal codes may not be credited. |
| Collaboration | For online entrants, any collaboration or result sharing leads to disqualification. Asking organizers (rhik@bluequbit.io, Discord #duke-2026) is always allowed. |

**Superseded:** the earlier `circuit,qubit,estimate` format and the "two samples" description. The real setup has three samples, and 140 graded values plus 50 sample values.

## Strategy notes

Pearson correlation is the competition objective, and numerical closeness is the scientific goal; track both on S1–S3 against exact local values. Methods that get the per-qubit *shape* right (sign and relative size) score well even when the overall scale is off. Never use scoring probes to produce predictions.

## Next steps

Follow [PLAN.md](PLAN.md). Operating rules are in [AGENTS.md](AGENTS.md); physics references are in [RESEARCH_READING_MAP.md](RESEARCH_READING_MAP.md).
