# Domain Rules — fpa-variance-analyzer

Explainable variance **findings** and how they map to a **commentary review priority**.
Materiality thresholds, run-rate escalation, and driver tie-out tolerance are configuration
(versioned, owned by the FP&A/controllership team), not hard-coded judgments, and are never
tuned to make a specific line look material or immaterial. The firm's FP&A standard and
materiality policy take precedence over any default here.

## Variance basis

For each line the skill computes three variances from the posted actual:

| Variance | Formula | Purpose |
| -------- | ------- | ------- |
| `vs_budget` | actual − budget | Primary managed variance (default materiality basis) |
| `vs_forecast` | actual − forecast | Execution against the latest expectation |
| `vs_prior` | actual − prior period | Trend / run-rate context |

The **materiality screen and driver tie-out run on the `basis`** (default `budget`); the
other two are reported for context. Configure `basis` to `forecast` or `prior` per engagement.

## Favorable / unfavorable (sign convention)

Direction is not the sign of the number — it depends on account type:

| Account type | Favorable when | Unfavorable when |
| ------------ | -------------- | ---------------- |
| `revenue` (income) | actual > base (variance > 0) | actual < base |
| `expense` (cost)   | actual < base (variance < 0) | actual > base |

Mislabeling an over-budget cost as "favorable" because the raw number is positive is the
classic FP&A error; the skill sets `favorable` from account type, never from the raw sign.

## Materiality screen (deterministic)

A line is **material** if either test passes:

| Test | Fires when (default config) |
| ---- | --------------------------- |
| Absolute | `abs(variance) >= abs_threshold` (default 100,000) |
| Percent | `abs(base) >= min_base` (default 50,000) **and** `abs(variance/base) >= pct_threshold` (default 10%) |

The `min_base` floor prevents a tiny base from making a trivial variance look material by
percentage. Only material lines receive evidence, attribution, run-rate, and commentary.

## Driver attribution tie-out

If a line supplies a driver decomposition, the skill checks it **ties out** to the computed
variance:

| `attribution_status` | Meaning |
| -------------------- | ------- |
| `ok` | `abs(variance − sum(drivers)) <= attribution_tolerance` (default 1.0) |
| `fail` | Drivers supplied but do not reconcile to the variance (internally inconsistent) |
| `unattributed` | No driver decomposition supplied |

The skill never fabricates drivers to force a tie-out. `fail` and `unattributed` mean the
material variance is **not yet explained** and needs a human.

## Run-rate impact

For a **recurring** material line, `run_rate_impact = variance × periods_remaining`
(`periods_remaining` from config). One-time and timing items get `0`. Every non-zero run-rate
figure is flagged `run_rate_is_estimate: true` — it is an estimate for context, **not** a
reforecast or a committed guidance number.

## Commentary priority mapping (deterministic, documented)

| Suggested band | Rule |
| -------------- | ---- |
| **Routine** | 0 material variances |
| **Standard** | 1–2 material variances, all explained (tie-out `ok`), no run-rate escalation |
| **Elevated** | ≥ 3 material variances, OR any unexplained material variance (`fail`/`unattributed`), OR any recurring run-rate impact ≥ `run_rate_escalation` (default 250,000) |

Priority is a **triage suggestion for a human reviewer** — it prioritizes which commentary a
finance business partner reviews first. It is not a management decision and it never commits
a number or triggers an action.

## Hard boundaries (fail closed)

- Never make or imply a **management decision** (cut/add headcount, defund/approve a program,
  freeze hiring or the budget) — describe the variance and attribute the decision to management.
- Never **commit a forecast or guidance** number, reforecast as the official number, or state
  the company "will hit/deliver" a figure — that is an approved company communication.
- Never **restate** actuals, **post/book a journal or adjustment**, or otherwise change the
  system of record — route posting/reconciliation to the appropriate skill and human.
- Never provide **personalized investment, tax, or legal advice**.
- Never tune materiality/attribution config to a specific line to change whether it is flagged.

## Alternative-explanation prompts (always include when a finding is material)

Timing/phasing that reverses next period; reclassifications or account-mapping changes between
actual and plan; accrual true-ups; FX retranslation; allocation or cost-center reorganizations;
one-time items mixed into a run-rate line. The pack must invite the reviewer to weigh these
before drawing a conclusion.
