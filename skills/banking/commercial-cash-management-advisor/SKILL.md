---
name: commercial-cash-management-advisor
description: >-
  Analyze a commercial customer's operating cash flows and account balances and produce
  source-linked, explainable treasury-management recommendations — receivables, payables,
  liquidity structures (ZBA/sweep/pooling, earnings credit), fraud controls (Positive Pay,
  ACH debit block), and international/FX — each with a rationale, cited evidence, and the
  implementation questions the banker should bring to the client. Use when a treasury-
  management officer or commercial banker asks "which cash management services fit this
  client", "how should we structure their liquidity", "prepare a treasury review", or wants
  a discussion-ready service-fit analysis from a cash profile. This skill RECOMMENDS
  candidate services and poses questions only; it NEVER makes a binding product, pricing,
  credit, or investment decision, never approves a line/overdraft or commits rates, never
  gives personalized investment advice, and never opens, changes, or prices an account or
  service — those are human/authorized-system actions.
license: MIT
compatibility: Amazon Quick Desktop; requires core-banking, CRM, document-intelligence, loan-origination/servicing, product-terms, and approved-calculation MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Banking"
  aws-fsi-skill-type: "Guidance or domain-expertise skills"
  aws-fsi-risk-tier: "R2"
  aws-fsi-archetype: "Domain workflow"
  aws-fsi-agent-pattern: "Interactive decision-support copilot"
  aws-fsi-delivery-wave: "Wave 2 - analytical production"
  aws-fsi-action-mode: "Read-only analysis"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "external-delivery"
  aws-fsi-data-classification: "Highly Confidential (customer NPI/PII)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Banking product & credit operations"
  aws-fsi-primary-user: "Treasury-management officer / commercial banker"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Commercial Cash Management Advisor

## Purpose and outcome
Given a commercial customer's operating cash flows and account balances, run a multi-step
treasury review that produces **explainable, source-linked service recommendations**: for
each candidate treasury-management service, whether it fits, the rationale, the cited
evidence behind it, and the **implementation questions** the banker should raise with the
client. A successful output is a discussion-ready service-fit analysis that a
treasury-management officer takes into a client conversation — the product, pricing, credit,
and investment decisions all remain human and are handled by the responsible desk.

## Use when
- "Which cash management services fit this client?"
- "How should we structure their liquidity / concentrate their balances?"
- "Prepare a treasury-management review from these statements/analytics."
- "What should I bring to the treasury conversation with this commercial customer?"
- A banker wants a consistent, cited service-fit write-up (receivables, payables, liquidity,
  fraud controls, international) to attach to a relationship review.

## Do not use
- The user wants a **binding product or pricing decision**, a **rate/ECR commitment**, or a
  signed proposal → out of scope. This skill recommends and questions; pricing sits with the
  product/pricing desk under human review.
- The user wants a **credit decision** — approve/decline a working-capital line, overdraft
  facility, or loan → out of scope; this skill does not assess creditworthiness. Route the
  liquidity/credit **referral** to commercial lending (see handoffs) and a human underwriter.
- The user wants **personalized investment advice** (e.g., "should they buy this fund")
  → out of scope; route sweep/investment suitability to a **licensed investment specialist**.
- The user wants to **open, enroll, change, or price** a service → that is a
  system-of-record action for treasury operations, not this skill.
- The input is raw statements needing extraction first → `bank-statement-analyzer`; a forward
  cash-flow projection → `cashflow-forecaster`; an existing-fee analysis →
  `fee-and-charge-reviewer`.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill emits a service-fit advisory
with a durable `advisory_id`; upstream analysis skills feed it and downstream product,
lending, compliance, and licensed-specialist steps consume it. It must not duplicate their
pricing, credit, investment, or enrollment steps.

## Inputs and prerequisites
- **Customer identifier** and a **cash profile**: the account group (each with type and
  average collected/ledger balance) and the **operating activity** for the analysis period
  (checks issued/deposited, mailed receipts, ACH debits/credits, wires, card acceptance,
  cross-border volume, overdraft days). Schema:
  [scripts/validate_input.py](scripts/validate_input.py).
- The client's intended **operating buffer** (minimum liquidity to keep) where known; if
  absent, idle balance is an upper-bound estimate flagged low-confidence.
- Read access to core-banking, CRM (existing services), and the **versioned threshold
  config** (see [references/domain-rules.md](references/domain-rules.md)).

