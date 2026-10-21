# Cedar Harbor FNOL workflow review — draft, 20 September 2026

Mina Chen owns this fictional insurer's commercial-property FNOL sandbox review under REV-4 v4. Sources: OPS-7 v7 (18 September) and API-3 v3 (17 September), preserved in `raw-sources.json`. This review supports a pilot design decision only.

## Process and source contract

Current normal route: intake operator records and checks the document (14 human / 25 elapsed minutes). Current exception route: that same intake, then Mina's exception queue (18 additional human / 120 additional elapsed minutes), ending in a source-reconciled draft. Normal/exception shares are workshop assumptions of 80%/20% for all synthetic single-location property FNOL submissions.

Target normal route: extraction prepares a draft, then a human checks it (7 human / 12 elapsed minutes for review). Target exception route: extraction failure goes to Mina's manual recovery queue (20 human / 90 elapsed minutes), which reconciles the source and completes the draft. The target shares are 90%/10%. They are proposed scenario assumptions, not measured improvement.

Extraction is bounded to two attempts with a one-minute timeout each. OPS-7's three-minute aggregate extraction slot already includes both attempts and dispatch overhead; do not multiply it by two. Retain document hash, actual attempt count, timeout events and operator receipt. The proposal reads deidentified snapshots under DOC/API-3, fnol-doc-v2, with Elena Park as owner; both attempts use the same snapshot. Supplied access/purpose review statements do not prove a live connector or authenticate institutional approval. There is no proposed core write or autonomous coverage/claim decision.

## Scenario comparison

| Design | Normal human / elapsed | Exception human / elapsed | Weighted human | Weighted elapsed |
|---|---:|---:|---:|---:|
| Current | 14 / 25 min | 32 / 145 min | 17.60 min | 49.00 min |
| Target | 7 / 15 min | 20 / 93 min | 8.30 min | 22.80 min |

Native source: `workflow-complete.output.json`, `results.paths` and `results.weighted_minutes`. Independent check: current human = .8×14 + .2×32; target elapsed = .9×15 + .1×93. Scenario reductions are 9.30 human and 26.20 elapsed minutes per submission. No staffing, cost saving, throughput, critical-path or production performance claim follows from these serial estimates.

API-4 v4 (19 September) changes the schema to fnol-doc-v3 and explicitly lacks access review. `workflow-access-gap.output.json` correctly returns needs-data and nulls all path/weighted times. Preserve the design but do not apply API-3's approval to v3. Elena must supply the v3 scope review before a dependent pilot recommendation.

## Pilot decision and evidence required

Proposal: Mina and Elena review the two route diagrams above, test successful extraction, first and second attempt failures, timeouts and operator receipt, and record actual route shares and handling times for the same population. Mina should check accessibility and exception usability; Elena should confirm least-privilege snapshot access and audit retention under institution policy. Representatives must assess whether the synthetic population represents actual intake variability. Claims staff retain coverage and disposition decisions. These native artifacts pass structural/recomputation validation; they do not authorize implementation, system access, customer communication or a claim action.
