---
name: trade-confirmation-explainer
description: >-
  Explain a securities trade confirmation in plain language — trade and settlement dates,
  buy/sell side, agent vs. principal capacity, quantity and price, principal, commission or
  markup/markdown, regulatory fees, accrued interest, yield, and the net amount — with every
  figure tied to the confirmation or clearing record. Use when a retail investor or associate
  asks "what does this trade confirmation mean", "explain my confirm", "what did I pay or
  receive", "why is the net different from price times shares", or attaches a Rule 10b-10
  confirmation and wants it decoded. Informational only: it never gives investment advice,
  judges whether the trade, price, or charges were good, fair, or too high, makes a suitability
  or best-execution determination, or finds the confirmation erroneous — route those to the
  appropriate advice-boundary or dispute skill.
license: MIT
compatibility: Amazon Quick Desktop; requires post-trade/clearing, customer-confirmation (document-intelligence), OMS/EMS, and reference/market-data MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Capital Markets"
  aws-fsi-skill-type: "Guidance or domain-expertise skills"
  aws-fsi-risk-tier: "R1"
  aws-fsi-archetype: "Explain & summarize"
  aws-fsi-agent-pattern: "Interactive decision-support copilot"
  aws-fsi-delivery-wave: "Wave 1 - stabilize existing"
  aws-fsi-action-mode: "Read-only analysis"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "existing-no-changes"
  aws-fsi-human-approval: "external-delivery"
  aws-fsi-data-classification: "Highly Confidential (customer NPI/PII)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Capital Markets operations & compliance"
  aws-fsi-primary-user: "Retail investor"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Trade Confirmation Explainer

## Purpose and outcome
Turn one securities trade confirmation into a faithful, plain-language explanation so the
reader understands exactly what the trade was and how the money adds up. A successful output
lets the reader see the trade and settlement dates, whether they bought or sold, whether the
firm acted as agent or principal, the quantity and price, the principal amount, each charge
(commission or markup/markdown and regulatory fees), any accrued interest, and the net amount
— every figure traceable to the confirmation or clearing record — **without** any opinion on
whether the trade, price, or charges were good, fair, or advisable.

## Use when
- "What does this trade confirmation mean", "explain my confirm", "decode this statement".
- "What did I actually pay / receive", "why is the net different from price × shares".
- "What does agent vs. principal mean here", "what is this commission / markup / SEC fee".
- The user attaches a Rule 10b-10 customer confirmation and wants a readable walkthrough.
- An associate needs a clean plain-language explanation to attach to a client reply (delivery
  to a client requires human review — see Human approval).

## Do not use
- The user wants to know whether the trade, price, or timing was **good/bad** or what to do
  next → that is investment advice; out of scope, do not answer it here.
- The user asks whether a **recommendation was suitable** or met **best execution** → route to
  `best-execution-reviewer` (and suitability belongs to the suitability/Reg BI reviewer).
- The user believes the confirmation is **wrong** or disputes a charge → `trade-break-resolver`.
- The user wants to understand the **security/offering** itself →
  `prospectus-plain-language-breakdown`; a corporate-action booking → `corporate-action-interpreter`.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). In short: this skill produces a
plain-language explanation and a normalized explanation object tagged with a durable
`explanation_id`, then stops. It hands off to `trade-break-resolver` (disputes/breaks),
`best-execution-reviewer` (execution quality), and `communications-compliance-reviewer`
(supervised review before client delivery). It never resolves, judges, or advises itself.

## Inputs and prerequisites
- One confirmation at a time: `account_id` (masked), `confirmation_id`, `trade_date`,
  `settlement_date`, `side`, `capacity`, instrument identity, `quantity`, `price`, charges,
  `net_amount`, and a source citation. See the schema in
  [scripts/validate_input.py](scripts/validate_input.py).
- A **citation** (`source.system` + `source.ref`) tying the confirmation to books-and-records
  or the document page/line. Reject a confirmation with no citable source.
- Read permission to the clearing/confirmation source; reference data to resolve instrument
  identity or security type when the document is silent.

