# Controls — comps-analysis-builder

- **Risk tier:** R2 — analytical / drafting support. **Action mode:** Draft-only; no
  system-of-record change. The output is a draft comps analysis for human review, not a
  valuation opinion, a recommendation, or a delivery.
- **Human approval:** `external-delivery` — a human must review and approve before the analysis
  is delivered externally, relied on for a valuation conclusion, or treated as a
  system-of-record change. Internal analytical assembly may be reviewer-sampled.

## Prohibited (fail closed)

- **Investment recommendation / rating / price target**: any buy/sell/hold, overweight/
  underweight, "we recommend", or price-/target-price statement. Comps produce an implied
  cross-check range only.
- **Valuation / fairness opinion**: any "fair value is", "the company is worth", "intrinsic
  value is", "fairness opinion", or "guaranteed return" language. A binding valuation opinion is
  a licensed, human-owned deliverable.
- **Fabrication**: inventing an operating metric, price, share count, or estimate. Missing
  metrics are non-meaningful multiples and missing-metric open items.
- **Cherry-picking**: selecting or excluding peers to steer the result. Inclusion/exclusion
  follows the versioned selection criteria and every entry is cited and human-confirmable.
- **Selective disclosure / MNPI misuse**: using or exposing material non-public information
  outside the information-barrier / wall-crossing controls.
- **Delivery / submission**: sending, submitting, distributing, or delivering the analysis.
  Draft-only.

## Build / peer states (this skill may set only these)

- Per peer: `included` | `included-stale` | `excluded` (with cited reason).
- Per multiple: `meaningful` | `nm` (non-positive denominator) | `missing` | `outlier`
  (outside the configured band; excluded from statistics).
- Analysis: `draft-comps` only. It may **not** set `final`, `approved`, `delivered`, or any
  valuation-conclusion state.

## Required output screens (`scripts/validate_output.py`)

- All required template sections present (mirrors [../assets/output-template.md](../assets/output-template.md)).
- Every EV bridge and every company multiples row carries a citation; every implied-value row
  cites a summary-statistic basis that exists (no unsupported/unapproved claims).
- Deterministic tie-outs hold: `market_cap == share_price * diluted_shares` and
  `enterprise_value == market_cap + debt + preferred + minority - cash` for every bridge.
- Recorded approvals carry `type`, `approver_role`, `date`, and `citation`; missing required
  approvals appear as outstanding open items; `human_approval_required_before_delivery` is `true`.
- No recommendation/rating/price-target, valuation/fairness-opinion, MNPI, or send/deliver
  language.
- `build_status` equals `draft-comps`.
- Standing note present (see [domain-rules.md](domain-rules.md)).

## Segregation of duties

Building the comps set is distinct from the valuation conclusion, from independent valuation
review, and from external delivery. The same person/skill must not both assemble the comps and
sign off the valuation opinion or deliver it to the client.

## Data classification, privacy, records

- **Highly Confidential (MNPI / client-confidential).** Enforce information barriers; use
  data-room (non-public) figures only when the user is wall-crossed and permissioned. Mask
  approver and internal identifiers in output.
- Retain the analysis manifest, citations, and config/template versions per the firm's
  research/deal recordkeeping policy; log the analyst identity on every read and build.
- Keep data within the deployment's residency boundary.
