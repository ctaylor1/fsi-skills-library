---
name: investment-data-quality-exception-detector
description: >-
  Detect data-quality exceptions in approved investment data feeds — stale prices, absent
  risk/analytic factors, duplicate instruments, implausible day-over-day price moves,
  conflicting classifications across feeds, and broken security-master mappings — and produce
  a prioritized, evidence-cited exception queue for an investment-data analyst to work. Use
  when someone asks to run a data-quality / DQ sweep on a pricing or reference-data snapshot,
  screen a portfolio feed for stale or implausible prices, find duplicate or unmapped
  instruments, or triage a feed exception queue before it reaches valuation, risk, or client
  reporting. This skill only detects, evidences, and prioritizes: it NEVER silently corrects,
  overrides, or fills a value, NEVER suppresses, waives, or closes an exception, and NEVER
  decides which feed is canonical. Route reference-data conflicts (conflicting
  prices/ratings/classifications) to investment-vendor-feed-reconciler; identity/mapping
  conflicts to the security-master steward.
license: MIT
compatibility: Amazon Quick Desktop; requires market-data/pricing, security-master/reference-data, entity-resolution, and approved-calculation MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Asset Management"
  aws-fsi-skill-type: "Analysis and evaluation skills"
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
  aws-fsi-primary-user: "Investment-data analyst"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Investment Data Quality Exception Detector

## Purpose and outcome
Given a snapshot of approved investment data feeds (instruments, prices, factors,
classifications, and security-master mappings), run a fixed set of **deterministic
data-quality checks**, attach cited evidence to every exception, assign each a **severity**
from versioned config, and emit a **prioritized exception queue** with a durable
`exception_queue_id`. A successful output lets an investment-data analyst work the queue in
priority order and route each item to the right owner — while the data itself, and any
correction, stays with the source owner and the human. The detector finds and evidences
problems; it never fixes them.

## Use when
- "Run a data-quality / DQ sweep on today's pricing and reference-data snapshot."
- "Screen this portfolio feed for stale or implausible prices before valuation."
- "Find duplicate instruments or unmapped securities in the feed."
- "Which holdings are missing required risk factors?"
- "Build the feed exception queue for the data desk to work this morning."

## Do not use
- The user wants the exception **corrected, overridden, or filled** ("set the price to X",
  "use vendor A's value", "fix the mapping") → out of scope. This skill never mutates or
  chooses a value; correction is a source-owner action.
- The user wants an exception **suppressed, waived, dismissed, or closed** → out of scope;
  disposition is a human/case action, not this detector's.
- **Reference-data conflict** where two approved sources disagree on a price, rating, index
  membership, corporate-action term, or classification and someone must reconcile them →
  `investment-vendor-feed-reconciler` (it produces field-level discrepancies; it also does
  not choose the canonical value).
- **Identity / mapping conflict** needing security-master enrichment or a new/merged
  security record → `security-master-enricher` and the security-master steward.
- The feed is not yet normalized into the canonical schema → normalize first via
  `holdings-transaction-normalizer`, then run this detector on the canonical snapshot.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill emits an evidence-cited
exception queue with a durable `exception_queue_id` and a per-exception `route_to`; the
reconciler and security-master skills consume the referenced items rather than re-detecting.
It must not duplicate their reconciliation or enrichment, and it never chooses a value.

## Inputs and prerequisites
- A **feed snapshot** for one portfolio/universe as of a stated date: `instruments[]` (key,
  identifiers, asset class, held flag, required factors), `prices[]`, `factors[]`,
  `classifications[]` (per feed), and `mappings[]`. Schema and field rules:
  [scripts/validate_input.py](scripts/validate_input.py).
- The **DQ config version** (thresholds and per-type severities). Config is a versioned
  contract; see [references/domain-rules.md](references/domain-rules.md).
- Read access to market-data/pricing, security-master/reference-data, and entity resolution.
  All read-only; no writes to any source of record.

## Source hierarchy
See [references/source-map.md](references/source-map.md). The approved market-data feed is
the position of record for prices; the security master is the position of record for
identity and reference data; the versioned DQ config supplies thresholds and severities.
Every exception cites the specific feed row(s) and their **as-of** time. When two approved
sources disagree, this skill records the disagreement as an exception and routes it — it
does not resolve it.

## Workflow
1. **Scope & load** — confirm the portfolio/universe and snapshot `as_of`; load the feed
   snapshot; validate with `validate_input`. Fail closed on structural problems; note
   evaluability gaps as warnings.
