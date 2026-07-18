---
name: prospectus-plain-language-breakdown
description: >-
  Explain a prospectus (or summary prospectus / offering document) in plain language —
  fees and expenses, investment strategy, liquidity and redemption terms, conflicts of
  interest, principal risks, and investor obligations — with a page-level citation behind
  every statement. Use when a retail investor or a sales/compliance associate asks "what
  does this prospectus say", "break down the fees on this fund", "explain the risks in
  plain English", "what are the redemption/lock-up terms", or attaches a prospectus, summary
  prospectus, KIID, or offering memorandum and wants a readable, source-linked breakdown.
  This skill is informational only: it does not give investment advice, recommend or solicit
  buying/subscribing, judge suitability, opine on whether the offering is "good", or make an
  offer — route those to the appropriate advice-boundary or suitability skill.
license: MIT
compatibility: Amazon Quick Desktop; requires document-intelligence (page/section citation), approved-source retrieval (filed prospectus/SAI), and entity-resolution (issuer/security) MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Capital Markets"
  aws-fsi-skill-type: "Guidance or domain-expertise skills"
  aws-fsi-risk-tier: "R2"
  aws-fsi-archetype: "Explain & summarize"
  aws-fsi-agent-pattern: "Interactive decision-support copilot"
  aws-fsi-delivery-wave: "Wave 1 - stabilize existing"
  aws-fsi-action-mode: "Read-only analysis"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "existing-updated"
  aws-fsi-human-approval: "external-delivery"
  aws-fsi-data-classification: "Highly Confidential (customer NPI/PII)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Capital Markets operations & compliance"
  aws-fsi-primary-user: "Retail investor / sales or compliance associate"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Prospectus Plain-Language Breakdown

## Purpose and outcome
Turn a filed prospectus (or summary prospectus, KIID, or offering memorandum) into a
faithful, plain-language breakdown so a reader can understand what they are being offered:
what it costs, how it invests, how and when they can get their money out, who benefits and
how, what can go wrong, and what the investor is agreeing to. A successful output covers
each required disclosure topic — **fees, strategy, liquidity, conflicts, risks, investor
obligations** — in plain English, with a **page-level citation behind every statement**,
flags any topic the document does not disclose as a gap, and contains **no recommendation,
solicitation, suitability judgment, or offer**.

## Use when
- "Explain this prospectus / summary prospectus / offering memorandum in plain English."
- "Break down the fees and expenses on this fund"; "what's the expense ratio / sales load /
  12b-1 fee / redemption fee".
- "What are the redemption terms / lock-up / gates / notice period / liquidity."
- "Summarize the principal risks", "what are the conflicts of interest", "what am I
  agreeing to / what are my obligations as an investor".
- A retail investor or a sales/compliance associate attaches a prospectus and wants a
  readable, source-linked breakdown (external delivery to a client requires review — see
  Human approval).

## Do not use
- The user wants **advice, a recommendation, or a solicitation** — "should I invest",
  "is this a good fund", "will it go up", "buy or not" → out of scope; do not answer with a
  view. Offer the informational breakdown instead.
- The user asks whether the offering is **suitable** for them or their client, or asks for a
  Reg BI / best-interest judgment → route to `suitability-reg-bi-reviewer`.
- The user wants a **personalized risk/diversification opinion** on their portfolio →
  `portfolio-risk-diversification-check` (educational, non-advice).
- The user wants a **fee reasonableness / benchmarking** conclusion (not just what the fees
  are) → `fee-and-charge-reviewer`.
- The user wants to **draft marketing or a fact sheet** from the prospectus →
  `fund-fact-sheet-builder` / `fund-commentary-drafter` (draft-and-package, approval-gated).
- The document is a **trade confirmation** or a **corporate-action notice**, not a
  prospectus → `trade-confirmation-explainer` / `corporate-action-interpreter`.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). In short: this skill produces a
plain-language, page-cited **breakdown** and stops. It hands off the breakdown (and its
durable `breakdown_id`) to suitability, fee-reasonableness, marketing-drafting, and
portfolio-analysis skills; it never performs suitability, benchmarking, drafting, or advice
itself.

## Inputs and prerequisites
- A **parsed prospectus source** for **one document at a time**: document id/type, issuer,
  instrument, effective/filing date, jurisdiction, total pages, and the extracted sections
  with headings, page ranges, and text. See the input schema in
  [scripts/validate_input.py](scripts/validate_input.py).
- Every section must carry a **page anchor** (`page_start`/`page_end`) so each plain-language
  statement can be cited to a page. A section without a page anchor is rejected.
- The **effective/filing date** of the document (prospectuses are updated periodically;
  an out-of-date document is labeled, not silently trusted).
- Read access to the filed document via document-intelligence; approved-source retrieval for
  the statutory prospectus / Statement of Additional Information (SAI) when the summary
  prospectus incorporates them by reference.

## Source hierarchy
Rank sources and cite every statement to a page. See
[references/source-map.md](references/source-map.md).
1. The **filed statutory prospectus / offering document** (and SAI where incorporated) —
   the authoritative text (highest).
