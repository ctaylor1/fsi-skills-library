---
name: policy-wording-comparator
description: >-
  Compare insurance policy forms, endorsements, manuscript clauses, and form versions against
  approved or filed baseline forms; produce clause-level findings of material wording changes,
  additions, removals, conflicts, and coverage gaps with citations to both forms, plus reviewer
  questions and a suggested review track. Use when product counsel, underwriting, or compliance
  asks to diff two policy forms, check a manuscript endorsement against a filed form, review what
  changed between editions, or find wording conflicts and gaps before human review. This skill
  surfaces cited evidence and review questions only; it NEVER decides coverage, determines
  compliance, approves or clears a form for filing, files or binds a form, or closes the review —
  those are licensed-human / authorized-system actions requiring mandatory adjudication.
license: MIT
compatibility: Amazon Quick Desktop; requires policy-form/endorsement-repository, filed-approved-forms, document-intelligence (clause parsing), product-rules, and legal/compliance-reference MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Insurance"
  aws-fsi-skill-type: "Analysis and evaluation skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Analyze & review"
  aws-fsi-agent-pattern: "Interactive decision-support copilot"
  aws-fsi-delivery-wave: "Wave 3 - regulated casework"
  aws-fsi-action-mode: "Read-only analysis"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Highly Confidential (customer NPI/PII)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Insurance underwriting & claims"
  aws-fsi-primary-user: "Insurance product counsel / underwriting / compliance"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Policy Wording Comparator

## Purpose and outcome
Given a **subject form** (a policy form, endorsement, manuscript clause set, or new edition) and
a **baseline form** (the approved or filed form of record), align the two clause-by-clause,
identify **material wording changes, additions, removals, conflicts, and coverage gaps**, attach a
clause-level citation to **both** sides of every finding, and produce reviewer questions plus a
**suggested review track**. A successful output lets product counsel, an underwriter, or a
compliance reviewer see exactly what changed, why it may matter, and what to ask — while the
coverage, compliance, and filing **decisions remain with a licensed human**.

## Use when
- "Diff this endorsement against the filed CGL form and show me what changed."
- "What is materially different between the 04/2024 and 07/2026 editions of this form?"
- "Check this manuscript wording against our approved form and flag conflicts and gaps."
- A reviewer needs a consistent, cited wording-comparison pack to attach to a form-review file.

## Do not use
- The user wants a **coverage determination**, a **compliance/filing decision**, form **approval**,
  or the form **filed/bound** → out of scope. Produce evidence and route to licensed counsel /
  compliance and the authorized filing system.
- Plain-language **explanation of a single policy** (no comparison) → `policy-document-explainer`.
- Compare a customer's **needs/exposures** against policy terms for adequacy → `coverage-gap-analyzer`.
- Compare **expiring vs proposed renewal** terms for a customer explanation → `policy-renewal-reviewer`.
- **Reinsurance treaty** wording (attachment, reinstatements, recoverability) →
  `reinsurance-treaty-interpreter`.
- Compare **premiums/quotes** across carriers → `premium-quote-comparator`.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill emits a cited **comparison pack**
with a durable `comparison_id`; upstream underwriting/renewal skills request it, and the human
reviewer routes onward. It must not duplicate their decisions or take a filing/coverage action.

## Inputs and prerequisites
- A **subject form** and a **baseline form**, each with: `form_id`, `form_name`, `filing_status`
  (`filed` | `approved` | `draft` | `manuscript` | `proposed`), optional `edition_date`, and a
  non-empty `clauses[]` list.
- Each clause: `clause_id`, `clause_type`, `text`, `source_ref`; optional `heading`, `section`,
  `defines[]` (defined terms), `references[]` (clause_ids / terms it relies on). Schema:
  [scripts/validate_input.py](scripts/validate_input.py).
- `config_version` plus optional `config` (materiality rules) and `required_clause_types[]`
  (gap check). Read access to the form repository, filed/approved forms, and product rules.

## Source hierarchy
See [references/source-map.md](references/source-map.md). The **filed/approved baseline form** is
the position of record; the product-rules and materiality **config** is a versioned contract;
document-intelligence resolves clause boundaries and headings. Cite every finding to a specific
clause `source_ref` on **both** the subject and baseline side. Never substitute a drafter's summary
for the actual clause text; if a summary and the clause conflict, cite the clause and flag it.