## Source hierarchy
See [references/source-map.md](references/source-map.md). Core-banking balances and activity
analytics are the position of record; CRM supplies existing services and relationship
context; product terms define what each service requires; the versioned config supplies the
fit thresholds. Cite every recommendation's evidence to a source row.

## Workflow
1. **Scope & load** — confirm the customer and analysis period; load the account group and
   activity; validate with `validate_input`. Note existing services so the skill does not
   re-recommend what the client already has.
2. **Compute service fit (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py) to evaluate each
   service against the versioned thresholds (idle-balance/liquidity, receivables, payables,
   fraud controls, international, and a credit/liquidity **referral**). Each recommended
   service returns a rationale, the evidence rows behind it, the basis/thresholds, and the
   implementation questions. Fit is **explainable**, not a black-box score.
3. **Assemble the advisory** — for each recommended service attach evidence + citations;
   record `not_indicated` services with the reason and `already_in_place` services.
4. **Suggest engagement priority** — map the recommended-service profile to a priority band
   (Informational / Recommended-review / Priority-review) per the documented, deterministic
   mapping. This is a triage suggestion for a human, explicitly **not** a decision to sell.
5. **Write the pack** — plain-language rationale per service + evidence + implementation
   questions + assumptions/caveats, and route pricing/credit/investment/enrollment to the
   responsible human desk.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py)
after. The output check confirms: every recommended service has evidence + citation and at
least one implementation question, the priority maps deterministically from the recommended
set, no binding-decision/advice language is present, and the standing disclaimer is included.
Fail closed on any miss.

## Human approval
`external-delivery`: human review is required before the advisory is delivered to the client
or written to CRM/a system of record. No approval is needed for the banker's own read. The
skill never opens, prices, enrolls, or commits anything, and never decides credit or
investment suitability.

## Failure handling
- **Thin/missing balances or activity** → compute only the services the data supports; label
  the rest `not_indicated` or "not evaluable"; do not overstate fit.
- **No operating buffer** → idle balance is an upper-bound estimate; flag low-confidence and
  do not lean recommendations on it alone.
- **Ambiguous customer/entity** → stop and confirm; never analyze the wrong relationship.
- **Stale/conflicting sources** (balance vs. CRM note) → cite both; do not resolve silently.
- **Tool timeout** → return the services computed so far with a clear "incomplete" flag.

## Output contract
1. **Summary** — customer (masked), period, estimated idle balance, count of recommended
   services, suggested engagement priority.
2. **Recommendations** — per recommended service: name, category, plain-language rationale,
   basis/thresholds, cited evidence rows, and implementation questions.
3. **Not indicated / already in place** — services that did not fit (with the reason) and
   services the client already has.
4. **Assumptions & caveats** — period-average basis, config version, and the explicit routing
   of pricing/credit/investment/enrollment to the responsible human desk.
5. **Machine-readable** — recommendations + evidence + `advisory_id` for downstream steps.
6. **Standing disclaimer** — "Advisory analysis only; not a binding product, pricing, credit,
   or investment decision. No account or service has been opened, changed, or priced."
See [references/controls.md](references/controls.md).

## Privacy and records
Customer NPI/PII. Mask account numbers to last 4. Minimize customer data in the output to
what evidences a recommendation. Retain the advisory + citations + config version per records
policy; log the read and any external-delivery approval. Never exfiltrate customer data.

## Gotchas
- **A fit is not a sale, a price, or an approval.** A recommended service is a conversation
  starting point; pricing, credit approval, and investment suitability are separate human
  decisions and must never be asserted here.
- **The credit/liquidity referral is not a credit opinion.** Recurring overdrafts route to
  commercial lending; this skill never states or implies the client is (or is not)
  creditworthy or "approved".
- **Excess-balance ≠ investment advice.** Recommending an earnings-credit or sweep discussion
  is fine; recommending a specific security or asserting a return is not — route suitability
  to a licensed specialist.
- **Don't re-recommend existing services.** Check CRM `existing_services`; a service the
  client already has is `already_in_place`, not a recommendation.
- **Thresholds are config, not intuition.** Fit thresholds come from the versioned config and
  are never tuned to make a given client "qualify".
- **Volumes are period averages.** Validate current figures with the client before any
  proposal; seasonality can distort a single period.