2. The **summary prospectus / KIID** for the same security and effective date — for the
   headline breakdown, with cross-references to the statutory document.
3. **Reference/entity data** for issuer/security identity only.
Never substitute marketing material, a fact sheet, or a user assertion for the filed
document. If the summary and statutory documents conflict, cite both and treat the statutory
document as controlling. Apply the domain rules in
[references/domain-rules.md](references/domain-rules.md).

## Workflow
1. **Identify scope** — confirm the single document, its type, issuer/instrument, and
   effective date. If multiple documents or share classes are present, ask which one (do
   not merge share classes or documents).
2. **Map coverage** — locate each required topic (fees, strategy, liquidity, conflicts,
   risks, obligations) in the source and attach its page range. Any required topic the
   document does not disclose is recorded as a **gap**, not invented.
3. **Translate (faithful, deterministic in spirit)** — write each topic in plain language
   that preserves the document's meaning: normalize fees to the document's own figures with
   their page cite, state redemption/liquidity terms exactly (frequency, notice, lock-ups,
   gates), name conflicts as disclosed, and list principal risks without softening or
   editorializing. Attach a page citation to every statement.
4. **Validate** — run [scripts/validate_output.py](scripts/validate_output.py) to confirm
   every required topic is covered or flagged, every statement carries a citation, no
   advice/solicitation language is present, and the standing disclaimer is present.
5. **Surface gaps** — undisclosed topics, "incorporated by reference" cross-references you
   could not retrieve, and any figure the document does not state are listed explicitly
   rather than guessed.

## Validation loop
Run `validate_input` before translating and `validate_output` after. If a required topic is
neither covered nor flagged, a statement lacks a page citation, the output contains
advice/solicitation language, or the disclaimer is missing, **fix or fail closed** — do not
deliver an incomplete, uncited, or advice-tainted breakdown.

## Human approval
None required for the user's own informational read. **Human review is required before the
breakdown is delivered externally** (e.g., an associate sending it to a client or attaching
it to a client-facing packet) or written to a system of record —
`aws-fsi-human-approval: external-delivery`. This skill makes no binding decision.

## Failure handling
- **Missing/undisclosed required topic** → cover what the document discloses, list the
  missing topic as a disclosure gap; never fabricate the disclosure.
- **Incorporated by reference** (summary prospectus points to SAI/statutory) and the target
  is unavailable → state the cross-reference and that full detail is in the referenced
  document; do not paraphrase text you have not read.
- **Multiple documents / share classes** → stop and ask which one; do not merge.
- **Source conflict** (summary vs. statutory) → present both with page cites; statutory
  controls.
- **Missing page anchor / unparseable section** → reject at input; a statement with no page
  to cite is not delivered.
- **Tool timeout / permission denial** → report partial coverage and the exact gap; no retry
  assumption.

## Output contract
1. **Header** — issuer, instrument, document type, effective date, jurisdiction, and the
   source `document_id`.
2. **Breakdown** — one plain-language section per required topic (fees, strategy, liquidity,
   conflicts, risks, obligations), each with a **page citation**; optional topics (tax,
   distributions, management/adviser, performance) where present.
3. **Coverage & gaps** — a coverage map of required topics (covered / gap) and an explicit
   **Data gaps** list.
4. **Machine-readable** — the structured breakdown tagged with a durable `breakdown_id` for
   downstream skills.
5. **Standing disclaimer** — "Plain-language summary only; not investment advice, a
   recommendation, a solicitation, or an offer. Read the full prospectus before investing."
Every statement carries a page citation. See [references/controls.md](references/controls.md).

## Privacy and records
Customer NPI/PII may appear where a breakdown is prepared for a specific client. Mask any
account/holder identifiers (show last 4). Keep the document and breakdown within the approved
environment; never exfiltrate the filed document or client context. Retain the breakdown and
its citations per records policy; log the source read and any external-delivery approval
(who/when). See [references/controls.md](references/controls.md).

## Gotchas
- **"Explain" is not "advise"**: describing a 5.75% front-end load or a 2-year lock-up is in
  scope; calling the fund "expensive", "a good deal", "low-risk", or "worth it" is advice and
  is out of scope.
- **Every statement needs a page**: a plain-language sentence with no page anchor is a gap to
  fix, not a summary to ship.
- **Do not soften risk language**: translate principal risks faithfully; do not downgrade
  "you may lose your entire investment" to "some risk".
- **Summary vs. statutory**: a summary prospectus incorporates the statutory prospectus and
  SAI by reference — flag what is incorporated rather than implying the summary is complete.
- **Share classes differ**: fees, loads, and 12b-1 charges vary by share class; never blend
  classes or quote one class's fee for another.
- **Fees are multi-line**: sales load, expense ratio, management fee, 12b-1, redemption fee,
  and account fees are distinct — report each as the document states it, not a single blended
  number, unless the document itself states a total.
- **Past performance / forward statements**: report them as the document frames them; never
  restate them as an expectation or a projection of your own.
