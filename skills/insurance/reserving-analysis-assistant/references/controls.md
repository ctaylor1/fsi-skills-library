# Controls — reserving-analysis-assistant

- **Risk tier:** R2 — analytical / drafting support. No binding decision. **Action mode:**
  Draft-only; no system-of-record change.
- **Human approval:** `external-delivery` — a qualified (appointed) actuary must review,
  select, and approve before any reserve indication is used externally, relied upon, or
  booked. Internal drafting may be reviewer-sampled.

## Prohibited (fail closed)

- **Reserve selection or booking.** The skill computes method **indications**; it never
  selects the carried reserve, books IBNR to the ledger, or changes a system of record.
- **Reserve-adequacy opinion.** No statement that reserves are adequate, sufficient,
  deficient, or reasonable; no Statement of Actuarial Opinion; no "we opine".
- **Filing / signing / submission** of any opinion, exhibit, or reserve figure to a board,
  regulator, or auditor. A human submits after review.
- **Unsupported assertions.** Every figure must tie to the supplied triangle/data and cite
  its source; ultimate must equal reported + IBNR. No invented or smoothed data.
- **Personalized financial/actuarial advice** beyond the mechanical, cited analysis.

## Segment statuses (this skill may set only these)

`draft-analysis` (packageable) | `anomaly-flagged` (data anomaly; not packageable until an
actuary reviews) | `needs-data` (triangle too immature / undefined factor). It may **not**
set `selected`, `booked`, `filed`, `opined`, `adequate`, or `final`.

## Required output screens (`scripts/validate_output.py`)

- **Template fidelity** — all eight required sections present (see
  [../assets/output-template.md](../assets/output-template.md)).
- **Required approvals recorded** — the approval block lists a qualified/appointed actuary
  and every sign-off is `pending`/`required`; the skill never self-approves (`approved`,
  `signed`, `accepted`, `final`, `booked` are rejected).
- **Method fidelity** — every segment uses an approved method (volume-weighted or
  simple-average chain-ladder).
- **Completeness + source mapping** — a packageable segment has development factors, CDFs,
  per-origin ultimate/IBNR, totals, and a citation on every figure.
- **No unsupported assertions** — per-origin and total tie-outs hold (ultimate = reported +
  IBNR); no adequacy/opinion, booking, or filing language (regex-screened).
- **Standing note present** — the draft-only / no-selection / no-opinion disclaimer.

## Method & data discipline

- Development factors are computed volume-weighted (default) or simple-average across the
  origins that have both development periods; the tail factor is applied once to reach
  ultimate. IBNR = indicated ultimate − reported (latest diagonal).
- A paid triangle that decreases, or an incurred triangle that drops > 20% period-over-
  period, is a data anomaly → `anomaly-flagged`; it is **never** packaged on a guess.
- Uncertainty is an **indicative** min-max link-ratio range, explicitly not a statistical
  confidence interval and not a reserve-range opinion.

## Data classification, privacy, records

- **Highly Confidential (customer NPI/PII).** Work at the aggregate triangle level; include
  claim-level identifiers only for flagged large losses, and mask where not needed.
- Retain the draft exhibit, `dataset_version`, valuation date, citations, and the actuarial
  sign-off with the analysis; log every read and every exhibit produced with the analyst
  identity. Recertify per the recertification date.
