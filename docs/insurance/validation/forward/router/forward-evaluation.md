# Independent insurance router forward evaluation

Date: 2026-09-18. The four natural-language requests were provided by the evaluating parent agent. The evaluating assistant read the router skill, routing registry, input/source/control/handoff references and migration map, and then selected explicit intents. The routing script is not a natural-language classifier. No implementation plan, audit report, evaluation specification, test source, or prior expected answer was opened. The router test suite was executed only after the independent four case routes had been saved.

Each numbered JSON request retains the exact request text. The adjacent route JSON is exact stdout from `route.py`; stderr is retained separately. The adjacent validation text is the exact validation stdout/stderr. The execution manifest contains exact argument vectors, return codes and inspected router resource hashes. No insurance source documents or underlying numerical datasets were supplied, so these are routing and scope responses, not completed specialist analyses.

## Practitioner-facing responses

### 1. Carrier pricing actuary: personal-auto rate adequacy

Your requested deliverable is a personal-auto rate-adequacy analysis. The loss ratio increased by 13 percentage points, but the figures supplied do not establish the indicated rate change. The router returns **capability-gap** for `pc-rate-adequacy-analyzer`; this analysis is not implemented in the current library.

The catalog's `pc-reserving-analysis-assistant` can support a separately scoped P&C loss-development/reserving exercise using paid triangles, a valuation date, currency, and approved methods/tail assumptions. It does not complete rate adequacy. `insurance-rating-worksheet-builder` applies supplied approved rates and factors; it does not calculate a pricing indication. No supporting workflow was automatically launched. Retain the triangles as paid-loss evidence, the earned-premium basis, and the precise periods/versions of the renewal-rate evidence for an appropriately scoped pricing review. Jurisdiction and operative product/rate context remain unknown.

### 2. Policyholder: denied homeowners fire claim

This is a P&C claimant dispute. The router returns **capability-gap** for `claimant-dispute-packager`: the library does not currently implement the requested homeowners appeal preparation. Your claimant role and homeowners/fire context are preserved; the health-benefit appeal package does not apply.

The policy, denial letter and fire report are relevant supplied-source candidates, but their contents and versions have not been provided here. I cannot identify the denial grounds, evaluate the policy against those grounds, or produce a source-grounded appeal from this request alone. Retain those documents and their references, the actual property/claim context, and the applicable jurisdiction and appeal/deadline text when provided. The router has not determined coverage or filed an appeal.

### 3. Ceded reinsurance analyst: compare two property treaties

Use `reinsurance-contract-reviewer` for the requested treaty wording comparison, acting for the cedant. The router returns **routed** to that contract-review owner; the requested work is comparison of the two treaties' terms.

Supply the exact treaty versions, operative periods, contract type and source-located clauses, along with the comparison question. The shared “10 million excess of 5 million” description alone cannot establish whether the coverage wording is equivalent; currency and precise treaty basis also remain unstated. The receiving package must validate its own native input before review. The router has selected an owner but has not performed the clause comparison.

### 4. SIU manager: portfolio suspicious-claims spike

Your requested deliverable is portfolio-level driver analysis before individual investigations. The router returns **capability-gap** for `insurance-fraud-pattern-analyzer`, which is not implemented. The existing `insurance-fraud-referral-reviewer` is scoped to a single claim's referral review and cannot fulfill this portfolio request.

`insurance-data-reconciler` is offered only as an evidence-preparation option. With actual metrics, period/basis definitions, source versions and reconciliation configuration, it may help establish whether the reported quarter-to-quarter figures are comparable. That check would not identify the drivers or establish that any claim is fraudulent. The request does not supply the underlying portfolio records or the line of business, and no individual investigation or referral was started.

## Observations

- All four initial route commands exited 0 and all four saved outputs passed the router's recomputation validation with zero errors.
- The router's own 11 tests passed after these four forward cases were executed.
- No runtime errors or ambiguous intent selection arose in these four cases. Clear ownership distinctions were available in the local instructions.
- The assistant performed the natural-language interpretation. The deterministic script executed the explicit selected intent and retained original request text, but did not independently classify the request text.
- Initial outputs intentionally omitted `available_skills` and therefore say `availability: unverified`. This is explicitly allowed by the skill. The initial local package inventory had pre-rename names during an active parent integration; this is a transient integration observation, not treated as a router defect.
- A route output is not target input. No native specialist payload was manufactured from absent source documents, and no receiving specialist input validator was run.

## Installation availability

Pending final installed-name replay. The initial inventory is retained in `initial-local-insurance-inventory.json`.
