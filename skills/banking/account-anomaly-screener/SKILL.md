---
name: account-anomaly-screener
description: >-
  Identify unusual account or transaction activity, explain the specific signals that make
  it unusual, and assemble source-linked evidence for customer or fraud-team review. Use
  when a consumer, service agent, or fraud analyst asks "why is this transaction flagged",
  "does this activity look unusual", "screen this account for anomalies", or needs a
  review-ready evidence pack. This skill explains and evidences signals and proposes a
  review priority; it NEVER makes a fraud determination, confirms fraud, blocks/freezes an
  account, or files a report — those are human/authorized-system actions.
license: MIT
compatibility: Amazon Quick Desktop; requires core-banking/transactions, CRM, document-intelligence, and approved-calculation MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Banking"
  aws-fsi-skill-type: "Analysis and evaluation skills"
  aws-fsi-risk-tier: "R2"
  aws-fsi-archetype: "Analyze & review"
  aws-fsi-agent-pattern: "Interactive decision-support copilot"
  aws-fsi-delivery-wave: "Wave 1 — stabilize existing"
  aws-fsi-action-mode: "Read-only analysis"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "existing-updated"
  aws-fsi-human-approval: "external-delivery"
  aws-fsi-data-classification: "Highly Confidential (customer NPI/PII)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Banking fraud & customer operations"
  aws-fsi-primary-user: "Consumer / fraud analyst / service agent"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Account Anomaly Screener

## Purpose and outcome
Given an account's transaction history and the activity in question, compute a set of
**explainable anomaly signals**, explain in plain language why each fired, attach evidence
to each, and produce a review-ready pack with a **suggested review priority**. A successful
output lets a customer understand a flag, or lets a fraud/service reviewer decide what to
do next — the decision, and any action, remains human.

## Use when
- "Why was this transaction flagged / declined for review?"
- "Does this activity look unusual for this account?"
- "Screen the last 90 days for anomalies and give me the evidence."
- A reviewer needs a consistent, cited anomaly write-up to attach to a case.

## Do not use
- The user wants a **fraud determination** ("is this fraud?"), an account **block/freeze**,
  a **dispute filed**, or a **SAR** → out of scope. Provide evidence and route to the human
  reviewer / authorized system; for SAR narrative drafting route to
  `suspicious-activity-report-drafter` (which itself is draft-only).
- **Card-network chargeback/dispute** packaging → `chargeback-dispute-packager` (merchant)
  or `dispute-operations-assistant` (issuer/acquirer).
- **Payment-fraud case investigation** with device/beneficiary network evidence →
  `payment-fraud-case-investigator`.
- General "explain this transaction" with no anomaly question → `trade-confirmation-explainer`
  or `bank-statement-analyzer`.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill emits an evidence pack with
a durable `screening_id`; downstream case/investigation/dispute skills consume it. It must
not duplicate their determination or action steps.

## Inputs and prerequisites
- Account identifier and the **focal activity** (one or more transactions) OR a date window
  to screen.
- **Transaction history** sufficient to establish a baseline (default lookback: 180 days),
  each row with date, amount, direction, merchant/counterparty, channel, and location where
  available. Schema: [scripts/validate_input.py](scripts/validate_input.py).
- Read access to core-banking/transactions and CRM; approved thresholds/config (see
  [references/domain-rules.md](references/domain-rules.md)).

## Source hierarchy
See [references/source-map.md](references/source-map.md). Core-banking transactions are the
position of record; CRM adds customer context (travel notice, life events); reference data
resolves merchants/geos. Cite every signal's evidence to a source row.

## Workflow
1. **Scope & baseline** — confirm the account and focal activity/window; load history for
   the lookback; validate with `validate_input`.
2. **Compute signals (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py) to compute the
   configured signals (amount-vs-history, velocity/frequency, new counterparty, geo/channel
   novelty, dormancy-then-activity, structuring-adjacent patterns). Each signal returns a
   contribution and the evidence rows behind it. Signals are **explainable**, not a
   black-box score.
3. **Assemble evidence** — for each fired signal, attach the specific transactions and the
   baseline it deviates from, with citations.
4. **Suggest priority** — map the fired-signal profile to a review-priority band
   (Informational / Review / Elevated) per the configured, documented mapping. This is a
   triage suggestion for a human, explicitly **not** a fraud determination.
5. **Write the pack** — plain-language explanation per signal + the evidence + the
   suggested priority + explicit uncertainties and benign explanations to consider.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py)
after. The output check confirms: every fired signal has evidence + citation, no
determination/action language is present, the priority maps deterministically from signals,
and benign-explanation prompts are included. Fail closed on any miss.

## Human approval
`external-delivery`: human review required before the pack is sent to a customer or written
to a case/system of record. No approval is needed for the reviewer's own read. The skill
never takes an account action.

## Failure handling
- **Insufficient history** (baseline too thin) → state that signals are low-confidence;
  do not overstate anomalies; list what history is missing.
- **Ambiguous account/identity** → stop and confirm; never screen the wrong account.
- **Missing location/merchant data** → compute only the signals the data supports; label
  the rest "not evaluable".
- **Stale/conflicting sources** → cite both; do not resolve silently.
- **Tool timeout** → return partial signals computed so far with a clear "incomplete" flag.

## Output contract
1. **Summary** — account (masked), window, count of fired signals, suggested priority band.
2. **Signals** — per fired signal: name, plain-language reason, contribution, evidence rows
   (cited), and the baseline it deviates from.
3. **Consider (benign explanations)** — explicit alternative explanations (travel, payroll
   change, known payee) so the reviewer weighs both sides.
4. **Data gaps / not-evaluable signals.**
5. **Machine-readable** — signals + evidence + `screening_id` for downstream skills.
6. **Standing disclaimer** — "Screening evidence only; not a fraud determination. No account
   action has been taken."
See [references/controls.md](references/controls.md).

## Privacy and records
Customer NPI/PII. Mask account/card numbers (last 4). Minimize customer data in output to
what evidences a fired signal. Retain the screening + citations per records policy; log the
read and any external-delivery approval. Never exfiltrate customer data.

## Gotchas
- **A signal is not a decision.** High signal counts justify *review priority*, never a
  fraud conclusion or an account action.
- **Baseline contamination**: if the history window itself contains the suspicious activity,
  exclude the focal transactions from the baseline or the deviation vanishes.
- **Seasonality & payroll**: recurring large credits (payroll, tax refunds) and seasonal
  spend can look anomalous — the benign-explanation prompts exist for this reason.
- **Structuring language is sensitive**: describe amount patterns factually; do not assert
  intent ("structuring to evade") — that is a determination.
- **Do not tune thresholds to a person**: thresholds come from the approved config, not from
  guessing what "should" be normal for this customer.
