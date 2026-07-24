---
name: credit-terms-covenant-extractor
description: >-
  Extract structured credit terms — maturity, coupon, seniority, collateral, call provisions,
  covenants, and baskets — with page-level citations from a single controlled credit document
  (indenture, credit agreement, offering memorandum, prospectus, term sheet). Use when a credit
  analyst asks to pull, extract, or tabulate the terms of a bond or loan and cite the source
  pages, or to hand a clean, cited term set to a memo, surveillance, or covenant-testing
  workflow. Normalizes deterministically and flags ambiguous, conflicting, or defined-term
  language as needs_review rather than guessing. HARD BOUNDARY: never interprets ambiguous
  language, never determines covenant compliance or computes a covenant test, never gives an
  investment view, and never monitors an issuer over time. Route covenant testing to
  covenant-compliance-monitor and ongoing monitoring to credit-surveillance-packet. Every term
  carries a page-level citation or it is not extracted.
license: MIT
compatibility: Amazon Quick Desktop; requires document-intelligence, entity-resolution, and controlled-content-library MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Asset Management"
  aws-fsi-skill-type: "Utility skills"
  aws-fsi-risk-tier: "R2"
  aws-fsi-archetype: "Analyze & review"
  aws-fsi-agent-pattern: "Interactive decision-support copilot"
  aws-fsi-delivery-wave: "Wave 5 - 2026 industry expansion"
  aws-fsi-action-mode: "Read-only analysis"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "external-delivery"
  aws-fsi-data-classification: "Highly Confidential (MNPI / client-confidential)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Asset Management investment & product"
  aws-fsi-primary-user: "Credit analyst"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Credit Terms & Covenant Extractor

## Purpose and outcome
Given one controlled credit document, extract its key terms — **maturity, coupon, seniority,
collateral, call provisions, covenants, and baskets** — normalize each into a canonical shape,
and attach a **page-level citation** to every field. A successful output is a clean, cited,
machine-readable term set that a credit analyst can trust and that downstream memo, surveillance,
and covenant-testing workflows can consume without re-parsing the document. The extractor states
facts and their locations; it forms **no view** and makes **no determination**.

## Use when
- "Extract the maturity, coupon, seniority, and covenants from this indenture and cite the pages."
- "Pull the call schedule and the negative-covenant baskets out of this offering memorandum."
- "Tabulate the terms of this bond/loan into a structured, source-linked record."
- A memo, surveillance packet, or covenant monitor needs a consistent, cited term set to start from.