## Source hierarchy
Rank sources and cite every figure. See [references/source-map.md](references/source-map.md).
1. Post-trade/clearing books-and-records trade (highest).
2. The customer confirmation document (Rule 10b-10) itself.
3. OMS/EMS execution record; then reference/market data for identity/classification.
Never substitute a user assertion for the books-and-records confirmation; if they conflict,
surface the conflict, cite both, and stop for human review.

## Workflow
1. **Scope one confirmation** — confirm a single `confirmation_id`. If several confirmations
   are present, ask which one (do not merge trades).
2. **Validate input** — run [scripts/validate_input.py](scripts/validate_input.py): required
   fields, valid dates (settlement not before trade), known side/capacity, present citation.
   Fail closed on errors; carry warnings (derivable principal, undisclosed commission/markup,
   missing yield on debt) into the explanation as gaps.
3. **Reproduce the money (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py) to derive principal
   and tie the net amount to `principal + accrued ± charges` per the direction. See
   [references/domain-rules.md](references/domain-rules.md). A tie-out miss is re-checked or
   surfaced, never smoothed over.
4. **Explain, field by field** — state trade/settlement dates, side, capacity (agent vs.
   principal, in neutral terms), quantity and price, principal, each charge and what it is,
   accrued interest and yield where present, and the net amount — each with its citation.
5. **Surface gaps** — undisclosed or ambiguous fields are listed explicitly, not guessed.

## Validation loop
Run `validate_input` before explaining, `calculate_or_transform` to tie out the money, and
`validate_output` after drafting. If a figure does not tie, a key figure lacks a citation, a
required disclosure is missing, or the narrative contains advice/judgment language, **fix or
fail closed** — do not deliver an untied, incomplete, or advice-tainted explanation.

## Human approval
None required for the user's own informational read. **Human review is required before the
explanation is delivered to a client externally** or written to a system of record — supervised
communications review applies (`aws-fsi-human-approval: external-delivery`).

## Failure handling
- **Missing/ambiguous field** (e.g. capacity or price absent) → explain what is disclosed,
  flag the gap; never invent a figure.
- **Net amount does not tie** → surface the discrepancy with both the reported and computed
  figures; route a genuine mismatch to `trade-break-resolver`. Do not "correct" the number.
- **Multiple confirmations in one file** → stop and ask which; do not merge trades.
- **Source conflict** (document vs. clearing) → present both with citations; do not pick a winner.
- **Tool timeout / permission denial** → report partial results and the exact gap; no retry
  assumption.

## Output contract
1. **Header** — account label (masked), `confirmation_id`, trade date, settlement date, currency.
2. **The trade** — side, capacity (agent/principal), instrument, quantity, price, principal.
3. **The money** — commission or markup/markdown, regulatory fees (itemized), accrued interest,
   and the **net amount**, with the tie-out shown.
4. **Notes & gaps** — undisclosed/ambiguous fields listed explicitly.
5. **Machine-readable** — the normalized explanation object with per-figure citations, tagged
   with a durable `explanation_id` for downstream skills.
6. **Standing disclaimer** — "Informational explanation only; not investment advice or a
   recommendation."
Every figure carries a source citation. See [references/controls.md](references/controls.md).

## Privacy and records
Customer NPI/PII. Mask account numbers (show last 4). Do not transmit confirmation data outside
the approved environment. Retain the explanation and its citations per records policy; log the
read and any external-delivery approval. See [references/controls.md](references/controls.md).

## Gotchas
- **Net ≠ price × quantity, and that is normal**: charges, fees, and accrued interest move the
  net away from principal. Explain the bridge; don't treat the difference as an error.
- **Agent vs. principal**: agency shows a commission; principal embeds a markup/markdown in the
  price. State which applies neutrally — do not imply one is better or that a markup was "too high".
- **SEC Section 31 fee / FINRA TAF** generally apply to **sells**, not buys; their absence on a
  purchase is not a missing disclosure.
- **Bonds** quote per 100 face (`price_factor` 0.01), carry **accrued interest**, and require a
  **yield** disclosure — reproduce all three; missing yield is a gap to flag.
- **"Explain" is not "assess"**: describing a USD 9.95 commission is in scope; calling it "too
  high" or the price "a good deal" is advice and is out of scope.
