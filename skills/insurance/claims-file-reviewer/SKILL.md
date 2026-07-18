---
name: claims-file-reviewer
description: >-
  Review a claim file for policy/coverage citation, chronology, missing documentation,
  severity, reserve support, decision traceability, and open issues; produce a source-linked
  findings pack with cited evidence and a deterministic review-readiness band. Use when a
  claims adjuster, claims manager, or coverage specialist asks to "review this claim file",
  "what documentation is missing", "build the claim chronology", "is the reserve supported",
  "is this payment/decision traceable", or needs review-ready evidence before adjudication.
  HARD BOUNDARY: this skill produces findings and cited evidence for a human adjudicator
  only — it NEVER makes a coverage or reserve determination, approves/denies a claim, sets or
  changes a reserve, issues a payment, settles, closes a case, or files anything; those are
  human, authorized actions.
license: MIT
compatibility: Amazon Quick Desktop; requires claims-system, policy/endorsement, document-intelligence, payments/reserves-ledger, and approved-calculation MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Insurance"
  aws-fsi-skill-type: "Analysis and evaluation skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Analyze & review"
  aws-fsi-agent-pattern: "Case agent + evidence bundle"
  aws-fsi-delivery-wave: "Wave 3 - regulated casework"
  aws-fsi-action-mode: "Read-only analysis"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Highly Confidential (customer NPI/PII)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Insurance underwriting & claims"
  aws-fsi-primary-user: "Claims adjuster / claims manager / coverage specialist"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Claims File Reviewer

## Purpose and outcome
Given a claim file — policy and endorsements, correspondence, medical/repair/adjuster
evidence, payments, reserves, decisions, and legal/recovery data — build a **chronology** and
run a fixed set of **documented review checks** (coverage citation, policy-period fit, missing
documentation, reserve support/severity consistency, decision & payment traceability, stale
open issues). Attach cited evidence to every finding and map the finding set to a
**review-readiness band**. A successful output lets a licensed adjuster or claims manager see,
at a glance, what is complete, what is missing, and what to escalate — while the coverage and
reserve **decisions remain human**.

## Use when
- "Review this claim file / is it ready to adjudicate?"
- "What required documentation is missing on this claim?"
- "Build a chronology of this claim and flag anything inconsistent."
- "Is the reserve supported by the evidence? Are the payments and decisions traceable?"
- A reviewer needs a consistent, cited write-up to attach to a claim before adjudication.

## Do not use
- The user wants a **coverage or reserve determination**, a claim **approved/denied**, a
  **reserve set/changed**, a **payment/settlement**, a **case closed**, or a **filing** →
  out of scope. Produce findings + evidence and route the decision to the human adjuster.
- **Fraud referral** (indicators found, referral to draft) → `claims-fraud-referral-assistant`.
- **Reserve development / actuarial analysis** → `reserving-analysis-assistant`.
- **Subrogation / recovery screening** → `subrogation-opportunity-screener`.
- **First-line severity classification / routing** of a fresh FNOL → `claims-triage-assistant`.
- **Coverage-gap (needs vs terms)** analysis, form/wording comparison, or plain-language
  policy explanation → `coverage-gap-analyzer`, `policy-wording-comparator`,
  `policy-document-explainer`.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill emits a review pack with a
durable `review_id`; downstream fraud/reserving/recovery skills consume it. It must not
duplicate their drafting or any adjudication.

## Inputs and prerequisites
- **Claim identifier** and the claim file: policy `{effective_date, expiration_date,
  coverages[{code, limit, deductible, citation}], endorsements}`, `documents[]`, `events[]`
  (chronology), `reserves[]`, `payments[]`, `decisions[]`, `loss_date`, `report_date`.
  Schema: [scripts/validate_input.py](scripts/validate_input.py).
- Read access to the claims system, policy/endorsement forms, and the versioned **review
  config** (required-document sets, thresholds, tolerances — see
  [references/domain-rules.md](references/domain-rules.md)).

