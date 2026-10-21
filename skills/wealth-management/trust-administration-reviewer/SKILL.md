---
name: trust-administration-reviewer
description: >-
  Review one trust's governing-document evidence, fiduciary and beneficiary records, dated obligations, distribution request packets and principal/income cash reconciliation. Use for an administrator's source-bound trust review and specialist question list. Requires human legal applicability and authority evidence; never decides entitlement, classifies by law, approves a distribution, pays, files or changes trust records.
license: MIT
compatibility: Amazon Quick Desktop; approved read-only trust, custodian, document and policy sources. Bundled Python reads supplied JSON and prints a draft; no network or production integration.
metadata:
  aws-fsi-category: "Wealth Management"
  aws-fsi-skill-type: "Analysis and evaluation skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Analyze & review"
  aws-fsi-agent-pattern: "Interactive decision-support copilot"
  aws-fsi-delivery-wave: "Wave 9 - wealth management P3"
  aws-fsi-action-mode: "Draft-only; no system-of-record change"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Highly Confidential (customer NPI/PII)"
  aws-fsi-jurisdictions: "US (default); actual state-law applicability requires supplied human legal review"
  aws-fsi-owner: "Wealth Management trust administration & fiduciary oversight"
  aws-fsi-primary-user: "Trust administrator / fiduciary accountant / trust legal reviewer"
  aws-fsi-version: "0.2.0"
  aws-fsi-recertification-date: "2027-09-17"
---

# Trust Administration Reviewer

## Purpose and outcome
Create a draft review of one trust's governing evidence, people, duties, cash ledger and
open distribution requests. Show exactly what reconciles, what remains unknown, and which
source or professional review is needed next. This supports administration; it makes no
legal, entitlement, investment or payment decision.

## Use when
- Prepare a trust administration review from governing documents and current records.
- Reconcile cash and professionally supplied principal/income allocations.
- Assemble outstanding distribution requests, authority/conflict evidence and dated duties.

## Do not use
- Creating/amending a trust, deciding document precedence, legal validity or applicable law.
- Determining beneficiary entitlement, approving or paying distributions, filing returns,
  authenticating authority, changing beneficiaries or exercising a power to adjust.
- Combining trusts, household planning, family governance, investment selection or performance.
- FX, accrual accounting, noncash journals or partly settled transfers in transit.

## Inputs and prerequisites
Read [references/schema.md](references/schema.md). Use one USD trust, a matching trust-capacity
engagement, current policy, explicit coverage/upstream issues and individually sourced records.
The envelope household_id is trust:<trust_id>, a collection marker. Each row must identify the
same trust; beneficiary records retain their separately reviewed actual household IDs.

Obtain a current human legal profile covering applicable law and every governing document,
plus clause locators, reviewed fiduciary appointments and authority scope. A named trustee,
beneficiary or reviewer is not proof of authority. Preserve competing evidence and open issues.

## Source hierarchy
Use governing instruments/amendments/orders with the responsible professional's applicable-law
and precedence review; trust/custodian ledgers and balance statements; actual beneficiary/request
records; and the firm's current service/review policy. Dates and classifications are supplied facts.
Public guidance is orientation only. See [references/source-map.md](references/source-map.md).

## P5 source and recipient quality gate
Before treating model-created structured input or a recipient draft as reviewed,
follow [references/quality-gate.md](references/quality-gate.md). Inventory every
input field against detached source evidence and obtain a separate reviewer’s
field decisions. Preserve unknowns as null; a missing review stays pending.
Never create your own independent reviewer identity or approval to pass a gate.
Create one draft per exact recipient set, including internal colleagues, from the
supplied access registry. Keep the full input, review receipt and withheld details
in a separate restricted work area. Run the combined gate and verify the actual
final bytes before handoff; native calculator validation alone is insufficient.
If no independent reviewer or permission registry is available, deliver a clearly
pending internal working draft and the missing-evidence list to the authorized
reviewer. Do not describe it as cleared for any wider audience.

## Workflow
1. Triage the requested review. Route household planning, estate intentions, family governance,
   legal adjudication and operations to their proper workflows. Confirm one-trust scope.
2. Extract only supported documents, clauses, people, appointments, powers and dated duties.
   Read [references/domain-rules.md](references/domain-rules.md) before mapping financial records.
   Preserve the legal reviewer's precedence and joint-action assessment; do not generate it.
3. Separate settled, pending and cancelled cash activity. Map principal/income only from supplied
   professional allocations. Tie independent opening/closing balances and internal transfer legs.
   Identify cash inventory references so cash is counted once in gross asset totals.
4. For each distribution request, link actual prior/current payments, beneficiary evidence,
   authority clauses, required packet documents and dated conflict review. Keep request intent
   separate from actual classified payments and from any entitlement or approval decision.
5. Run `python -B scripts/validate_input.py REQUEST.json`, then
   `python -B scripts/calculate_or_transform.py REQUEST.json`, then
   `python -B scripts/validate_output.py OUTPUT.json`. Correct errors from sources; preserve gaps.
6. Present [assets/output-template.md](assets/output-template.md) and the reconstructed JSON.
   The responsible administrator/legal reviewer checks extraction, classifications and sufficiency.
   Prepare only the evidence handoffs in [references/handoffs.md](references/handoffs.md).

## Human review and failure handling
Every result requires human review, remains not-delivered, and records action_taken=false.
Malformed or cross-trust input, stale registry evidence, impossible ledger identities and duplicate
cash references reject. Unknown classifications, source gaps, legal/authority uncertainty,
reconciliation differences and conflicts produce needs-data. Never fill them with inferred law,
zero amounts, a title-based permission or a generic approval string.

A documented component means supported review evidence is present; it does not authenticate
source truth, professional approval or the claimed legal effect. Unresolved upstream issues
prevent a clean legal/authority/distribution qualification. See [references/controls.md](references/controls.md).

## Output and validation loop
The common evidence artifact retains scope, trust identity, source registry, full snapshot/hash,
policy and originating issues. It contains component cash bridges, asset evidence, legal/authority
review states, people/clauses, dated obligations, remaining distribution amounts and specialist
next actions. Unknown supported values remain null; raw observations are kept separately.

Review-ready means no configured supplied-data finding remains for professional review. It is
not compliance, entitlement, completed administration or authority to execute. The illustrative
cash-after-open-requests scenario is not a distribution recommendation or a payment schedule.

Run [evals/evals.json](evals/evals.json) and the bundled regression tests after changes. Local
checks test contracts, arithmetic and reconstruction. Model extraction/routing, professional
acceptance and production integrations remain separate, uncompleted release gates.

## Privacy, records and gotchas
Use masked names and opaque IDs. Keep beneficiary-specific records within the approved trust
team audience; no family member gains access from a governance role or relationship label.
The CLI prints a local draft and configures no storage, access, retention or external delivery.

- Cash principal/income are classifications of the same cash, not additional assets.
- Reclassification moves between buckets but changes total cash by zero.
- Prior-period request payments are already in opening cash; pending payments are not settled cash.
- Cash-ledger boundaries are not investment-performance external-flow classifications.
- Missing source citations block local supported labels as well as global readiness.
