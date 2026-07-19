---
name: market-surveillance-alert-investigator
description: >-
  Investigate an ESCALATED trade- or electronic-communications surveillance alert: resolve
  the entities and events, merge orders, trades, messages, market, and account context into
  a durable, fully cited evidence bundle with a chronology, compute documented manipulation/
  abuse indicators, link prior cases, and produce a disposition RECOMMENDATION. Use when a
  market-surveillance investigator or compliance analyst needs to work up an escalated
  spoofing/layering, wash-trade, marking-the-close, ramping, insider-dealing, or comms-
  collusion case and hand an audit-ready package to an adjudicator. This skill NEVER
  autonomously closes a case, makes a market-abuse determination, exonerates a trader, or
  files a STOR/SAR — every disposition is a recommendation for a qualified supervisor or
  compliance officer, and an un-triaged alert is routed to surveillance-alert-triager first.
license: MIT
compatibility: Amazon Quick Desktop; requires surveillance case-management, OMS/EMS, market/reference-data, electronic-communications-archive, account/customer-context, and prior-case MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Capital Markets"
  aws-fsi-skill-type: "Analysis and evaluation skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Investigate & casework"
  aws-fsi-agent-pattern: "Case agent + evidence bundle"
  aws-fsi-delivery-wave: "Wave 3 - regulated casework"
  aws-fsi-action-mode: "Read-only analysis"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Highly Confidential (customer NPI/PII)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Capital Markets operations & compliance"
  aws-fsi-primary-user: "Market-surveillance investigator / compliance analyst"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Market Surveillance Alert Investigator

## Purpose and outcome
Take an **escalated** trade- or e-comms surveillance alert and work it up into an
audit-ready case: resolve the subject party and events, merge orders, trades, communications,
market data, and account context into a durable, time-ordered **evidence bundle** with a
chronology, compute **documented, explainable indicators** for the alert type, link prior
cases, and produce a disposition **recommendation**. The outcome is a cited package a
supervisor / compliance officer can adjudicate — the substantive disposition, any
market-abuse determination, and any STOR/SAR filing stay with that human.

## Use when
- "Investigate this escalated spoofing/layering alert and build the evidence bundle."
- "Work up this e-comms case: chronology of the chats and trades, and a recommendation."
- "Does this marking-the-close alert hold up? Show the close-window participation."
- "Is this escalation a duplicate of a case we already have open on this trader?"

## Do not use
- **First-line triage** (prioritize a queue, clear obvious false positives, resolve basic
  data issues) → `surveillance-alert-triager`.
- **Comms supervision/disclosure review** beyond surveillance indicators →
  `communications-compliance-reviewer`.
- **Execution-quality / routing** questions (not manipulation) → `best-execution-reviewer`.
- **Adverse-media / external-event** corroboration → `adverse-media-investigator`.
- Any request to **close, determine market abuse, exonerate, or file** → refuse; produce the
  recommendation and route to the human adjudicator.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). Triage, investigation, and adjudication
are separate control activities. This skill **consumes a triage escalation**, emits a durable
`case_id` + evidence bundle, and hands a **recommendation** to a human; it never performs the
triager's or the adjudicator's work. Un-triaged alerts route back to
`surveillance-alert-triager`.

## Inputs and prerequisites
- The escalated case with `alert_id`, `alert_type`, `surveillance_rule_id`, **escalation
  provenance** (`triage_case_id`, `escalated_by`), instrument, period, subject/parties, and
  the relevant streams (orders, trades, messages, market), plus prior cases and the versioned
  threshold config. Schema: [scripts/validate_input.py](scripts/validate_input.py).
- Read access to surveillance case-management, OMS/EMS, market/reference data, the comms
  archive, and account context.

## Source hierarchy
See [references/source-map.md](references/source-map.md). The surveillance case platform is
the system of record for case state; OMS/EMS for order/trade facts; market data for context;
the comms archive for messages. **Cite every evidence item.** Thresholds and the
evidence-strength bands are **versioned contracts**.

## Workflow
1. **Validate & establish provenance** — run `validate_input`. Fail closed if escalation
   provenance is missing (route to `surveillance-alert-triager`); warn on unresolved
   entities, out-of-period events, and absent required streams.
2. **Resolve & build chronology (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py): resolve the
   subject party, merge orders/trades/messages/market into one time-ordered chronology with a
   citation on every event, and compute amounts.
