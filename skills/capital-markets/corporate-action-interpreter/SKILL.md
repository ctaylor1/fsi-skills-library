---
name: corporate-action-interpreter
description: >-
  Interpret an authoritative corporate-action notice — event type, key dates, elective
  options, and the resulting cash/share entitlements on an eligible position — into a
  clear, source-linked, plain-language explanation, and flag ambiguous or missing terms
  for operations review. Use when a retail investor or corporate-actions analyst asks
  "what does this corporate action mean", "what are my options and the deadline", "how
  many shares or how much cash will I receive", or attaches a DTC/agent/issuer notice for
  a split, cash or stock dividend, dividend option, merger, tender, exchange, rights, or
  spin-off. This skill is informational and analytical only: it never recommends which
  option to elect, gives investment or personalized tax advice, or submits/records an
  election or instruction — route those to the election-processing, tax-basis, and
  advice-boundary skills.
license: MIT
compatibility: Amazon Quick Desktop; requires post-trade/clearing (depository/agent notices), market/reference-data, portfolio-accounting/custody (eligible position), and document-intelligence MCP integrations (all read-only).
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
  aws-fsi-primary-user: "Retail investor / corporate-actions analyst"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Corporate Action Interpreter

## Purpose and outcome
Turn an authoritative corporate-action notice into a faithful, plain-language explanation
so the reader understands **what the event is, what (if anything) they must do, by when,
and what they would receive**. A successful output states the event type and status
(mandatory / voluntary / mandatory-with-options), the key dates, each elective option and
its terms, and the deterministic cash/share entitlement on the stated eligible position —
every figure and date traceable to a cited notice line — plus an explicit list of
ambiguous or missing terms flagged for operations review. It **never** recommends an
option, opines on tax, or submits an election.

## Use when
- "What does this corporate action mean", "explain this notice", "walk me through this
  event".
- "What are my options and the election deadline", "is this mandatory or do I have to
  respond", "what happens if I do nothing".
- "How many shares / how much cash will I receive on N shares" for a split, cash or stock
  dividend, dividend option, merger consideration, tender/exchange offer, rights, or
  spin-off.
- The user attaches a depository (DTC/DTCC), transfer/paying-agent, or issuer notice and
  wants a readable interpretation (external delivery requires human review — see Human
  approval).

## Do not use
- The user wants you to **place, submit, or confirm an election, tender, or subscription**
  → out of scope; route to `corporate-action-election-assistant` (R4). This skill never
  instructs the custodian.
- The user wants **which option is better / whether to participate** (investment advice) →
  out of scope; there is no advice skill — a licensed representative must handle it.
- The user wants a **personalized tax result, cost-basis restatement, or wash-sale/lot
  treatment** → out of scope; there is no catalog tax skill — refer the holder to a
  licensed tax professional.
- The user wants to **reconcile received entitlements vs. announced** after pay date →
  out of scope; hand the expected entitlements to the corporate-actions operations team
  for post-event reconciliation.
- The user needs the **eligible position itself** normalized from a statement/custody file
  → route to `portfolio-holdings-summarizer` (upstream) and pass the position back here.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). In short: this skill consumes an
eligible-position snapshot (often from `portfolio-holdings-summarizer`) and an official
notice, and emits a normalized **interpretation** tagged with a durable
`interpretation_id`. It hands off to `corporate-action-election-assistant` (to actually
elect), a licensed tax professional (tax basis), and the corporate-actions operations team
(post-event reconciliation); flagged ambiguities go to the corporate-actions operations
exception queue. It performs none of that downstream work itself.

## Inputs and prerequisites
- An **authoritative notice** for **one event at a time**: `event_id`, `event_type`
  (CAEV-style code), `mandatory_voluntary`, security identity, the key dates, terms
  (ratio and/or per-share rate), and — for voluntary / mandatory-with-options — the
  `options[]` with the election deadline. See the schema in
  [scripts/validate_input.py](scripts/validate_input.py) and the taxonomy in
  [references/domain-rules.md](references/domain-rules.md).
- The **eligible position** (quantity + as-of) to compute entitlements. Entitlement is on
  the **record-date** holding; a differing as-of is flagged, not silently used.
- Read permission to the depository/agent notice source, reference/market data for
  scrub/confirmation, and custody for the eligible position.

## Source hierarchy
Rank sources and cite every date, term, and figure. See
[references/source-map.md](references/source-map.md).
1. Depository / transfer-or-paying-agent **official notice** (highest) — terms, dates,
   options.
2. Issuer **offering document / official announcement** (prospectus, offer to purchase,
   8-K) — governing terms.
3. **Reference/market data** vendor scrub — confirmation only.
4. Custody **books-and-records** — the eligible position and as-of.
5. User-provided screenshot/summary — unverified; lowest.
Never let a user assertion override the official notice; if sources conflict, present both
with citations and stop for operations review.

