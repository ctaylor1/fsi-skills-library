# Domain Rules — investment-policy-statement-builder

Orientation references: SEC/FINRA books-and-records and Reg BI Care Obligation context, CFA
Institute IPS guidance, 2026 FINRA Annual Regulatory Oversight Report. The **firm's own** approved
IPS template, allocation policy, disclosures/restrictions register, and approved tax-assumptions set
take precedence and are **versioned contracts**. Nothing here is investment advice; it defines how a
draft is assembled and screened, not what a client should hold.

## Required IPS sections (template fidelity)

Every draft must contain all of these sections. `scripts/calculate_or_transform.py` lays inputs into
them and `scripts/validate_output.py` fails closed if any is missing.

| # | Section key | Title |
| - | ----------- | ----- |
| 1 | `purpose-and-scope` | Purpose and Scope |
| 2 | `governance-and-roles` | Governance and Roles |
| 3 | `investment-objectives` | Investment Objectives |
| 4 | `risk-tolerance` | Risk Tolerance |
| 5 | `time-horizon` | Time Horizon |
| 6 | `liquidity-requirements` | Liquidity Requirements |
| 7 | `tax-considerations` | Tax Considerations |
| 8 | `constraints-and-restrictions` | Constraints and Restrictions |
| 9 | `strategic-asset-allocation` | Strategic Asset Allocation |
| 10 | `rebalancing-policy` | Rebalancing Policy |
| 11 | `benchmarks-and-monitoring` | Benchmarks and Monitoring |
| 12 | `approvals-and-effective-date` | Approvals and Effective Date |
| 13 | `disclosures` | Disclosures |

## Risk-tolerance reconciliation (deterministic)

Record all three dimensions and govern to the most conservative:

- **Ability** (financial capacity to bear loss), **Willingness** (client's stated comfort),
  **Capacity** (horizon/liquidity headroom).
- `overall = most_conservative(ability, willingness, capacity)` on the ordered scale
  `Conservative < Moderate-Conservative < Moderate < Moderate-Aggressive < Aggressive`.
- Never round overall tolerance **upward** to justify a higher-risk allocation. If willingness and
  ability conflict, record both and flag for advisor discussion — do not resolve it here.

## Strategic asset-allocation rules (deterministic)

| Rule | Requirement |
| ---- | ----------- |
| Targets sum | Sum of `target_pct` across classes = **100%** (± 0.1 tolerance). |
| Within band | For every class, `min_pct ≤ target_pct ≤ max_pct`. |
| Band order | `min_pct ≤ max_pct`. |
| Citation | Every allocation line carries a `citation` (source ref); an uncited line is an unsupported assertion. |
| Benchmark | Every allocation line names a `benchmark` for monitoring. |

A violation is a **hard error** (fail closed) — the builder never re-weights, drops a class, or
fabricates a band to make the table sum.

## Material assertions require a source (no unsupported claims)

Each of these fields is a *material assertion* and must carry a citation, or the draft is `needs-data`
and the output screen fails:

- return objective and spending need (objectives)
- risk-tolerance dimensions (risk-tolerance)
- time horizon (time-horizon)
- liquidity reserve and distribution figures (liquidity)
- tax marginal rate / approved-assumption ref (tax) — must reference the **approved** tax set
- each restriction and legal/regulatory constraint (constraints)
- every strategic-allocation line (allocation)

## Hard boundaries (fail closed)

- **No suitability / Reg BI determination.** The draft never states an allocation is "suitable,"
  "approved," or "in the client's best interest as determined" — that is `suitability-reg-bi-reviewer`
  plus a human supervisor.
- **No trading or staging.** No order, trade list, or execution language — that is
  `portfolio-rebalancing-assistant` (R4, approval-gated).
- **No delivery / filing / finalization.** Never "sent," "submitted," "filed," "delivered to the
  custodian," "final and binding," or "signed" — approvals are recorded as `pending`.
- **No guarantees or performance promises.** No "guaranteed return," "risk-free," "will outperform,"
  or "no downside."
- **No personalized advice beyond documented inputs.** The draft reflects the documented profile; it
  does not invent objectives, tax positions, or allocations the sources do not support.

## Prohibited-language screen (regex families in `validate_output.py`)

The output validator rejects, case-insensitive:

1. **Approval/decision-as-done:** `suitability approved`, `recommendation approved`, `deemed
   suitable`, `we hereby approve`, `is approved for the client`, `best-interest determination made`.
2. **Trade/execution:** `execute the trade`, `trade(s)? executed`, `order placed`, `place the order`,
   `rebalance executed`, `sent to the custodian`.
3. **Filing/delivery/finalization:** `file the`, `submitted to`, `final and binding`, `delivered to
   the client`, `signed and executed`.
4. **Guarantee/performance:** `guaranteed return`, `guarantee[ds]? to`, `risk-free`, `will
   outperform`, `no downside`.

Any match is a hard error. These screens are deliberate belt-and-suspenders on top of the structural
draft-status and approval checks.