2. **Run checks (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py) to evaluate the
   six checks: `stale_price`, `implausible_move`, `absent_factor`, `duplicate_instrument`,
   `conflicting_classification`, `broken_mapping`. Each produced exception carries its
   evidence rows (with citations + as-of), a reason, a `severity`, and a `route_to`.
3. **Prioritize (deterministic)** — the engine assigns each exception a severity from the
   versioned config (escalated one band when the instrument is NAV-impacting for
   valuation-critical types) and maps the exception set to a queue priority band
   (`P1`–`P4`) per the documented rule in `domain-rules.md`.
4. **Route** — tag reference-data conflicts to `investment-vendor-feed-reconciler` and
   identity/mapping conflicts to `security-master-enricher`/the steward; leave price and
   factor exceptions for the data analyst to work with the source owner.
5. **Write the queue** — plain-language summary + the prioritized exceptions, each with
   evidence, severity, and route — plus what was checked, what was not evaluable, and the
   standing disclaimer.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py)
after. The output screen confirms: every exception has ≥1 cited evidence row with an as-of;
severity and `queue_priority` tie out to the deterministic mapping; every open exception has
`status` = `open` (nothing suppressed/closed); no correction/override/canonical-choice
fields are present; reference-data-conflict types carry the correct `route_to`; no
correction, suppression, or advice language appears; and the standing disclaimer is present.
Fail closed on any miss.

## Human approval
`external-delivery`: human review is required before the queue is delivered to another team,
written to a case/system of record, or used to drive a correction. No approval is needed for
the analyst's own read. The skill never writes to a feed, never corrects a value, and never
closes an exception.

## Failure handling
- **Missing identifiers** on an instrument → `duplicate_instrument` is not evaluable for that
  row; label it and continue.
- **No timestamps / as-of on a price** → cannot judge staleness for that row; mark
  `not_evaluable`, do not assume fresh.
- **Thin history** (no `prev_price`) → `implausible_move` not evaluable for that row; do not
  fabricate a prior.
- **Dangling reference** (a price/factor/classification points to an unknown instrument key)
  → this is itself a `broken_mapping` exception, not an input error.
- **Ambiguous portfolio/snapshot** → stop and confirm; never screen the wrong universe.
- **Tool timeout** → return the exceptions found so far with an explicit `incomplete` flag;
  page long universes as resumable stages.

## Output contract
1. **Summary** — portfolio (masked where needed), `as_of`, config version, exception count
   by type and severity, and the `queue_priority` band.
2. **Exception queue** — per exception: `exception_id`, `type`, instrument (key + best
   identifier), `severity`, plain-language `reason`, `evidence[]` (cited, with as-of), the
   baseline/threshold it breached, `route_to`, and `status` = `open`.
3. **Not evaluable / checks skipped** — rows or checks the data did not support, with why.
4. **Machine-readable** — the full queue JSON with `exception_queue_id` for downstream
   skills.
5. **Standing disclaimer** — "Detection evidence only; exceptions are open findings. No data
   has been corrected, overridden, or suppressed, and no canonical value has been chosen."
See [references/controls.md](references/controls.md).

## Privacy and records
Holdings and pricing can be MNPI / client-confidential. Minimize data in the queue to what
evidences an exception; mask account/portfolio identifiers where the audience does not need
them. Retain the queue + citations + config version per records policy; log the read and any
external-delivery approval. Never exfiltrate holdings or pricing data.

## Gotchas
- **A detection is not a decision.** The queue flags and prioritizes; it never states the
  "correct" value, the canonical feed, or a NAV adjustment — those are reconciliation and
  source-owner actions.
- **Stale ≠ wrong, implausible ≠ error.** A flat price may be a genuinely non-trading
  instrument; a large move may be a real corporate action. The queue evidences the pattern
  and leaves the judgement to the analyst and source owner.
- **Config is versioned, never tuned to a name.** Thresholds and severities come from the
  recorded config version so a sweep is reproducible; do not hand-tune per instrument.
- **Conflicts route, they do not resolve.** When two approved feeds disagree, record the
  disagreement and route to the reconciler; choosing a winner here would be an unauthorized
  decision.
- **Duplicate vs. legitimate multi-listing.** The same economic instrument can legitimately
  carry multiple listings/identifiers; evidence the identifier collision, do not assert one
  record must be deleted.
