---
name: communications-compliance-reviewer
description: >-
  Review a public or internal communication (email, social post, website, ad, letter,
  research, chat, memo) against communications-compliance rules: classify it (retail
  communication, correspondence, institutional, internal), then flag prohibited or promissory
  claims, performance predictions, one-sided/unbalanced content, missing required disclosures
  (member name, past-performance, BrokerCheck, testimonial), supervision gaps (principal
  pre-approval/review), retention and off-channel gaps, and escalation needs (MNPI/market
  abuse, complaints) — each with cited evidence and a recommended disposition. Use when a
  rep, supervisor, or compliance analyst asks to review a communication, whether it needs
  principal approval, whether a disclosure is adequate, or to flag compliance issues before
  sending. HARD BOUNDARY: findings and evidence only for registered-principal adjudication;
  NEVER approves or clears a communication, grants principal approval, files it, closes the
  review, or asserts a confirmed violation.
license: MIT
compatibility: Amazon Quick Desktop; requires communications-archive, supervision/approval, controlled-content-library (WSPs/disclosures), reference-data, and versioned-config MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Capital Markets"
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
  aws-fsi-owner: "Capital Markets operations & compliance"
  aws-fsi-primary-user: "Registered principal / communications compliance analyst"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Communications Compliance Reviewer

## Purpose and outcome
Given a single communication and its supervision/retention metadata, **classify** it under the
communications rulebook, run deterministic **content, disclosure, supervision, retention, and
escalation** checks, attach **cited evidence** to every finding, and produce a review pack with
a **recommended disposition** (Escalate / Remediate / Advisory / No-exceptions). A successful
output lets a registered principal see exactly what fired, why, and what to remediate — the
decision to approve, file, escalate, or close the review remains a human, principal-adjudicated
action.

## Use when
- "Review this email / social post / advertisement for compliance before we send it."
- "Does this retail communication need principal pre-approval?"
- "Are the required disclosures (past performance, BrokerCheck, testimonial) present?"
- "Is this business message captured for retention, or is it off-channel?"
- A supervisor needs a consistent, cited communications write-up to attach to a review.

## Do not use
- The user wants the communication **approved / cleared / filed**, or the **review closed** →
  out of scope. Produce findings + evidence and route to the **registered principal** who
  adjudicates in the supervision system of record.
- The communication is a **voice/phone interaction** → `call-quality-compliance-reviewer`.
- The material indicates **MNPI misuse or market abuse** → `surveillance-alert-triager` (then
  `market-surveillance-alert-investigator`).
- The material contains a **customer complaint** → `complaint-resolution-assistant`.
- A drafting task ("write the disclosure for me") — this skill reviews; drafting skills such as
  `advisor-follow-up-assistant` or `fund-commentary-drafter` produce content and route it here.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill emits a review pack with a
durable `review_id`; downstream surveillance/complaint/conflicts/exam skills consume it. It
must not duplicate their investigation, or the principal's approval/filing/closure.

## Inputs and prerequisites
- **The communication**: `comm_id`, `channel`, `audience`, `recipient_count` (and window,
  default 30 days), `subject`, `body`. Schema:
  [scripts/validate_input.py](scripts/validate_input.py).
- **Disclosures present**: the controlled disclosure tags attached to the communication
  (`firm_name`, `past_performance`, `brokercheck`, `testimonial_disclosure`, `risk_disclosure`).
- **Supervision**: principal pre-approval, reviewer, approval/first-use dates.
- **Retention**: archived status, archive system, whether the channel is approved.
- Read access to the communications archive, supervision system, controlled-content library
  (WSPs/disclosure register), and the versioned rulebook config (see
  [references/domain-rules.md](references/domain-rules.md)).

## Source hierarchy
See [references/source-map.md](references/source-map.md). The communications archive is the
record of what was said and to whom; the supervision system holds approval/review status; the
controlled-content library holds required disclosures and current rule mappings; config holds
thresholds and the disposition mapping. Cite every finding to a source field.

