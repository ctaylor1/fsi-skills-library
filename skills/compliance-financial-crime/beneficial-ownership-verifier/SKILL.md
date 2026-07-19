---
name: beneficial-ownership-verifier
description: >-
  Map a legal entity's ownership and control structure, compute each natural person's
  effective (indirect) ownership through intermediate entities, reconcile the computed
  beneficial owners against the entity's declaration, identify gaps (undeclared owners,
  unsatisfied control prong, missing/expired evidence, percentage mismatches), and apply
  the configured jurisdiction pack's thresholds, control-prong rule, and effective dates.
  Use when a KYC or legal-entity onboarding analyst asks "who are the ultimate beneficial
  owners", "does the declared UBO list match the ownership chart", "which owners cross the
  25% threshold", or needs a source-linked UBO verification pack. HARD BOUNDARY: produces
  evidence and a recommended readiness band ONLY; it NEVER determines or confirms beneficial
  ownership, approves or rejects onboarding, verifies identity, closes a KYC case, files a
  beneficial-ownership or suspicious-activity report, or writes any system of record — a
  human adjudicator decides.
license: MIT
compatibility: Amazon Quick Desktop; requires KYC/AML, sanctions/PEP, entity-resolution, document-intelligence, approved-source-retrieval, and case-management MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Compliance & Financial Crime"
  aws-fsi-skill-type: "Guidance or domain-expertise skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Domain workflow"
  aws-fsi-agent-pattern: "Interactive decision-support copilot"
  aws-fsi-delivery-wave: "Wave 3 - regulated casework"
  aws-fsi-action-mode: "Read-only analysis"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Restricted (AML/BSA — SAR confidentiality; tipping-off controls)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Compliance & Financial Crime (FIU)"
  aws-fsi-primary-user: "KYC / legal-entity onboarding analyst"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Beneficial Ownership Verifier

## Purpose and outcome
Given a legal entity's ownership/control structure and its self-declared beneficial owners,
compute each natural person's **effective ownership** of the root entity by multiplying
percentages along every chain and summing across chains, identify **candidate beneficial
owners** under the ownership prong (≥ the jurisdiction threshold) and the control prong
(senior managing officials), and **reconcile** that computed set against the declared list.
A successful output is a source-linked **verification pack**: the ownership computation,
the identified UBOs with evidence citations, an enumerated gap list, the jurisdiction
requirements applied, and a **recommended readiness band** for a human KYC analyst to
adjudicate. The determination, approval, and any filing remain human.

## Use when
- "Who are the ultimate beneficial owners of this entity?"
- "Does the declared UBO list match the ownership chart / cap table?"
- "Which owners cross the 25% (or configured) threshold once you follow the indirect chains?"
- "Is the control prong satisfied and is every UBO supported by current evidence?"
- An analyst needs a consistent, cited UBO reconciliation to attach to an onboarding case.

## Do not use
- The user wants a **beneficial-ownership determination**, an **onboarding approval/rejection**,
  a **case closure**, or a **BOI/SAR filing** → out of scope. Provide the pack and route to the
  human adjudicator / authorized system.
- **First-line CDD screening** (completeness, identity, sanctions/PEP, escalation need) →
  `kyc-customer-due-diligence-screener`.
- **Sanctions/PEP name-match adjudication** on an owner → `sanctions-match-adjudicator`.
- **Adverse-media** assessment on an owner → `adverse-media-investigator`.
- **Assembling the higher-risk EDD package** (source of funds/wealth, geography) →
  `enhanced-due-diligence-packager`.
- **Recalculating the customer risk rating** → `customer-risk-rating-reviewer`.
- **Onboarding document completeness** (signatures, expiries) → `customer-onboarding-document-checker`.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill emits a verification pack
with a durable `verification_id`; downstream screening, EDD, risk-rating, and SAR skills
consume it. It must not duplicate their screening, packaging, or filing steps, and it never
reaches a disposition.

## Inputs and prerequisites
- The **root legal entity** and its ownership/control graph: `nodes` (entities and natural
  persons), `ownership_edges` (owner → owned, percentage, source_ref/doc_id), and
  `control_edges` (controller → entity, role, type).
- The entity's **declared UBOs** (person, basis, declared percentage, supporting doc).
- **Supporting documents** (cap tables, registry filings, officer lists) with issue/expiry
  dates for freshness checks.
- The **jurisdiction pack** `config` (threshold, control-prong rule, document requirements,
  effective date). Schema: [scripts/validate_input.py](scripts/validate_input.py).
- Read access to KYC/AML, entity-resolution, document-intelligence, and approved-source
  retrieval (see [references/source-map.md](references/source-map.md)).

## Source hierarchy
See [references/source-map.md](references/source-map.md). Authoritative ownership evidence
(certified cap tables, corporate registry filings, trust/partnership deeds) outranks the
customer's self-declaration; the declaration is the object being reconciled, never the
source of truth. Cite every computed owner and every gap to a source row and date.