## Workflow
1. **Scope & load** — confirm the subject and baseline forms and their `filing_status`; load both
   clause sets; validate with `validate_input` (fails closed on structural problems).
2. **Align clauses (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py) to join clauses by
   `clause_id`, classifying each as **added**, **removed**, **modified** (with a text-change ratio),
   or unchanged, and to detect **dangling references** (conflicts) and **missing required clause
   types** (gaps).
3. **Classify materiality** — each change is flagged `material` by clause type or text-change ratio,
   and `escalate` when it touches an escalation clause type (exclusion, insuring agreement, limit,
   coverage trigger, condition precedent), deviates from a **filed** baseline, or is a conflict/gap.
   Rules are versioned config, not per-form judgement (see [references/domain-rules.md](references/domain-rules.md)).
4. **Suggest a review track** — map the finding set deterministically to `No material changes` /
   `Standard review` / `Legal/compliance review required`. This is a **triage suggestion for a
   human**, explicitly not a coverage, compliance, or filing decision.
5. **Write the pack** — per material finding: plain-language change description, both-side evidence,
   and a reviewer **question**; plus the suggested track, the legal/compliance handoff when escalated,
   uncertainties, and the standing disclaimer.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py) after. The
output screen confirms: every material finding has cited evidence on both sides, no
decision/closure/filing/coverage language is present, the suggested track equals the deterministic
mapping from the findings, a legal/compliance handoff is present when the track is escalated, and
the standing disclaimer is present. **Fail closed** on any miss.

## Human approval
`required` (R3). A licensed human must adjudicate before any coverage or compliance conclusion, any
form approval, any filing, any bind, or any write to a system of record. The skill never decides,
approves, files, binds, or closes the review — it produces cited evidence and questions only. No
approval is needed for the reviewer's own read of the pack.

## Failure handling
- **Missing/duplicate clause_id** → error; cannot align reliably. Stop and surface it.
- **Baseline not filed/approved** → proceed but label the comparison "not against a form of record";
  do not present it as a filed-form deviation check.
- **Missing headings/`references`/`defines`** → align by `clause_id` only; mark conflict/gap checks
  that depend on the missing metadata as `not_evaluable` rather than asserting none exist.
- **Wrong or mismatched forms** (different product/line) → stop and confirm; never diff the wrong pair.
- **Stale/conflicting sources** → cite both; do not resolve silently.
- **Tool timeout** → return the alignments computed so far with a clear "incomplete" flag; no retry
  or step-up authorization is assumed.

## Output contract
1. **Summary** — subject vs baseline (ids, editions, filing status), counts of material findings,
   suggested review track.
2. **Findings** — per material finding: type (added/removed/modified/conflict/gap), clause type,
   plain-language change, both-side cited evidence, and the reviewer question.
3. **Not-evaluable** — checks skipped for missing metadata.
4. **Legal/compliance handoff** — present whenever the track is `Legal/compliance review required`.
5. **Machine-readable** — findings + evidence + `comparison_id` for downstream reuse.
6. **Standing disclaimer** — "Comparison evidence only; not a coverage, compliance, or filing
   determination. A licensed professional must adjudicate; no form has been filed, approved, or bound."
See [references/controls.md](references/controls.md).

## Privacy and records
May include customer NPI/PII in manuscript/specimen wording. Mask policy/account numbers to last 4;
minimize customer data in output to what evidences a finding. Retain the comparison + citations +
config version per records policy; log the read and any external-delivery approval. Never exfiltrate
form or customer data to unapproved destinations.

## Gotchas
- **A finding is not a decision.** Material changes justify *review*, never a coverage/compliance
  conclusion or a filing/approval action — those are the licensed human's.
- **"Filed" is not "compliant".** A deviation from a filed form raises a filing-review question; it
  does not mean the subject form is or is not compliant.
- **Add vs remove an exclusion cut both ways.** An added exclusion narrows coverage; a removed
  exclusion broadens it — both are material; describe the direction factually, do not judge it.
- **Alignment depends on stable `clause_id`s.** If the two forms renumber clauses, map ids first or
  added/removed findings will be noise.
- **Text-change ratio ≠ materiality.** A tiny wording change to an insuring agreement can be highly
  material; a large formatting change to a notice-of-address clause may not be. Clause type leads.
- **Do not tune materiality to the deal.** Thresholds come from the versioned config, not from what
  a reviewer hopes the answer will be.
