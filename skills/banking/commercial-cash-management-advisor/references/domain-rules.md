# Domain Rules — commercial-cash-management-advisor

Explainable treasury-service **fit rules** and how the recommended set maps to an
**engagement-priority band**. Thresholds are configuration (versioned, owned by the TM
product team), not hard-coded judgments, and never tuned to make a given client "qualify".
The firm's TM product standard and product terms take precedence over this orientation
reference.

## Service-fit taxonomy

| Service | Category | Fits when (default config) | Evidence attached |
| ------- | -------- | -------------------------- | ----------------- |
| `excess_balance_investment` | liquidity | Estimated idle collected balance (total collected − operating buffer) ≥ `idle_balance_min` (250,000) | Account balances + idle calc |
| `liquidity_structure` | liquidity | Accounts ≥ `multi_account_min` (3) AND idle balance > 0 (ZBA / target-balance sweep / pooling) | Account group |
| `lockbox_receivables` | receivables | Mailed check receipts/month ≥ `lockbox_min` (200) | Activity metric |
| `remote_deposit_capture` | receivables | Checks deposited/month ≥ `rdc_min` (50) | Activity metric |
| `merchant_services` | receivables | Card acceptance/month ≥ `merchant_services_min` (50,000) | Activity metric |
| `controlled_disbursement_payables` | payables | Checks issued/month ≥ `controlled_disbursement_min` (150) | Activity metric |
| `check_positive_pay` | fraud_control | Checks issued/month ≥ `check_positive_pay_min` (50) | Activity metric |
| `ach_debit_block` | fraud_control | ACH debits received/month ≥ `ach_debit_block_min` (25) | Activity metric |
| `fx_international_services` | international | Cross-border/month ≥ `fx_services_min` (100,000) | Activity metric + currencies |
| `overdraft_liquidity_referral` | referral | Overdraft days in period ≥ `overdraft_referral_days` (3) — **refer to lending**, not a credit opinion | Activity metric |

Rules are **additive and independent**; the output reports each recommended service with its
own evidence and implementation questions. A service already in CRM `existing_services` is
reported as `already_in_place`, never re-recommended. There is no opaque composite "score".

## Engagement-priority mapping (deterministic, documented)

| Suggested band | Rule |
| -------------- | ---- |
| **Informational** | 0 services recommended |
| **Recommended-review** | 1–2 services recommended, none an escalator |
| **Priority-review** | ≥ 3 services recommended, OR any of `check_positive_pay` / `ach_debit_block` / `overdraft_liquidity_referral` recommended |

The escalators are a **fraud-control gap** (unprotected check/ACH exposure) or a
**credit/liquidity referral**, each of which warrants a priority conversation regardless of
how many other services fit. Priority is a **triage suggestion for the banker**. It is not a
decision to sell, a price, a credit opinion, or investment advice.

## Hard boundaries (fail closed)

- Never make or imply a **binding product/pricing decision** (rate, ECR, fee, "final
  pricing", "locked-in", signed proposal).
- Never make or imply a **credit decision** or assess creditworthiness; the overdraft
  referral routes to commercial lending and a human underwriter.
- Never give **personalized investment advice** (a specific security, an asserted
  return/yield); route sweep/investment suitability to a licensed specialist.
- Never **open, enroll, change, close, or price** a service (system-of-record action).
- Never **guarantee** savings/return/outcome or **tune thresholds to the individual**.

## Implementation questions (always include per recommended service)

Each recommended service carries the concrete questions the banker should bring to the client
(e.g., lockbox: peak-day receipt volume, remittance fields for AR posting, wholesale vs.
retail configuration). These questions are the discussion deliverable — the skill surfaces
what must be confirmed with the client, not a commitment.