## Workflow
1. **Scope & validate** — confirm the root entity, jurisdiction pack, and as-of date;
   load the graph and declarations; run `validate_input` (fail closed on broken graph
   references or non-numeric percentages; note data-quality warnings).
2. **Compute effective ownership (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py) to multiply
   percentages along chains and sum across chains for every natural person, flagging any
   circular ownership. Identify ownership-prong UBOs (≥ threshold) and control-prong persons.
3. **Reconcile** — compare the computed UBO set against the declared list; enumerate gaps
   (undeclared owner, unsatisfied/undeclared control prong, unsupported declaration,
   percentage mismatch, missing/expired document), each with its subject and evidence.
4. **Apply jurisdiction requirements** — record the threshold, control-prong rule, document
   freshness window, and requirements effective date from the config version used.
5. **Recommend readiness (not a decision)** — map the gap set to a readiness band
   (`Complete-for-review` / `Remediation-needed` / `Escalate`) per the documented mapping in
   [references/domain-rules.md](references/domain-rules.md). This is a triage recommendation
   for a human, explicitly **not** an approval or a beneficial-ownership determination.
6. **Write the pack** — plain-language summary + the computation + identified UBOs with
   citations + gaps + jurisdiction requirements + the recommended readiness + the standing
   disclaimer.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py)
after. The output check confirms: every identified UBO has a cited evidence row, the
readiness band maps deterministically from the gap set, no decision/closure/filing/approval
language is present, and the standing disclaimer is included. **Fail closed on any miss** —
do not present a pack that trips the screen.

## Human approval
`required` (R3): a human KYC analyst must adjudicate before any regulated decision —
beneficial-ownership determination, onboarding approval/rejection, risk-rating change, case
closure, or BOI/SAR filing. The skill never makes or communicates such a decision and never
writes a system of record. No approval is needed for the analyst's own read of the pack.

## Failure handling
- **Broken graph / non-numeric percentage** → `validate_input` errors; stop and fix inputs.
- **Circular ownership** → flag it, skip the affected chain, and surface it as a blocking
  data-quality gap; do not silently drop ownership.
- **Ownership sums over 100%** for an owned entity → surface as a data-quality gap; do not
  normalize silently.
- **Ambiguous entity/person identity** → stop and confirm via entity resolution; never
  reconcile against the wrong party.
- **Missing documents / thin evidence** → compute what the data supports, flag the rest as
  `missing_document`; never assert an owner is "verified".
- **Stale/conflicting sources** → cite both and flag for the reviewer; the authoritative
  record outranks the declaration but conflicts are surfaced, not resolved.
- **Tool timeout** → return the computation completed so far with a clear "incomplete" flag.

## Output contract
1. **Summary** — entity, jurisdiction, as-of, threshold, count of identified UBOs,
   recommended readiness band.
2. **Computation** — every natural person's effective ownership with the contributing chain.
3. **Identified UBOs** — per person: basis (ownership/control), effective percentage or
   role, declared? flag, reason, and cited evidence rows.
4. **Gaps** — per gap: type, subject, detail, severity, and evidence where applicable.
5. **Jurisdiction requirements applied** — threshold, control-prong rule, freshness window,
   effective date, authority, and config version (for reproducibility).
6. **Machine-readable** — computation + UBOs + gaps + `verification_id` for downstream skills.
7. **Standing disclaimer** — "Verification evidence and recommendations only; not a
   beneficial-ownership determination or KYC/onboarding approval. No case has been approved,
   closed, or filed, and no system of record has been updated. Human adjudication is required."
See [references/controls.md](references/controls.md).

## Privacy and records
Restricted (AML/BSA). Beneficial-ownership work can be tied to SAR activity — observe
**tipping-off** controls: never disclose to the customer that a gap, escalation, or filing
consideration exists. Minimize personal data to what evidences an identified UBO or gap;
mask identifiers where possible. Retain the pack + citations + config version per records
policy; log the read and any adjudication. Never exfiltrate customer or ownership data.

## Gotchas
- **A computed owner is not a confirmed owner.** Effective ownership ≥ threshold makes a
  person a *candidate* UBO for human adjudication — never state ownership "is verified".
- **Follow every indirect chain and sum them.** A person just under threshold on one chain
  can cross it once a second chain is added (the golden fixture's Jane Doe: 30% direct + 6%
  indirect = 36%). Missing a chain understates ownership.
- **The control prong is independent of ownership.** Under the US CDD rule at least one
  senior managing official is a UBO regardless of any 25% owner; an unsatisfied control prong
  is a blocking gap even when ownership is fully mapped.
- **The declaration is the object, not the source.** Reconcile the declaration *against* the
  authoritative records; never treat the customer's UBO list as evidence of itself.
- **Thresholds and control-prong rules are jurisdiction config**, versioned and owned by
  policy — never tune them to an entity. Record the config version so the pack reproduces.
- **Tipping-off is a real control.** Keep escalation and filing considerations internal to
  compliance; they never appear in customer-facing communication.
