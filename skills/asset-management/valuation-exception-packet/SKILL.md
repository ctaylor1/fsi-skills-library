---
name: valuation-exception-packet
description: >-
  Investigate pricing exceptions on a fund book: identify stale, missing, disputed, or
  outlier prices and compile vendor evaluated prices, broker quotes, trade prints, and the
  pricing-hierarchy rules into a cited valuation-exception packet with a durable case_id and
  an evidence bundle for the valuation committee. Use when a valuation analyst works a
  price-exception queue, explains why a security looks stale, absent, disputed, or off-market,
  or packages pricing evidence for committee adjudication or NAV tie-out. Every candidate
  price is tagged as an OBSERVED price (exchange close, vendor evaluated, executable quote,
  trade print) or a HYPOTHESIS (matrix, model, indicative quote, carry-forward). HARD
  BOUNDARY: this skill NEVER selects or overrides a valuation, chooses a canonical price,
  certifies or strikes NAV, or closes the exception; it produces recommendations and cited
  evidence only, and the valuation committee plus fund accounting adjudicate. Routes
  reconciliation and NAV tie-out to adjacent skills.
license: MIT
compatibility: Amazon Quick Desktop; requires pricing/IBOR, approved-pricing-vendor, broker-quote, trade-blotter/OMS, corporate-actions, and valuation-policy/tolerance MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Asset Management"
  aws-fsi-skill-type: "Analysis and evaluation skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Investigate & casework"
  aws-fsi-agent-pattern: "Case agent + evidence bundle"
  aws-fsi-delivery-wave: "Wave 5 - 2026 industry expansion"
  aws-fsi-action-mode: "Read-only analysis"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Highly Confidential (MNPI / client-confidential)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Asset Management investment & product"
  aws-fsi-primary-user: "Valuation analyst"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Valuation Exception Packet

## Purpose and outcome
Take the securities on a fund book as of a valuation date and make the price-exception queue
workable: detect which instruments are **stale, missing, disputed, or outlier**, gather every
candidate price with its as-of time, apply the firm's documented **pricing hierarchy**, and
assemble an audit-ready **valuation-exception packet** — a durable `case_id` per instrument
plus an evidence bundle (chronology, parties, amounts, hierarchy, citations). The outcome is a
cited, committee-ready packet that ranks exceptions by severity and, for each, **recommends a
next step**. Every candidate price is explicitly tagged **observation** or **hypothesis**. The
skill never picks the price or the NAV — the valuation committee and fund accounting do.

## Use when
- "Work my valuation-exception queue for today's close / prioritize these price exceptions."
- "Why does this security's price look stale / missing / off-market?"
- "Two vendors disagree on this bond — package the evidence for the pricing committee."
- "Compile the pricing evidence for this name for NAV tie-out."

## Do not use
- **Selecting or overriding the price / choosing the canonical value** → not permitted here;
  package the evidence and route to the human **Valuation Committee**.
- **Certifying or striking NAV / posting an accounting entry** → the human **fund accounting /
  NAV oversight** function, working `nav-preparation-tie-out`.
- **Internal-vs-vendor reference/price feed reconciliation** (field-level discrepancies across
  feeds) → `investment-vendor-feed-reconciler`.
- **Feed-level data-quality detection** (stale/absent/implausible signals across the whole
  feed) → `investment-data-quality-exception-detector`.
- Any request to **close, resolve, or finalize** an exception, or to state the "correct" price
  → refuse; produce the packet and route to the committee.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). Exception **investigation/packaging**
(this skill) is deliberately separated from **reconciliation** (upstream) and from **NAV
striking / price decision** (downstream human adjudication). This skill emits a durable
`case_id` + evidence bundle; it must not perform the reconciler's matching or the committee's
decision. Adjacent skills referenced here exist in the catalog; NAV certification and price
selection are human handoffs (no skill decides them).

## Inputs and prerequisites
- The book as of a valuation date: per instrument the `instrument_id`, `asset_class`, any
  `prior_price` (+ date), optional `market_value` and `benchmark_return_pct`, an
  `open_challenge` flag, and the **candidate prices** (each with `source_id`, `source_type`,
  `price`, `as_of`). The versioned **valuation-tolerance config** (staleness days, outlier
  bands, dispute tolerance by asset class) and the pricing hierarchy. Schema:
  [scripts/validate_input.py](scripts/validate_input.py).
- Read access to pricing/IBOR (system of record for the carried price), approved pricing
  vendors, broker-quote capture, the trade blotter/OMS, corporate actions, and the valuation
  policy/tolerance config. All read-only.

## Source hierarchy
See [references/source-map.md](references/source-map.md). Pricing/IBOR is the system of record
for the carried price and holdings; approved vendors, executable quotes, and trade prints are
**observed** inputs; matrix/model/indicative/carry-forward are **hypotheses**. Cite every
evidence item with its as-of time/version. Tolerance config and the hierarchy are **versioned
contracts** recorded on every case.

