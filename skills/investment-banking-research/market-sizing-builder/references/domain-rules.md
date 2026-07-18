# Domain Rules — market-sizing-builder

How the TAM/SAM/SOM model is computed and how scenarios behave. All scenario definitions,
tolerances, and the primary method are **configuration** (versioned, owned by the
research/banking analytics team), never hard-coded judgments and never reverse-engineered to
hit a target number. The computation is deterministic and reproducible from inputs +
`config_version` (see `scripts/calculate_or_transform.py`).

## Definitions

- **TAM** (Total Addressable Market) — total annual demand for the product/service in the
  defined market if every addressable buyer bought.
- **SAM** (Serviceable Addressable Market) — the portion of TAM the business model can serve
  given segment, geography, channel, and regulatory reach.
- **SOM** (Serviceable Obtainable Market) — the realistic share of SAM obtainable over the
  planning horizon given competition and go-to-market capacity.

By construction **SOM ≤ SAM ≤ TAM** in every scenario (a containment tie-out).

## Method 1 — top-down (deterministic)

From a total-market magnitude, apply two fractions:

```
TAM = total_market
SAM = TAM × sam_ratio          (0 ≤ sam_ratio ≤ 1)
SOM = SAM × som_ratio          (0 ≤ som_ratio ≤ 1)
```

## Method 2 — bottom-up (deterministic)

Build from segment unit economics, then sum across segments:

```
segment TAM = units × arpu
segment SAM = segment TAM × attach_rate      (serviceable fraction, 0..1)
segment SOM = segment SAM × capture_rate     (obtainable share, 0..1)
method TAM/SAM/SOM = Σ over segments
```

Segments must be **mutually exclusive and collectively exhaustive** for the total to be valid;
overlapping segments double-count. `validate_input` warns when only one segment is supplied.

## Scenarios (deterministic, documented)

Each driver carries `low`/`base`/`high` values. A scenario evaluates **every** driver at that
scenario's value, so the aggregate TAM/SAM/SOM are monotonic across scenarios:

| Scenario | Meaning |
| -------- | ------- |
| **low** | Conservative assumption set (smaller universe, lower price/attach/capture) |
| **base** | Central, best-estimate assumption set |
| **high** | Optimistic assumption set (larger universe, higher price/attach/capture) |

Because all drivers move together and ratios are non-negative, endings satisfy
`low ≤ base ≤ high` for every level; `validate_output` enforces this scenario-behavior check.
Low/base/high are **assumption ranges, not probabilities** — never present them as odds.

## Triangulation (reconciliation)

For each scenario and level, compare the two methods:

```
gap_pct = |top_down − bottom_up| / max(|top_down|, |bottom_up|)
within_tolerance = gap_pct ≤ triangulation_tolerance_pct   (default 0.20)
```

Triangulation is a **reconciliation signal**, not a pass/fail gate: an out-of-tolerance gap is
reported (and must be investigated and explained), but it does not, by itself, make the exhibit
non-compliant. `validate_output` re-derives every `gap_pct` and `within_tolerance` flag to
ensure the reported reconciliation is arithmetically honest.

## Reported headline (deterministic)

The configured `primary_method` (default `top_down`) supplies the reported TAM/SAM/SOM; the
other method is the cross-check. This is a documented, deterministic rule — the skill does not
silently blend the two into an invented point estimate.

## Tie-outs (formula correctness)

- **Top-down tie-out:** `SAM = TAM × sam_ratio` and `SOM = SAM × som_ratio` per scenario.
- **Bottom-up tie-out:** method TAM/SAM/SOM equal the sum of segment TAM/SAM/SOM per scenario.
- **Containment tie-out:** `SOM ≤ SAM ≤ TAM` per method per scenario.
- **Scenario-ordering tie-out:** `low ≤ base ≤ high` per level per method.
- **Reported tie-out:** the headline equals the primary method's values.

All use a small numeric tolerance for floating-point safety.

## Hard boundaries (fail closed)

- Never give **investment advice** or a personalized recommendation to buy, sell, hold, or
  allocate.
- Never issue a **rating** (buy/sell/hold, overweight/underweight) or a **price target**, and
  never call a security under- or over-valued.
- Never **value a security** or translate a market size into an equity/enterprise value.
- Never **guarantee** revenue, growth, or market share; a size is a range of estimates.
- Never **tune** scenario definitions, tolerances, or the primary method to hit a desired
  number; use only the versioned config, and label internal assumptions as such.

## Interpretation prompts (include when relevant)

Whether segments are MECE; whether the total-market source is official or an industry estimate;
which driver (often SOM/capture) dominates the range; sensitivity of ARPU to mix and discounting;
adoption/attach trends that could move the serviceable fraction; and the reminder that the
downside (low) scenario is a planning aid, not a prediction. Invite the analyst to refine the
softest, lowest-tier drivers first.
