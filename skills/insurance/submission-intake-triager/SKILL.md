---
name: submission-intake-triager
description: >-
  Ingest a commercial-insurance new-business or renewal submission (broker email, ACORD
  forms, PDFs, statement-of-values spreadsheets, loss runs, supporting documents), extract
  and normalize exposure data, reconcile inconsistencies across documents, detect missing
  fields, draft broker follow-up requests, and triage the risk against approved appetite
  rules — producing a cited intake packet with a routing recommendation. Use when an
  underwriter, underwriting assistant, or broker-operations user asks to "triage this
  submission", "check this ACORD against appetite", "what's missing from this submission",
  "normalize and reconcile the exposure data", or "should this go to the underwriter". HARD
  BOUNDARY: this skill recommends and evidences only; it NEVER binds, quotes, prices,
  declines, issues, or closes the risk, and it makes no regulated underwriting decision —
  a licensed human underwriter adjudicates every routing recommendation.
license: MIT
compatibility: Amazon Quick Desktop; requires broker-email, ACORD/PDF document-intelligence (OCR + extraction), policy-administration, producer-data, approved-appetite-rules, and third-party-exposure MCP integrations (all read-only).
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
  aws-fsi-primary-user: "Commercial underwriter / underwriting assistant / broker operations"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Submission Intake Triager

## Purpose and outcome
Given a commercial-insurance submission — a broker cover email plus ACORD forms, PDFs, a
statement of values (SOV), loss runs, and supporting documents — produce a **review-ready
intake packet**: normalized exposure data, cross-document reconciliation, a gap list with
**drafted broker follow-up requests**, appetite findings with cited evidence, and a
**routing recommendation** (In-appetite / Refer / Out-of-appetite / Incomplete). A
successful output lets an underwriter pick up a clean, evidenced submission and decide what
to do next. The **decision — bind, quote, price, decline, or issue — remains human**; this
skill never makes it.

## Use when
- "Triage this submission / check it against our appetite."
- "Extract and normalize the exposure data from these ACORD forms and the SOV."
- "What's missing from this submission and what should I ask the broker for?"
- "Reconcile the TIV / payroll / revenue across the email, application, and spreadsheet."
- "Should this risk route to an underwriter or does it fall outside guidelines?"

## Do not use
- The user wants a **binding decision or action** — bind, quote, price, decline, issue, or
  **close** the submission. Out of scope: recommend + evidence only, then route to the human
  underwriter. See [references/controls.md](references/controls.md).
- Building the full **underwriter-ready risk profile** and drafting **decision rationale** →
  `underwriting-workbench-assistant` (this skill hands off the normalized intake packet).
- **Catastrophe accumulation / portfolio exposure** aggregation for a cat-flagged risk →
  `catastrophe-exposure-monitor`.
- **Coverage adequacy** analysis of stated needs vs. terms/limits/exclusions →
  `coverage-gap-analyzer`.
- **Policy-form / manuscript wording** clause comparison → `policy-wording-comparator`.
- **Quote comparison** across markets (post-quote) → `premium-quote-comparator`.
- **Renewal** term-change review → `policy-renewal-reviewer`.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill emits a cited intake packet
with a durable `triage_id`; downstream skills consume it and must not re-extract or
re-triage. It never performs their underwriting, exposure, or coverage decisions.

## Inputs and prerequisites
- **Submission identifier** and the **line of business** (default schema: commercial
  property).
- **Documents** — each with `doc_id`, `doc_type`
  (`acord` | `sov_spreadsheet` | `loss_run` | `email` | `pdf` | `other`), and a
  `source_ref`. The document-intelligence platform service performs OCR/extraction; this
  skill consumes its **extracted fields**, it does not re-OCR.
- **Extracted fields** — `field`, `value`, `doc_id`, `source_ref` (optional `unit`,
  `confidence`, `doc_type`). Schema: [scripts/validate_input.py](scripts/validate_input.py).
- Read access to policy-administration, producer data, and the **approved appetite config**
  (versioned) — see [references/domain-rules.md](references/domain-rules.md).

## Source hierarchy
See [references/source-map.md](references/source-map.md). Field authority is document-typed:
the **SOV** is authoritative for total insured value, the **loss run** for loss history, and
the **ACORD application** for the remaining application data; the broker email and PDFs are
supporting. Every appetite finding cites the specific source row behind the canonical value.
Where documents disagree, cite **all** sources and surface the mismatch — never resolve it
silently.

