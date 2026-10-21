---
name: model-roll-forward-auditor
description: >-
  Audit a financial model's roll-forward between two versions by deterministically checking that
  each line item's prior-period ending balance ties to the current-period opening balance within
  tolerance, and flagging continuity breaks with cited evidence, as a review packet for an
  investment-banking analyst. Use when an analyst asks to "audit the model roll-forward", "check
  the opening balances tie to last version", "did anything break when we rolled the model", or
  "reconcile prior close to current open". HARD BOUNDARY: R2 model/decision-support — it checks
  balance continuity only; it NEVER opines on valuation or fair value, approves or validates the
  model, or confirms the model is correct; the deal team owns model sign-off. MNPI/information-
  barrier controls apply. Routes document version diffs to document-version-comparator.
license: MIT
compatibility: Portable local Python 3 stdlib; authorized supplied JSON works offline. Optional connected data and workbook tools require deployment-specific access and permitted use; none are bundled.
metadata:
  aws-fsi-category: "Investment Research"
  aws-fsi-skill-type: "Artifact-creation skills"
  aws-fsi-risk-tier: "R2"
  aws-fsi-archetype: "Model & calculate"
  aws-fsi-agent-pattern: "Interactive production copilot"
  aws-fsi-delivery-wave: "Wave 5 - 2026 industry expansion"
  aws-fsi-action-mode: "Draft-only; no system-of-record change"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "existing-updated"
  aws-fsi-human-approval: "external-delivery"
  aws-fsi-data-classification: "Highly Confidential (MNPI / client-confidential)"
  aws-fsi-jurisdictions: "Select applicable reporting, geography and institutional profiles; no universal conduct regime"
  aws-fsi-owner: "Investment Research"
  aws-fsi-primary-user: "Research analyst / research model reviewer"
  aws-fsi-version: "0.2.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Model Roll-Forward Auditor

## Phase 1 method and validation boundary

Retained through Phase 1 until shared-check and future reviewer parity is established. This is a supplied-balance continuity checker only: it does not read/update a workbook, compare formulas, assess assumptions or provide independent assurance. Require unique line items, model version IDs, explicit balances (null means structural break) and nonnegative explicit tolerances. A tied subset does not establish model correctness.

The native result is a closed calculation record. Retain the original input separately and validate with `python3 scripts/validate_output.py RESULT.json --input ORIGINAL.json`; `--selftest` loads both bundled examples. Computation validates input first. Finite JSON numbers, valid dates, supported domains and unique identifiers are enforced; duplicate JSON keys are rejected. Output validation reconstructs from the original and rejects omitted, altered or extra results, including flags/counts/statuses. Keep author narrative and workflow envelopes outside the native result. Source binding establishes deterministic fidelity to supplied inputs, not source authenticity, data rights, economic validity, institutional acceptance or independent assurance.

See [controls](references/controls.md) and [input schema](scripts/validate_input.py) before using the numerical helpers.


## Purpose and outcome
Given a financial model's prior and current versions, deterministically check that each line
item's prior-period ending balance ties to the current-period opening balance within tolerance,
and flag every continuity break with cited evidence. A successful output is a continuity-audit
packet an analyst reviews; valuation opinions and model sign-off remain the deal team's.

## Use when
- "Audit the model roll-forward", "check the opening balances tie to last version".
- "Did anything break when we rolled the model", "reconcile prior close to current open".
- A reviewer needs a consistent, cited roll-forward continuity check.

## Do not use
- The user wants a **valuation/fair-value opinion** or **model approval/validation** → out of
  scope; the deal team decides.
- The user wants a **document/version content diff** → route to
  `document-version-comparator`.
- The user wants **capital-structure mapping** → `issuer-capital-structure-mapper`.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). Emits an audit packet with a durable
`audit_id`; it does not approve the model or opine on value.

## Inputs and prerequisites
- The **model** (id, prior/current versions) and **roll_forward** line items (prior_ending,
  current_opening, tolerance). Schema: [scripts/validate_input.py](scripts/validate_input.py).
- Tolerances are documented inputs. See [references/domain-rules.md](references/domain-rules.md).

## Source hierarchy
See [references/source-map.md](references/source-map.md). The two model versions are the evidence;
cite each break to the line item and both versions.

## Workflow
1. **Validate input** — run `validate_input`; confirm numeric prior/current balances.
2. **Compute (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py): per line item, residual
   = current_opening − prior_ending; break if |residual| > tolerance.
3. **Assemble the audit** — per item: prior ending, current opening, residual, tie status, citation.
4. **Suggest disposition** — `tied` or `breaks-for-review` (a triage suggestion, not a sign-off).
5. **Validate output** — run [scripts/validate_output.py](scripts/validate_output.py) for the
   residual identity, the no-valuation/no-approval screen, and disclaimer.

## Validation loop
`validate_input` before, `validate_output` after. If a residual does not equal current_opening −
prior_ending, or the text contains valuation/approval language, **fix or fail closed**.

## Human approval
`external-delivery`: the audit may be produced, but external delivery requires human sign-off; no
valuation opinion or model approval is ever made by this skill.

## Failure handling
- **Missing balance** → the item is not-tieable; flag it; do not assume continuity.
- **Missing tolerance** → use exact match (tolerance 0) and state it; never invent a tolerance.
- **Sign/label mismatch** (item present in one version only) → flag as a structural break, not a
  numeric one.
- **Tool timeout** → partial + incomplete flag.

## Output contract
1. **Summary** — model id, versions, item count, break count, disposition.
2. **Line items** — prior ending, current opening, residual, within-tolerance flag, citation.
3. **Breaks** — items exceeding tolerance and structural breaks.
4. **Machine-readable** — items + `audit_id`.
5. **Standing disclaimer** — "Roll-forward continuity check only; not a model approval, a
   validation, or a valuation/fair-value opinion. The model has not been approved."
See [references/controls.md](references/controls.md).

## Privacy and records
MNPI / client-confidential. Enforce information barriers; deal-team only. Retain audit + citations
+ versions. Log read + external-delivery approval. Never cross the wall.

## Gotchas
- **Continuity is not correctness.** Balances tying says nothing about whether the model or the
  valuation is right.
- **A break is a review prompt, not an error to fix** here — the analyst investigates.
- **Tolerance is documented**, never guessed; state whether exact match was used.
- **Never opine on value or approve the model** — continuity evidence only.

## Category ownership — Phase 1

Primary owner: Investment Research. This category migration preserves the existing
native method, evidence rules and approval boundaries. It does not add connectors,
method coverage or institutional acceptance. Research/publication and transaction
contexts remain explicit; downstream consumers use the original validated artifact.

## Shared Phase 1 evidence standard

Read [the evidence and control standard](references/evidence-standard.md) for identity,
knowledge timing, permission use, detached source binding and professional acceptance
boundaries. The package retains its native schema; no universal adapter is implied.
