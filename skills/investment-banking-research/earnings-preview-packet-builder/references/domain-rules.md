# Domain Rules - earnings-preview-packet-builder

Orientation references: the firm's research-publication standard and supervisory-analyst
(SA) review policy, research-analyst conduct rules (e.g. FINRA 2241-style disclosure /
supervision expectations), the information-barrier / control-room policy, and the approved
preview **template** (a versioned contract). The firm's standards and the template version
take precedence and are versioned contracts.

## Durable identifiers

- **`packet_id`** - durable per-issuer/period identifier, `EPP-{TICKER}-{FISCAL_PERIOD}`
  (e.g. `EPP-ACME-FY26Q2`). One packet per issuer-event; re-runs replace the packet rather
  than creating parallel briefs.
- **`job_id`** - the durable build/run identifier for a given assembly, for audit and
  idempotency. Recording both keeps every assembly reproducible and reviewable.

## Item-inventory rules (every substantive item)

An item is `ready` only when **all** of the following hold; otherwise it is blocked and the
first blocking condition sets the status:

| Requirement | Blocking status if missing |
| ----------- | -------------------------- |
| A one-line **takeaway** (factual "what to watch", not a view) | `needs-source` |
| At least one **source citation** | `needs-source` |
| Every **data point** maps to an **approved** `source_ref` | `unsupported-claim` |
| Every forward-looking data point is **third-party attributed** | `unsupported-claim` |
| Content **approval** recorded (`approved`) | `needs-approval` |

## Attribution & no-origination rule (the HARD BOUNDARY)

The packet **compiles**; it does not opine. Enforced by `validate_input`/`validate_output`:

- Forward-looking data points (`kind` = `consensus`, `guidance`, `sensitivity`) must carry an
  `attribution` to a third party (consensus provider, company guidance/disclosure, cited
  sell-side note, cited news). An attribution of `self`/`own`/`analyst`/`house`/`our-model`
  is rejected - the packet never carries an originated estimate.
- Data-point `kind` of `own_forecast`, `target`, `price_target`, `rating`, or `trade_view` is
  **prohibited** entirely.
- **Prohibited language** (blocked by `validate_output`, fail closed): assigned ratings
  ("rating: buy", "we rate", "upgrade to buy", "reiterate buy"); price targets with a value
  ("price target of $220", "PT: $220", "fair value of $..."); first-person forecasts ("we
  forecast/estimate/project/model", "our estimate of", "we are above consensus"); and trade
  views / personalized advice ("we recommend buying", "you should buy", "buy the dip", "top
  pick", "add to the position", "go long into the print").
- Consensus is a **third-party aggregate**, cited to its provider - not the skill's number.
  Guidance is reproduced **as issued**, cited to the filing/transcript.

## Descriptive arithmetic only (what the engine may compute)

The deterministic engine performs factual transforms of already-sourced numbers, never a
projection:

- **Consensus-vs-guidance positioning** - reports whether each metric's cited consensus value
  sits below/within/above the company's cited prior-guidance range, plus the numeric gap to
  the range midpoint. It states where two sourced numbers sit relative to each other; it does
  **not** predict the print.
- **KPI trend** - QoQ and YoY deltas computed from the reported historical KPI series. No
  value is projected for the upcoming period.

## Required approvals before external distribution

| Approval role | Owner | Purpose |
| ------------- | ----- | ------- |
| `supervisory_analyst` | Registered supervisory analyst | Research-content supervision and sign-off |
| `research_compliance` | Research compliance / control room | Disclosures, conflicts, wall-cross, information barriers |
| `legal_disclaimers` | Legal | Confidentiality and no-offer / no-advice / no-recommendation disclaimer set |

`ready-for-distribution` is permitted **only** when all required approvals are recorded and
`approved`; otherwise the packet stays `hold-for-approval`. The preparer must not self-approve
the control approvals (segregation of duties).

## Template fidelity & completeness

The assembled packet must contain every section in the template's `required_sections`
(default: cover, event-calendar, consensus-snapshot, prior-guidance, historical-kpis,
controversies-and-debates, sensitivities, open-questions, disclaimer). Items are ordered by
the template's section order; a missing required section blocks `ready-for-distribution`.

## Hard boundaries (fail closed)

- Never set a **forecast, rating, price target, or trade view**; never carry an originated
  estimate or personalized investment advice.
- Never **publish / send / distribute / file**; never set a distributed state.
- Never **fabricate** a figure, KPI, controversy, or source; never keep an unattributed
  forward-looking figure.
- Never **self-approve** the required control approvals (segregation of duties).
- Pre-event only: post-earnings beat/miss, guidance-revision, and thesis-impact analysis
  belong to `earnings-results-analyzer`.

## Assembled packet - required contents

`packet_id`, `job_id`, `as_of_date`, issuer, event calendar; template `id@version`; ordered
items each with takeaway, sources, attributed data points, and status;
`sections_present`/`sections_missing`; `consensus_vs_guidance` positioning; `kpi_trends`;
`unsupported_items`; recorded `required_approvals` + `approvals` with status; `packet_status`;
draft-only notice and standing note.
