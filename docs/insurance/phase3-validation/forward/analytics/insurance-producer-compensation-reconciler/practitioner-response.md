# Practitioner response — insurance-producer-compensation-reconciler

Synthetic evaluation case; not a live insurance engagement.

Case `insurance-producer-compensation-reconciler-forward-01` | Harbor Mutual (synthetic) | Producer compensation analyst | object `AGENCY-M7` | SYNTHETIC-STATE / commercial-package | as of 2026-09-18.

AG7’s evidenced earning trigger and 13.75% rate generate E1 gross commission $13,750.48125 and E2 $5,500. Clause 7’s evidenced 25% reversal of E1 produces a negative $3,437.6203125 chargeback, using E1’s original 65%/35% splits (agreement §1–2; events §1–2).

Period net earned is $15,812.8609375. P65 receives $10,278.359609375 and P35 $5,534.501328125. Relative to reported controls, calculated-minus-reported differences are −$0.000390625 and +$4.501328125 respectively. All figures retain unrounded arithmetic; this is earned activity, not a payable or cash balance roll-forward (reported §1).

P65’s reported $10,278.36 is consistent with ordinary cent rounding, but no approved payout rounding policy was supplied, so the exact difference remains visible. P35’s $5,530 control needs substantive source/control reconciliation. Distribution finance should identify the difference and document the rounding/settlement policy before disposition. No payment, fiduciary withdrawal, licensing decision or producer communication occurred.

Evaluation chronology: the initial native mapping linked the agreement and clause evidence but omitted the newly explicit chargeback_basis field, so the helper withheld the reversal and period totals. A separate mapping supplement places the already supplied clause 7 entitlement in that field without changing raw evidence or expectations. Replay returns the values above and needs-review status. Original and supplemented inputs and outputs are retained.

Native disposition: **needs-review**, completeness **complete**, evaluability **evaluable**. Retained native artifact: [mapping-replay/result.json](mapping-replay/result.json). Raw source register and exact section mapping: [mapping.json](mapping.json). All evidence is supplied synthetic v1, unauthenticated. Human review remains required; approval not requested and execution not performed.