## Source hierarchy
See [references/source-map.md](references/source-map.md). The claims system is the position of
record; policy forms govern coverage; evidence supports severity/reserves; config supplies
required-doc sets and thresholds. Cite every finding to a record, clause, or config rule. On
conflict (note vs form), cite both and raise a finding — never resolve it as a coverage call.

## Workflow
1. **Scope & load** — confirm the claim and `as_of`; load the file for the policy period;
   validate with `validate_input`.
2. **Build chronology** — order dated events; check report-vs-loss ordering and event gaps.
3. **Run checks (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py) to evaluate coverage
   citation, policy-period fit, missing documentation, reserve support/severity consistency,
   payment/decision traceability, and stale open issues. Each fired check returns its evidence
   and citation. Checks are **explainable**, not a black-box score.
4. **Map readiness** — map the finding set to `documentation_complete` / `follow_up_required`
   / `escalate` per the deterministic mapping. This is a triage suggestion for a human,
   explicitly **not** a coverage or reserve determination.
5. **Write the pack** — chronology + per-finding evidence + readiness + reviewer
   considerations + recommended handoffs, with the standing disclaimer.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py)
after. The output screen confirms: every finding has cited evidence, no
determination/action/filing language is present, readiness maps deterministically from the
findings, the disclaimer is present, and reviewer considerations are included. Fail closed on
any miss.

## Human approval
`required`: a licensed adjuster / claims manager / coverage specialist must adjudicate before
any coverage or reserve decision, payment, closure, or filing, and before the review is
written into the claims system of record. No approval is needed for the reviewer's own read.
The skill never takes a claim action.

## Failure handling
- **Missing coverage citation / thin file** → raise a `blocking`/`warning` finding; do not
  infer coverage or a conclusion from an incomplete file.
- **Ambiguous claim/policy identity** → stop and confirm; never review the wrong file.
- **Loss outside policy period** → raise a `blocking` finding (threshold question for the
  adjuster); do not decide whether coverage was in force.
- **Stale/conflicting sources** (note vs form) → cite both; do not resolve silently.
- **Tool timeout** → return the checks completed so far with a clear "incomplete" flag.

## Output contract
1. **Summary** — claim (masked), `as_of`, claim type, incurred (`reserves+paid`), severity
   band, review-readiness band.
2. **Chronology** — dated, cited events in order.
3. **Findings** — per finding: id, category, severity, plain-language summary, cited evidence.
4. **Open issues** — outstanding tasks with age.
5. **Reviewer considerations** — coverage/reserve/jurisdiction cautions the human must weigh.
6. **Machine-readable** — findings + evidence + `review_id` + `config_version` for downstream
   skills and reproducibility.
7. **Standing disclaimer** — "Review findings and evidence only; not a coverage or reserve
   determination. No claim decision, payment, reserve change, or case closure has been made."
See [references/controls.md](references/controls.md).

## Privacy and records
Customer NPI/PII (claimant medical, repair, personal data). Minimize to what evidences a
finding; mask identifiers where surfaced. Retain the review + citations + `config_version`
per records policy; log the read and any approval to write the review into a case. Never
exfiltrate claimant data.

## Gotchas
- **A finding is not a decision.** Blocking findings justify *escalation and human review*,
  never a coverage/reserve conclusion or a claim action.
- **Missing ≠ non-existent.** A required document absent from the file may exist elsewhere;
  the pack flags a gap to confirm, not a coverage defect.
- **Reserve support is a consistency check, not adequacy.** The skill flags an unsupported or
  divergent indemnity reserve; it never opines on the "right" reserve — that is actuarial.
- **Expense (ALAE) reserves** are not tied to a damage estimate; only indemnity reserves are
  checked for supporting evidence.
- **Coverage language is sensitive.** Describe citation/period gaps factually; do not write
  "coverage applies/denied" — that is a determination reserved to the human.
- **Do not tune config to the claim.** Required-doc sets and thresholds come from the
  versioned config, not from what "should" apply to reach a readiness band.