## Workflow
1. **Identify scope** — confirm a single `event_id` and security. If the file bundles
   multiple events or securities, ask which one (do not merge).
2. **Validate the notice** — run
   [scripts/validate_input.py](scripts/validate_input.py): structural completeness,
   date ordering, and — for voluntary/options events — a present election deadline,
   non-empty options, and a single default. Data-quality gaps (missing ex-date, fractional
   exposure, position/record mismatch, unknown code) surface as warnings to carry forward.
3. **Compute entitlements (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py) to derive the
   cash/share outcome for the mandatory result or for **each** option from the stated
   terms and eligible quantity. Whole vs. fractional shares are reported separately; a
   cash-in-lieu rate is never invented.
4. **Interpret in plain language** — state event type and status, key dates, each option
   and its terms, the entitlement per option, and — for options events — what happens on
   the default if the holder does nothing. Describe tax *category* neutrally
   (e.g., "may be treated as a return of capital") without a personalized tax result.
5. **Flag ambiguity** — list missing/contradictory terms, superseded notices, unknown
   codes, and unstated fractional handling as `ambiguities[]` for operations review rather
   than guessing.
6. **Validate the output** — run [scripts/validate_output.py](scripts/validate_output.py)
   for entitlement tie-outs, citation coverage, the no-advice/no-tax-advice/no-binding
   screen, and disclaimer presence.

## Validation loop
Run `validate_input` before interpreting and `validate_output` after. If an entitlement
does not tie to its stated terms, a figure or date lacks a citation, the text contains
advice / recommendation-on-election / personalized-tax / binding-instruction language, or
the disclaimer is missing, **fix or fail closed** — do not deliver an untied or
advice-tainted interpretation.

## Human approval
None required for the user's own informational read. **Human review is required before the
interpretation is delivered externally** (e.g., an analyst sending it to a client) or
written to a system of record — `aws-fsi-human-approval: external-delivery`. Any actual
election, tender, or instruction is out of scope here and gated in the R4
election-processing skill.

## Failure handling
- **Missing/contradictory terms or dates** → interpret what is stated, list the rest as
  `ambiguities` for ops review; never invent a rate, ratio, or fractional-share treatment.
- **Unknown event code** → interpret narratively from the notice text, flag the code as
  unconfirmed, and do not assert a formula that may not apply.
- **Multiple events/securities in one file** → stop and ask; do not merge.
- **Superseded/updated notice** → use the latest official version; flag that an earlier
  version was replaced.
- **Election deadline already passed / position as-of ≠ record date** → surface explicitly;
  do not assume the entitled position.
- **Source conflict** → present both figures with citations; do not pick a winner.
- **Tool timeout / permission denial** → report partial results and the exact gap; assume
  no retry.

## Output contract
1. **Header** — security (masked account where shown), `event_id`, event type + name,
   mandatory/voluntary status.
2. **Key dates** — announcement, ex, record, election deadline (if any), pay/effective.
3. **Action required** — for options events, the deadline and the default outcome if the
   holder does nothing; for mandatory events, "no action required".
4. **Options & entitlements** — each option's terms and the deterministic cash/share
   entitlement on the eligible position, with whole/fractional split and a citation each.
5. **Ambiguities** — missing/contradictory terms flagged for operations review.
6. **Machine-readable** — the normalized interpretation tagged with a durable
   `interpretation_id` for downstream skills.
7. **Standing disclaimer** — "Informational interpretation only; not investment or tax
   advice, and not an election or instruction; verify against the official notice and
   confirm any election through your custodian or operations team."
Every date, term, and figure carries a source citation. See
[references/controls.md](references/controls.md).

## Privacy and records
Customer NPI/PII (the eligible position and account). Mask account numbers (show last 4).
Keep notices and positions within the approved environment; never exfiltrate. Retain the
interpretation and its citations per records policy; log the source read, interpretation
creation, and any external-delivery approval (who/when). See
[references/controls.md](references/controls.md).

## Gotchas
- **Entitlement is on the record-date holding**, not today's — a differing position as-of
  is flagged, not silently used.
- **Fractional shares**: report whole shares and the fractional remainder separately; the
  cash-in-lieu rate comes from the notice — if absent, flag it, do not compute it.
- **Bond/rate quoting**: per-share rates apply to shares; do not confuse a per-share cash
  rate with a percentage of par.
- **Mandatory-with-options has a default** — always state what happens if the holder does
  nothing; that is not a recommendation.
- **"Interpret" is not "advise"**: computing that the cash option pays $120 and the stock
  option delivers 12.5 shares is in scope; saying which to pick, or that it is
  "tax-free to you", is advice and out of scope.
- **Voluntary ≠ elective outcome by us**: the skill never records or submits an election;
  it only explains the choices and the deadline.
