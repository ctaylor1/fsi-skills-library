# Domain Rules — investment-committee-memo-builder

## Supplied-input validation boundary

The bundled scripts operate on supplied JSON. Connector access, source extraction, authenticated approvals and external delivery are not implemented by these scripts. Retain the original input separately and run `python -B scripts/validate_output.py output.json --input input.json` (alias `--source`). Output includes `input_hash` and `source_truth: unverified`; validation reconstructs the native result and rejects changed figures, narrative, classifications, omitted fields and extra fields. A successful check proves correspondence with the supplied input, not source truth, legal applicability or permission to distribute. Never add a raw source snapshot to an outward-facing artifact. Source and approval strings remain supplied evidence for professional review.

This remains a supplied-model private-deal memo. Base, upside and downside are all required. Sector limits are hard by default; only an explicitly discretionary sector_limit_type permits a warning. equity_value_proxy means EV minus net debt, not sponsor funding or a sources-and-uses equity check. The supplied model itself is in the source-reference ledger. No new public-security or institutional-allocation model is implemented.


Orientation: standard private-markets IC practice (thesis, structure, valuation, returns,
scenarios, risks/mitigants, sizing, decision questions). The firm's **IC memo template** and
**concentration-limit config** are versioned contracts and take precedence over these
defaults. All figures are illustrative ($mm unless noted); tolerances are configurable.

## Model tie-outs (deterministic — `scripts/calculate_or_transform.py`)

The memo must reconcile to the model source within tolerance `TOL = 0.05`:

| Tie-out | Identity checked |
| ------- | ---------------- |
| `entry_multiple` | `entry_ev / metric_value` == stated entry multiple |
| `equity_value_proxy` | `entry_ev - net_debt` == stated equity-value proxy (not sponsor funding) |
| `leverage_x` | `total_debt / ebitda` == stated leverage |

A mismatch beyond tolerance is a **block** (`tie-out-break`): the memo may not restate a
figure the model does not support.

## Scenario consistency (mandatory downside)

- A **Downside** case is mandatory. A Base and an Upside are expected. Missing downside is a
  **block** (`missing-downside`) — a memo without a modeled downside is incomplete.
- MOIC and IRR must be ordered **downside ≤ base ≤ upside**; a violation is a **block**
  (`scenario-ordering`).
- The **base** case MOIC/IRR must tie to the model returns (MOIC within `0.05`, IRR within
  `0.5` pts); otherwise a **block** (`base-scenario-mismatch`).

## Position sizing & concentration

- `computed_position_pct = proposed_commitment / fund_nav × 100`, checked against the stated
  figure (tolerance `0.1`).
- `computed_position_pct > single_name_limit_pct` → **block** (`single-name-breach`).
- `sector_current_pct + computed_position_pct > sector_limit_pct` → **block** by default. Only `sector_limit_type: discretionary` changes this to a disclosed warning. Committee review does not waive a binding mandate limit.

## Valuation guardrail

- Entry multiple **above** the peer range → **warn** (`valuation-above-peers`): disclose and
  justify; do not bury it.

## Traceability (no unsupported/unapproved claims)

Every thesis point, risk, scenario, valuation basis, and sizing input must cite a `source_id`
present in `sources[]`:

- Unknown `source_id` → **block** (`unsupported-claim`).
- A `market` or `research` source not marked **approved** → **block** (`unapproved-source`).

## Hard boundaries (fail closed)

- **Draft only.** Never send, circulate, email, submit, or mark a memo final.
- **No decision.** `committee_decision` is always left `pending`; the skill never records or
  makes the investment decision or the committee vote.
- **No fabrication.** Never invent a figure, comp, or claim not present in an approved input.
- **No personalized investment advice** and no guarantee/"can't-lose"/"risk-free" language.
- **No omission of known risks or the downside** to strengthen the case.

## Required approvals before circulation

`preparer` (deal-team lead) and `reviewer` (independent desk / compliance) sign-offs must be
**recorded** (by humans) before the draft may be circulated. The committee decision is
recorded in committee, never by this skill.

## Decision-question completeness

The memo must end with explicit questions the committee must decide (commitment amount,
conditions precedent, leverage, waivers). An empty decision-question set is a data gap.