## Workflow
1. **Scope & validate** — confirm the submission, line of business, and documents; run
   [scripts/validate_input.py](scripts/validate_input.py). Fail closed on structural errors;
   note data-quality warnings.
2. **Normalize & reconcile (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py). It normalizes
   values to canonical units, selects the canonical value per field by document authority,
   and flags cross-document **mismatches** with every source cited.
3. **Detect gaps & draft follow-ups** — list required fields not present; for each, draft a
   neutral broker follow-up request (draft only — a human sends it). Critical-field gaps
   block triage (band `Incomplete`).
4. **Apply appetite rules (deterministic)** — evaluate the approved rules (state, class,
   TIV capacity, loss ratio, catastrophe exposure) against the canonical values; each rule
   returns `pass` / `refer` / `out` / `not_evaluable` with cited evidence.
5. **Map routing recommendation** — deterministically map the finding set + critical gaps to
   a band (see [references/domain-rules.md](references/domain-rules.md)). This is a **triage
   recommendation for a human underwriter**, explicitly not an underwriting decision.
6. **Write the packet** — normalized fields, reconciliation, gaps + drafted follow-ups,
   appetite findings with evidence, routing recommendation, and the standing disclaimer.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py)
after. The output check confirms: the band matches the deterministic mapping; every
refer/out finding is cited; every reconciliation mismatch carries ≥2 cited sources; gaps
have drafted follow-ups; **no bind/quote/price/decline/issue/closure language** is present;
and the standing disclaimer is present. Fail closed on any miss.

## Human approval
`required` (R3). The routing recommendation is decision **support**; a licensed underwriter
must adjudicate before any bind, quote, price, decline, issuance, posting, or system-of-record
write, and before any follow-up request is sent externally to the broker. The skill takes no
such action itself.

## Failure handling
- **Missing critical field** (state, class, TIV, effective date) → band `Incomplete`; draft
  the follow-up; do not triage appetite as if the data were present.
- **Cross-document conflict** → surface the mismatch with all sources cited; the canonical
  value is the highest-authority source, but the reviewer resolves the discrepancy.
- **Unreadable / low-confidence extraction** → warn and route the field to broker
  verification; do not silently trust a low-confidence value.
- **Ambiguous submission / insured identity** → stop and confirm; never triage the wrong
  submission.
- **Missing appetite config** → use documented defaults and record the `config_version`;
  never invent thresholds.
- **Tool timeout** → return the fields normalized so far with an explicit "incomplete" flag;
  no assumed retry.

## Output contract
1. **Summary** — submission (masked as needed), line of business, received date, routing
   recommendation band, count of fired appetite flags and open gaps.
2. **Reconciliation** — per field: canonical value + source, match/mismatch/single-source,
   and every source value with citation.
3. **Gaps & follow-ups** — each missing field with severity + a drafted broker request.
4. **Appetite findings** — per rule: status, plain-language reason, cited evidence, and the
   config used.
5. **Routing recommendation** — the band + why, framed as a recommendation for the human
   underwriter.
6. **Machine-readable** — the `calculate_or_transform` core + `triage_id` for downstream
   skills.
7. **Standing disclaimer** — "Triage evidence and routing recommendation only; not a bind,
   quote, price, or coverage decision. A licensed underwriter adjudicates …"
See [references/controls.md](references/controls.md).

## Privacy and records
Highly Confidential (customer/insured NPI/PII). Minimize insured data to what evidences a
finding or gap; mask identifiers where display is not required. Retain the packet +
citations + `config_version` per records policy; log the read and any external-delivery
approval for follow-ups. Never exfiltrate submission data to unapproved destinations.

## Gotchas
- **A routing band is not an underwriting decision.** "In-appetite" means *route to an
  underwriter for standard handling*, not "accepted"; "Out-of-appetite" means *recommend
  decline for underwriter adjudication*, not "declined".
- **TIV lives in the SOV, not the ACORD.** When they disagree, the SOV is canonical but the
  mismatch must be surfaced — a stale ACORD TIV is a common intake error.
- **Loss ratio comes from the loss run**, not the broker's summary email; use the
  authoritative document.
- **Do not tune appetite to a broker or insured** — thresholds come only from the versioned
  appetite config.
- **Catastrophe flags mean refer, not decline** — accumulation review is an underwriter/cat
  function; this skill routes, it does not aggregate portfolio exposure.
- **Never draft a quote or premium number** — pricing is outside this skill entirely.
