# Controls — market-sizing-builder

- **Risk tier:** R2 — analytical / model. **Action mode:** Draft-only; no system-of-record change.
- **Human approval:** `external-delivery` — required before the sizing exhibit is delivered to a
  client or written to a data room / system of record. Internal analytical use may be
  reviewer-sampled.

## Prohibited (fail closed)

- No **investment advice** or personalized recommendation to buy, sell, hold, allocate, or
  divest ("you should buy", "we recommend investing").
- No **rating or price target** — never state or imply a buy/sell/hold, overweight/underweight,
  price target, expected return, or that a security is under- or over-valued.
- No **security valuation** — never convert a market size into an equity or enterprise value or
  an implied multiple recommendation.
- No **guarantee or promise** of revenue, growth, or market share ("guaranteed return",
  "risk-free"). A market size is a range of estimates.
- No **per-deal tuning** of scenario definitions, tolerances, or the primary method; these come
  from the versioned config, not from working backward to a desired number.
- No **system-of-record write** — the skill produces a draft artifact only.

## Required output screens (`scripts/validate_output.py`)

- Both methods (`top_down`, `bottom_up`) present with every configured scenario.
- Top-down tie-outs recompute: `SAM = TAM × sam_ratio`, `SOM = SAM × som_ratio` per scenario.
- Bottom-up tie-outs recompute: method totals equal the sum of segment TAM/SAM/SOM per scenario.
- Containment holds: `SOM ≤ SAM ≤ TAM` per method per scenario.
- Scenario behavior ordered: `low ≤ base ≤ high` per level per method.
- Triangulation gaps and `within_tolerance` flags are internally consistent (re-derived).
- Reported headline equals the primary method's values.
- Every `assumptions_register` entry carries non-empty `provenance` **and** `source_tier`.
- No investment-advice / rating / price-target / guarantee language (regex screen over
  narrative + notes).
- Standing disclaimer present: "Market-size estimates for analytical purposes only; not
  investment advice, not a recommendation to buy, sell, or hold any security, and not a
  guarantee of revenue or market share. Estimates depend on the stated assumptions and sources
  and will vary."

## Reproducibility & tie-outs

- `sizing_id` + `config_version` make every scenario, tie-out, and triangulation gap
  reproducible from inputs. Re-running the same inputs and config yields identical figures.
- Triangulation is a reported reconciliation signal; an out-of-tolerance gap must be explained
  in the narrative but does not by itself fail the compliance screen.

## Conduct / research independence

- Do not let a desired conclusion drive the assumptions; the size follows the sourced drivers,
  not the other way around.
- Keep the analytical exhibit free of any recommendation; ratings and advice are the domain of
  licensed research/banking professionals and their supervised process.
- Respect information barriers between advisory and research/public-side activities.

## Data classification, privacy, records

- **Highly Confidential (MNPI / client-confidential).** Treat market definitions, drivers, and
  data-room figures as material non-public information.
- Minimize data in the exhibit to what the sizing needs; do not commingle engagements.
- Retain the sizing exhibit + assumptions register + config version per records policy; log the
  read and any external-delivery approval. Never exfiltrate client or data-room content.