3. **Compute indicators (deterministic)** — the same script computes the documented
   indicators for the alert type (order-to-trade ratio, cancel rate, opposite-side cancel
   clustering, close-window participation, self-match, message-to-trade proximity, flagged
   terms), each with its threshold, breach flag, and citations. See
   [references/domain-rules.md](references/domain-rules.md).
4. **Disposition RECOMMENDATION** — `needs-data` if a required stream is absent;
   `possible-duplicate` if it overlaps an open case (linked, not re-investigated); otherwise
   the evidence-strength band maps to `recommend-refer-regulatory-consideration`,
   `recommend-escalate-to-compliance-review`, or `recommend-close-no-further-action`.
5. **Route where relevant** — attach lateral routing (comms review, adverse-media, best-ex)
   as recommendations, not actions.
6. **Never adjudicate** — no closure, determination, exoneration, or filing.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py)
after. The output screen enforces: durable `case_id` (`MKT-SURV-<alert_id>`); escalation
provenance present; disposition ∈ the allowed recommendation set; every evidence item cited;
strength-based dispositions tie out to the score; and **no closure/determination/filing
language**. Fail closed on any miss.

## Human approval
`required`. Investigation is decision-support: this skill proposes a disposition and assembles
evidence. **Every** case closure, market-abuse determination, exoneration, and STOR/SAR
filing is adjudicated by a qualified supervisor / compliance officer / MLRO through the
approval broker. The skill recommends; humans decide.

## Failure handling
- **Missing required stream** → `needs-data`, list exactly what is missing; never guess to
  clear or escalate.
- **Un-triaged alert (no provenance)** → fail closed; route to `surveillance-alert-triager`.
- **Ambiguous entity / dedup** → link as `possible-duplicate` for human confirmation; never
  auto-merge or re-investigate in parallel.
- **Out-of-period / conflicting events** → flag in the chronology and cite; do not drop.
- **MNPI / insider signal** → surface as an indicator for review within the authorized
  channel; do not broadcast MNPI or conclude insider dealing.
- **Tool timeout** → return the partial bundle with an explicit incomplete flag; no retry
  assumption.

## Output contract
1. **Case list** — per case: `alert_id`, durable `case_id`, `alert_type`, escalation
   provenance, `disposition_recommendation`, `evidence_strength_score` + reason.
2. **Evidence bundle** (per case) — subject + parties (masked) with roles; time-ordered
   chronology (each event cited); amounts (traded qty, notional, currency); indicators with
   thresholds and citations; linked cases; full citation list.
3. **Rationale** — recommendation tied to the breached indicators (recommendation language).
4. **Routing** — lateral/downstream handoffs where relevant.
5. **Machine-readable** — the case records + bundles keyed by durable `case_id`.
6. **Standing note** — "Investigation decision-support only; no case has been closed, no
   market-abuse determination has been made, and no regulatory report (e.g., STOR/SAR) has
   been filed. A qualified supervisor or compliance officer must adjudicate every
   disposition."
See [references/controls.md](references/controls.md).

## Privacy and records
**Highly Confidential (customer NPI/PII + MNPI).** Communications content and identities are
sensitive; mask account/party identifiers to what the evidence requires. Respect
**information barriers** — keep MNPI/insider signals within the authorized surveillance/
compliance channel. Retain the evidence bundle, indicator values, thresholds/config version,
and citations per surveillance recordkeeping; log analyst identity on every read and on the
recommendation.

## Gotchas
- **Indicators are evidence, not findings.** A breached threshold is weight-of-evidence for a
  human; it is never a determination that abuse occurred.
- **Recommendation ≠ disposition.** `recommend-close-no-further-action` proposes a close; the
  case is only closed when an authorized human adjudicates it.
- **Provenance gates investigation.** No triage escalation ⇒ do not investigate; route to
  triage. This preserves segregation of duties.
- **Dedup links, never merges.** `possible-duplicate` points at the open case; it is not a
  closure and not a parallel investigation.
- **Config is versioned.** Record the thresholds/band version on every bundle so the
  recommendation is reproducible and reviewable.
- **Comms proximity is directional.** Proximity is measured only from a flagged message to a
  *subsequent* order/trade; earlier activity is not "explained" by a later message.
