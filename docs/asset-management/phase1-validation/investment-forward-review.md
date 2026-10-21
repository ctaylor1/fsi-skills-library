# Investment forward evaluation evidence

Recorded `2026-09-20T23:10:32.768875+00:00`. Nine synthetic cases and 29 independently expected assertions passed against the renamed native packages. The complete inputs, actual native outputs, output mutations, observed rejection messages, implementation SHA-256 values and read-only replay command are retained in [investment-forward-review.json](investment-forward-review.json).

This is a durable re-execution of the preceding in-memory forward cases, not a retrospective statement of unrecorded acceptance. Inputs were constructed independently of package eval fixtures. The economic date `2026-09-20`, source references and identities are synthetic.

| Workflow | Independently expected outcome | Observed result |
| --- | --- | --- |
| Investment mandate review | On $100m NAV, Alpha 12% current / 15% proposed and cash 10% current / 8% proposed produce exactly four breaches. Other-mandate and future-effective rules do not apply; unsupported regulatory method is not evaluable. | Passed, including separate original-input output validation. |
| Mandate negative/coverage cases | Altered breach output and future holdings/prices are rejected; missing sector is not evaluable. | Passed; actual inputs, mutation and rejection messages retained. |
| Portfolio exposure | All $100m retained: Alpha 27%, US 80%, UNKNOWN 4%; government/cash remain in exposure tables and fund wrapper remains in asset-class exposure. | Passed. |
| Exposure coverage/negative cases | Missing liquidity produces null total with known illiquid 20%; missing corporate duration is disclosed; a $5m NAV gap stays unreconciled without invented cash; altered output and a short position are rejected. | Passed; actual outputs and rejection messages retained. |

Replay from the repository root using the full `verification_command` in the JSON. It first checks the eight implementation-file digests, recomputes all successful cases, repeats rejection checks and applies the independent arithmetic/behavior assertions. It writes no files. A changed digest requires a fresh evaluation; do not relabel this record as current without rerunning it.

The native output validator reconstructs with the same calculator, so its agreement is not an independent mathematical oracle. The separate expected arithmetic and behavior checks provide bounded additional evidence. No real source truth, complete institutional workflow coverage, professional acceptance, legal approval, deployment acceptance or execution authority is established. No trade, posting, external delivery or other professional action occurred.

Final replay recorded `2026-09-20T23:19:06.659578+00:00`: all nine cases and 29 independent assertions passed under the privacy-repaired helper. Only the two tracked `native_integrity.py` hashes changed; the other six implementation files, original evidence JSON and numerical expectations remain unchanged. [investment-final-replay.json](investment-final-replay.json) records current hashes, explicit expected helper changes, actual case/assertion results and the adapted replay command. The original JSON remains historical evidence with its original hashes. This bounded replay establishes no source truth or professional/deployment acceptance.
