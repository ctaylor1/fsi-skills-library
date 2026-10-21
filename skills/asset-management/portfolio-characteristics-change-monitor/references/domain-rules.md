# Domain Rules — portfolio-characteristics-change-monitor

How the prior→current **change** for each portfolio characteristic is computed, when a change
becomes an **exception**, when a characteristic is **routed** to compliance, and how the
flagged set maps to a **review-priority band**. Attention bands and the routing buffer are
configuration (versioned, owned by the risk-analytics team), not hard-coded judgments, and
are never tuned to an individual portfolio. The firm's risk-analytics standard and the fund's
IPS/mandate take precedence over this file.

## Characteristics compared (approved snapshots only)

| Family | Characteristic(s) | Change | Default attention band |
| ------ | ----------------- | ------ | ---------------------- |
| scalar | `tracking_error` (ex-ante, %) | current − prior | `tracking_error_band` = 0.50 |
| scalar | `duration` (effective, yrs) | current − prior | `duration_band` = 0.50 |
| scalar | `beta` (vs benchmark) | current − prior | `beta_band` = 0.10 |
| vector | `active_weights` (per bucket, pct pts) | per key: current − prior | `active_weight_band` = 2.00 |
| vector | `factors` (per factor, exposure) | per key: current − prior | `factor_band` = 0.25 |

A change is **material drift** when `abs(delta) > band` (strictly over; a delta exactly at the
band is a reported change, not an exception). A characteristic evaluable in only one snapshot
is reported `not_evaluable`, never assumed unchanged.

## Limit-proximity routing (optional `mandate_reference`)

When a mandate reference is supplied, a characteristic is flagged `route_to_compliance` if its
**current** value is at or within `route_buffer` (default 0.25) of the reference:

| Reference | Route when |
| --------- | ---------- |
| `tracking_error_max` | current TE ≥ `tracking_error_max − route_buffer` |
| `duration_band = [lo, hi]` | current duration ≤ `lo + route_buffer` **or** ≥ `hi − route_buffer` |
| `max_active_weight` | any bucket `abs(current) ≥ max_active_weight − route_buffer` |

Routing is a **hand-off trigger**, not a breach finding. The packet does not decide whether a
limit is breached — `investment-mandate-reviewer` is the authoritative limit test. If no
mandate reference is supplied, routing is disabled and the packet says so.

## Exceptions

An **exception** is any change that is material drift OR routed for limit proximity. Each
exception carries its `type` (`material_drift`, `limit_proximity`, or both), the delta, the
band, a plain-language reason, and cited evidence (current + prior `source_ref`).

## Priority mapping (deterministic, documented)

| Suggested band | Rule |
| -------------- | ---- |
| **Informational** | No exceptions (no band exceeded, nothing routed) |
| **Review** | 1–3 exceptions, none routed for limit proximity |
| **Elevated** | Any `route_to_compliance` item, OR ≥ `4` exceptions (`ESCALATE_EXCEPTION_COUNT`) |

`ESCALATE_EXCEPTION_COUNT` is a fixed constant (4), documented here and mirrored in
`scripts/validate_output.py`; it is not config-overridable and is never tuned per portfolio.
Priority is a **triage suggestion for a human analyst** — it is not a compliance
determination and it never triggers a trade or a limit change.

## Hard boundaries (fail closed)

- Never **rebalance** (direct/recommend/size/stage/execute a trade, reweight, trim, add).
- Never **set or modify a mandate limit / band / threshold**.
- Never assert a portfolio **is in breach / breaches / violates** a mandate — route it.
- Never provide **personalized investment advice**.
- Never compare **unapproved** characteristics; both snapshots must be approved.

## Version / effective-date & durable-ID rules

- `config_version` is a versioned contract recorded in the packet; bands and buffer come from
  it, never from a guess about "what's normal for this book".
- `as_of` (current) and `prior_as_of` (prior) are the effective dates; `prior_as_of` must be
  strictly before `as_of`. The window (and optional label, e.g. `MoM`, `QoQ`) is reported.
- `packet_id = pdm-{portfolio_id}-{as_of}-0001` is the durable identifier tying the output to
  its inputs; downstream skills and case records reference it. Re-running the same approved
  snapshots under the same `config_version` reproduces the result.