## Workflow
1. **Scope & validate** — confirm the communication and its metadata; run `validate_input`.
2. **Classify (deterministic)** — determine retail communication / correspondence /
   institutional / internal from audience and recipient count within the window.
3. **Run checks (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py) to evaluate prohibited
   claims, performance predictions, fair-and-balanced, required disclosures, supervision,
   retention/off-channel, and escalation. Each fired finding returns severity + evidence rows
   with citations. Findings are **explainable**, not a black-box score.
4. **Map disposition** — map the fired findings' severities to a recommended band per the
   documented mapping. This is a **recommendation for a registered principal**, explicitly not
   an approval, filing, or closure.
5. **Write the pack** — plain-language finding-by-finding explanation + evidence + recommended
   disposition + remediation prompts + escalation routes + the standing disclaimer.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py) after.
The output screen confirms: every finding has evidence + citation, no approval/decision/
closure/filing language is present, the disposition maps deterministically from the findings,
the standing disclaimer is present, and remediation prompts are included when any high/medium
finding fired. **Fail closed** on any miss (see
[evals/files/review_pack_prohibited.json](evals/files/review_pack_prohibited.json)).

## Human approval
`required` (R3): a **registered principal** must independently review and adjudicate before any
regulated decision — approving/clearing the communication, granting principal approval, filing
it, posting it, or closing the review. This skill never performs any of those; it produces the
evidence a principal decides on.

## Failure handling
- **Missing supervision/retention metadata** → fail closed on structure; where a field is
  simply absent, report the gap conservatively (e.g., no approval on record → supervision gap).
- **Unknown recipient count** (retail) → classify conservatively as a **retail communication**
  and state the assumption; do not under-classify to avoid the pre-approval requirement.
- **Ambiguous communication identity** → stop and confirm; never review the wrong record.
- **Stale/conflicting sources** (archive vs. supervision system) → cite both; do not resolve
  silently.
- **Tool timeout** → return the findings computed so far with a clear "incomplete" flag.

## Output contract
1. **Summary** — comm (masked as needed), classification, count of findings, recommended
   disposition band.
2. **Findings** — per fired finding: type, rule (orientation label), severity, plain-language
   reason, cited evidence rows, and remediation.
3. **Escalation routes** — surveillance/complaint/conflicts routing when applicable.
4. **Remediation prompts** — the concrete fixes to weigh before use.
5. **Machine-readable** — findings + evidence + `review_id` for downstream skills.
6. **Standing disclaimer** — "Advisory compliance review only; not a supervisory approval,
   regulated determination, or filing. A registered principal must independently review and
   adjudicate this communication before any use, distribution, regulatory filing, or review
   closure."
See [references/controls.md](references/controls.md).

## Privacy and records
Customer NPI/PII may appear in communication content. Mask account/card numbers (last 4) and
minimize customer data in the output to what evidences a finding. Retain the review +
citations + `config_version` per records policy; log the read and any escalation routing.
Never exfiltrate communication content or customer data.

## Gotchas
- **A finding is not a decision.** Even a clean "No-exceptions" result is **not** approval —
  principal review is still mandatory before use.
- **Keyword scans over-fire by design.** Prohibited-claim and prediction matches are
  conservative; a hit is a finding to review, not a confirmed violation. Clearing false
  positives is the principal's call.
- **Classification drives the requirements.** More than 25 retail recipients (default) makes it
  a retail communication requiring pre-approval; an unknown count defaults conservatively to
  retail — never round down to dodge the requirement.
- **Off-channel is serious.** A business communication on an unapproved medium is a high-
  severity recordkeeping finding, not a style note.
- **Rule labels are orientation.** FINRA/SEC citations are guides; the firm's WSPs, current
  rule text, and any jurisdiction pack govern. Do not treat a rule label as legal advice.
- **Never tune to the author.** Thresholds and the claim library come from the versioned config,
  not from what "should" be acceptable for a particular rep or campaign.