## Workflow
1. **Validate & normalize** — run `validate_input`; confirm each instrument has an id, asset
   class, and a source ref; flag inputs that block assessment (`needs-data`).
2. **Classify each candidate price** — tag every price `observation` or `hypothesis` from its
   `source_type` via the documented pricing hierarchy. A hypothesis is never treated as an
   observed price. See [references/domain-rules.md](references/domain-rules.md).
3. **Detect exceptions (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py): computes staleness
   (business days), day-over-day move %, and cross-source dispersion %, then flags
   **stale / missing / disputed / outlier** against the versioned tolerances. An open
   challenge forces the exception to the top severity band.
4. **Score severity (deterministic)** — a documented, explainable severity band (P1–P3) from
   exception type, magnitude, materiality, and liquidity — a triage rank for the committee,
   **not** a valuation conclusion.
5. **Assemble the evidence bundle** — for each exception build the chronology (priced
   observations and hypotheses over time), parties (vendors, brokers, challenger), amounts
   (observed prices vs hypotheses, market value), the hierarchy reference, citations, and a
   durable `case_id`; set disposition `exception-confirmed` and `adjudication: human-required`.
6. **Recommend, never decide** — record an advisory `recommended_next_step` (e.g., obtain a
   challenge quote, confirm against a trade print, refer to the committee). Never select a
   price, override a mark, certify NAV, or close the case.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py)
after. The output screen enforces: durable `case_id`/`job_id` present; only allowed
dispositions (no `price-selected`/`nav-certified`/`closed`); no prohibited decision fields
(`final_price`, `selected_price`, `override_price`, `certified_nav`, …); every candidate price
carries a `price_type` consistent with its source (**no hypothesis presented as an
observation**); every exception bundle is cited; severity band ties to the deterministic
mapping; no price-selection / override / NAV-certification language; standing note present.
Fail closed on any miss.

## Human approval
`required`. This skill is decision-**support**: it compiles evidence and recommendations only.
The price selection/override is the **Valuation Committee's**; NAV striking/certification is
**fund accounting / NAV oversight's**. This skill proposes and packages; humans adjudicate.

## Failure handling
- **Missing assessment inputs** (no asset class, no pricing inputs at all) → `needs-data`, list
  exactly what is missing; do not guess a price to clear an instrument.
- **No observed price, only hypotheses** → `exception-confirmed` type `missing`; surface the
  hypotheses tagged as hypotheses; recommend obtaining an observation or a committee fair-value
  determination — never adopt the hypothesis as the price.
- **Conflicting sources** → `disputed`; cite every source with its as-of time; do not resolve.
- **Stale/effective-date drift** → record the config version and as-of; if the tolerance config
  is stale or unversioned, fail closed and flag it.
- **Tool timeout / partial book** → return the partial packet with an explicit incomplete flag;
  assume no retry and no step-up authorization.

## Output contract
1. **Exception queue** — per instrument: `case_id`, `exception_type`(s), severity band,
   disposition (`exception-confirmed` | `needs-data` | `no-exception-detected`), one-line cited
   reason.
2. **Evidence bundle** (per confirmed exception) — chronology, parties (masked), amounts
   (observed prices vs hypotheses), hierarchy reference, metrics (staleness / move % /
   dispersion %), citations, `recommended_next_step`, `adjudication: human-required`.
3. **Observed-vs-hypothesis ledger** — every candidate price tagged `observation`/`hypothesis`.
4. **Data gaps / needs-data list.**
5. **Machine-readable** — the exception records + bundles keyed by `case_id`, under `job_id`.
6. **Standing note** — "Valuation exception packet only; no price has been selected or
   overridden and no NAV has been certified or struck. Observed prices and hypotheses are
   evidence for the valuation committee's decision."
See [references/controls.md](references/controls.md).

## Privacy and records
**Highly Confidential (MNPI / client-confidential).** Holdings, vendor marks, and broker quotes
are market- and client-sensitive; vendor pricing may be licensed — cite provenance, do not
redistribute raw vendor data beyond entitlement. Mask account/holder identifiers to what
evidences the exception. Retain packets, citations, and the tolerance/hierarchy versions per
records policy; log every read and every packet generation with the analyst identity.

## Gotchas
- **Observation ≠ hypothesis.** A matrix/model/indicative/carry-forward price is evidence, not
  an observed price. Presenting one as observed is a hard failure.
- **Packaging ≠ deciding.** Confirming an exception and recommending a next step is not
  selecting the price or striking NAV — those are the committee's and fund accounting's.
- **Stale needs an as-of, not a guess.** Staleness is measured in business days against the
  valuation date; carrying a price forward is a committee call, never an automatic fill.
- **Dispute means cite both.** Do not collapse two disagreeing sources into one number; the
  dispersion and both marks are the evidence.
- **Config is versioned.** Record the tolerance/hierarchy version on every case so the exception
  is reproducible and reviewable.