## Do not use
- The user wants **covenant compliance determined** or a **covenant test computed** ("is it in
  compliance?", "what's the headroom?", "calculate the leverage test") → out of scope. Extract the
  covenant mechanic and threshold as raw text and route the test to `covenant-compliance-monitor`.
- The user wants **ongoing issuer monitoring / a review packet** (leverage, coverage, liquidity,
  maturity wall, spreads, ratings, covenant changes over time) → `credit-surveillance-packet`.
- The user wants an **investment view** (buy/sell/hold, over/underweight, rating) → prohibited;
  this skill never advises.
- The terms feed a commercial **credit memorandum** for approval → `credit-memo-drafter`; or
  **portfolio-level** analysis → `credit-risk-portfolio-analyzer`.
- The document is a **draft/redline/marketing deck** with unfixed terms → record `doc_version` and
  flag fields `needs_review`; do not present draft language as final terms.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill emits a cited extraction with a
durable `extraction_id`; downstream covenant-testing, surveillance, memo, and portfolio skills
consume it and must not re-parse the document. It never performs their determination, monitoring,
or drafting steps.

## Inputs and prerequisites
- A **single controlled credit document** identified by `doc_id`, `doc_type`, `issuer`,
  `effective_date`, and `doc_version` (execution/filed preferred).
- A document-intelligence **candidate set**: for each term, a `field` (one of the seven canonical
  fields), a verbatim `raw_value`, a **`page`** (mandatory), and a `locator` (section/clause).
  Schema: [scripts/validate_input.py](scripts/validate_input.py).
- `expected_fields[]` — the fields the analyst wants covered (drives `not_found` reporting).
- Read access to document-intelligence, entity resolution, and the versioned normalization rules
  (see [references/domain-rules.md](references/domain-rules.md)).

## Source hierarchy
See [references/source-map.md](references/source-map.md). The document text is the position of
record; document-intelligence supplies locators; entity resolution binds the extraction to the
right issuer/instrument. **Every** extracted term cites its page; a term with no page-level
citation is not extracted.

## Workflow
1. **Scope & resolve** — confirm the document (`doc_id`, `doc_version`, `effective_date`) and the
   issuer/instrument; confirm `expected_fields`. Validate with `validate_input` (fails closed on a
   candidate missing its `page`).
2. **Normalize (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py) to map each candidate to
   its canonical shape (dates→ISO, coupon→rate/type/frequency, seniority→ranked ladder, covenant→
   incurrence/maintenance + captured threshold, basket→type + stated cap), carrying the page/locator
   citation onto every field.
3. **Flag, don't resolve** — any candidate with ambiguity markers (`subject to`, `as defined`, `to
   be determined`, defined-term cross-references) or conflicting single-value candidates is set to
   `needs_review` with a reason. The skill emits **no** definitive value for these.
4. **Report coverage** — expected fields with no candidate are `not_found`; everything else is
   `extracted` or `needs_review`, each with its citation.
5. **Package** — a plain-language summary + the machine-readable extraction + the standing
   disclaimer. Ambiguity and gaps are stated explicitly for the analyst to read.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py) after. The
output check confirms: every extracted/needs_review field has a page-level citation; no
compliance-determination or investment-advice language is present in generated prose; no field with
ambiguity markers was silently resolved; the standing disclaimer and durable `extraction_id` are
present. Fail closed on any miss.

## Human approval
`external-delivery`: human review required before the extraction package is delivered outside the
requester or written to a system of record (e.g., the research platform). No approval needed for the
requester's own read. The skill never writes or acts.

## Failure handling
- **Candidate missing a page** → `validate_input` errors; the term is not extracted (fail closed).
- **Unparseable/off-ladder value** (bad date, non-standard seniority, grower/ratio basket) →
  `needs_review`, never a guessed value.
- **Ambiguous or defined-term language** → `needs_review` with the markers named.
- **Conflicting candidates** for a single-value field → both `needs_review`; never pick a winner.
- **Draft/redline document** → record `doc_version`; flag terms `needs_review` (not fixed).
- **Tool timeout on a long document** → return the fields normalized so far with a clear
  "incomplete" flag; page the rest as a resumable stage.

## Output contract
1. **Summary** — document (id/version/effective date), issuer/instrument, coverage counts.
2. **Fields** — per field: canonical value, status (`extracted`/`needs_review`/`not_found`),
   verbatim `raw_value`, and the page-level `citation`.
3. **Needs review** — each ambiguous/conflicting item with its reason and citation.
4. **Not found** — expected fields with no candidate.
5. **Machine-readable** — the full extraction + durable `extraction_id` for downstream skills.
6. **Standing disclaimer** — "Extracted terms and citations only; no compliance determination,
   covenant test, or investment advice has been made."
See [references/controls.md](references/controls.md).

## Privacy and records
Highly Confidential (MNPI / client-confidential). Treat all document text and outputs as MNPI;
restrict to entitled research users. Minimize output to the cited terms and needs_review reasons; do
not copy large verbatim passages beyond the cited clause. Retain the extraction + citations +
`doc_version` + rule-set version per records policy; log the read and any external-delivery
approval. Never exfiltrate document text.

## Gotchas
- **A term is not a test.** Capturing "Net Leverage not to exceed 4.00x" is extraction; saying the
  issuer is within it is a covenant test — out of scope, route to `covenant-compliance-monitor`.
- **Defined terms hide the real value.** "the greater of $X and Y% of EBITDA", "Available Amount",
  and "as defined" carve-outs must go to `needs_review`; the dollar figure on the page is often not
  the operative cap.
- **Grower baskets.** A basket stated as a fixed dollar amount may actually be a grower; flag when
  the language ties to a ratio/defined term rather than emitting the static number as final.
- **Amendments supersede.** A supplemental indenture or amendment can change maturity, coupon, or
  covenants — extract against the governing amended text and record which `doc_id` governs.
- **Verbatim source is quoted, never editorialized.** `raw_value` may contain phrases like "Event of
  Default"; the skill quotes them but must never add its own determination in the narrative.
