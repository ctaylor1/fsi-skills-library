# Insurance artifact and handoff contract

This is a repository engineering convention, not an insurance regulation or evidence of source authenticity. Read it when a package emits `artifact`, accepts an upstream artifact, or prepares a typed handoff. Canonical code is `shared/insurance/insurance_contract.py`; importing packages carry an identical local copy so exports remain self-contained. `tools/sync_insurance_contract.py --check` detects drift.

## Context and provenance

Inputs use `context.capacity` (the role in which the user acts), `represented_party` and `object_id`. Add jurisdiction and line of business when relevant. An analyst representing a claimant has different access and decision authority from a carrier adjuster. A role label never grants access. Object identity is the policy, claim, portfolio, submission or dataset under review, not an invented customer identity.

Supply `as_of` and `sources: [{source_ref, version, as_of?}]`. References and versions must identify the supplied material; they do not prove that material is authoritative. Missing fields stay unknown, create unresolved issues and prevent a complete/evaluable artifact. Cite applicable contract, rule/configuration and source versions in domain output. If a receiver changes the represented party or object, explicitly explain the scope transition and apply its own access controls.

## Four separate states

- `completeness`: `complete`, `partial`, `unknown` describes the declared input/output scope.
- `evaluability`: `evaluable`, `partial`, `not_evaluable` describes the requested calculation/check. A fully evaluated break can still require review.
- `approval: not_requested` means this deterministic artifact supplies no business approval.
- `execution: not_performed` means it records no externally executed action.

Neither a complete file nor an evaluable calculation means coverage is confirmed, a reserve certified, a claim settled, or an action authorized. Domain methods must supply their own missingness and evaluability; the shared helper additionally enforces context/provenance and upstream status floors. Preserve `unresolved_issues` in all handoffs. The helper cannot certify a method or infer omitted domain requirements.

Explicit input `unresolved_issues` conservatively keeps the receiving artifact partial.
These are inherited open input questions, not an assertion that every newly computed
finding prevents a completed check. A known, fully evaluated break may remain a domain
finding while requiring review; do not silently remove inherited unknowns to promote readiness.

## Content binding and validation

`build_artifact(input_doc, output, producer=..., artifact_type=..., completeness=..., evaluability=..., issues=...)` returns an envelope to attach at `output.artifact`. Canonical finite-JSON SHA256 hashes bind the input, output (excluding the artifact key) and envelope. These detect content mismatch; anyone able to replace content can recompute a hash. `evidence_assurance` is always `supplied_not_authenticated`. No signature, authorization, source authenticity, freshness, or system-of-record reconciliation is implied.

`validate_artifact(envelope, input_doc=..., output=...)` rechecks supplied content and status floors. Pass both objects when available. Without them it checks only envelope consistency and metadata. A validated envelope is not an independently verified output; run the package's native input/output validation and domain recomputation as well.

`make_handoff(source_artifact, target_skill=..., target_input=..., requested_output=...)` retains the source artifact and issues within receiver input. `validate_handoff(packet, target_skill=..., receiver_validator=...)` invokes the actual receiver validator; it accepts either an error list or `(errors, warnings)`. A producer's assertion that validation passed cannot replace that call. Handoffs grant no execution authority. Receiving packages must propagate upstream incompleteness and unresolved issues into their own artifacts.

## Financial and temporal meaning

`amount` uses finite decimal values; booleans, missing values, NaN and infinity are rejected. Unknown never becomes zero. Before arithmetic, each domain must establish grain/object, currency, unit, gross/net/ceded basis, period/date basis, valuation date and definition version. Incompatible rows are partitioned or reported as non-comparable; do not sum different currencies or silently apply FX. Any explicit conversion needs rate, date, source and rounding policy.

Keep written/earned premium, paid/incurred loss, case/aggregate reserves, TIV/insured limit, indemnity/expense and gross/ceded/net distinct. A ratio must name both its numerator and denominator. Missing and explicit zero have different meanings.

Use `iso_date` for strict calendar dates and `timestamp` for instants with an explicit timezone. Do not infer a timezone or truncate an invalid timestamp. Observation/as-of, policy effective/expiry, event occurrence, report, accounting and valuation dates describe different facts. CAT model results additionally require event, peril, footprint, exposure snapshot, model version/run, currency and financial/loss-statistic basis. Summing marginal quantiles does not produce a portfolio quantile.

## Source anchors and jurisdiction

- [NAIC AI bulletin, adopted December 4, 2023](https://content.naic.org/sites/default/files/inline-files/2023-12-4%20Model%20Bulletin_Adopted_0.pdf): governance, data lineage, validation and third-party oversight expectations. Actual jurisdiction adoption and law must be checked; this contract does not certify compliance.
- [ASB current standards](https://www.actuarialstandardsboard.org/standards-of-practice/): select the applicable current data-quality, modeling, communications and actuarial standard with a qualified reviewer.
- [NAIC statutory accounting overview](https://content.naic.org/insurance-topics/statutory-accounting-principles): U.S. SAP has state prescribed/permitted variations. Do not treat SAP, U.S. GAAP and IFRS as interchangeable bases.

These are reference anchors reviewed September 18, 2026. Local workflow controls and status vocabularies above are design choices; they are not quoted regulatory mandates.
