---
name: private-market-client-reviewer
description: >-
  Review a household’s private-fund positions, commitments, capital calls, distributions, eligibility evidence and dated funding needs. Reconcile settled movements with notices and forecast calls, retain unknown NAV and unresolved issues, and prepare advisor and specialist questions. Consumes shared manager diligence; makes no investment or eligibility decision and takes no account action.
license: MIT
compatibility: Amazon Quick Desktop; requires approved read-only client, custodian, fund-administrator, document and policy integrations. Bundled Python uses supplied JSON only, with no live connectors or network access.
metadata:
  aws-fsi-category: "Wealth Management"
  aws-fsi-skill-type: "Analysis and evaluation skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Analyze & review"
  aws-fsi-agent-pattern: "Interactive decision-support copilot"
  aws-fsi-delivery-wave: "Wave 8 - wealth management P2"
  aws-fsi-action-mode: "Draft-only; no system-of-record change"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Highly Confidential (customer NPI/PII)"
  aws-fsi-jurisdictions: "US (default); approved additional jurisdiction packs required before use"
  aws-fsi-owner: "Wealth Management private-investment oversight"
  aws-fsi-primary-user: "Wealth advisor / private-market investment specialist / client operations reviewer"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-09-17"
---

# Private Market Client Reviewer

## Purpose and outcome
Prepare a client-level view of private-fund commitments, cash movements, unpaid notices,
forecast calls and account funding needs. Reconcile actual capital activity and identify
questions for the advisor, fund administrator and legal eligibility reviewer. The output
supports a professional review of existing positions; it does not select an investment.

## Use when
- Review several private-fund holdings before an advisor meeting or a capital-call deadline.
- Explain remaining commitment, called-but-unpaid amounts, recallable distributions and dated cash needs.
- Identify stale NAV, incomplete legal eligibility evidence or an unresolved manager-diligence issue.

## Do not use
- Manager selection, investment underwriting, performance calculation or fund operational diligence.
- Subscription, redemption, transfer, payment, trading or an investment recommendation.
- Deciding legal investor eligibility, interpreting enforceability, or inferring permitted investor status from wealth.
- Non-USD portfolios, secondary transfers, noncash/deemed contributions, fund-level waterfalls,
  facility financing, netted notices or commitment adjustments without a professionally reconciled operative total.

## Adjacent-skill handoffs
Use [references/handoffs.md](references/handoffs.md). Consume investment-manager-due-diligence-reviewer
artifacts and preserve their substantive unresolved findings in `upstream_issues`. Send the
client cash schedule to household-financial-planning-assistant or the applicable liquidity workflow;
send legal or ownership conflicts to the assigned specialist. Carry request, household, artifact,
source and capacity context. Do not repeat shared manager research or treat its status as approval.

## Inputs and prerequisites
Read the exact [references/schema.md](references/schema.md) before extracting records. The
request requires a current supplied review policy, source registry, explicit coverage assertions,
upstream issues, accounts, positions, all notices and settled movements since inception, active
or superseded call forecasts, and other account obligations. Use current settled available cash;
historical payments are already reflected in that cash. Every material record needs citations.

The operative commitment includes documented amendments; identify its basis explicitly. A
professional must map source amounts to this package’s defined commitment balance before
comparing an administrator’s differently defined “unfunded” figure. Unknown facts remain null.

## Source hierarchy
Current governing agreements and notices establish the supplied contractual allocation;
administrator/custodian records establish posted movements, balances and dated NAV; the
applicable legal/policy profile establishes required eligibility evidence. The advisor supplies
attributed incremental forecasts and household obligations. Preserve conflicts and source dates.
See [references/source-map.md](references/source-map.md) for primary orientation sources.

## Workflow
1. Triage whether this is a client holdings/funding review. Route manager diligence, legal
   determination and requested transactions to their responsible workflow; do not execute them.
2. Confirm current household, account/fund ownership, capacity, USD scope, policy version and
   horizon. Obtain complete inventories or explicitly mark incomplete coverage. Reconcile each
   original notice with its payment/receipt records, rather than copying cumulative totals twice.
3. Extract gross cash amounts and supported commitment effects separately. Read
   [references/domain-rules.md](references/domain-rules.md) for recallability, lifecycle and funding conventions.
   Supersede a forecast when its corresponding call becomes a notice; retain the link.
4. Run `python -B scripts/validate_input.py REQUEST.json`; malformed, stale or inconsistent
   lifecycle inputs must be repaired from sources before calculation.
5. Run `python -B scripts/calculate_or_transform.py REQUEST.json`. Review position balances,
   fund summaries, dated account budgets, unknowns and specialist questions. Unsettled
   distributions do not replenish cash; household aggregation does not authorize a transfer.
6. Run `python -B scripts/validate_output.py OUTPUT.json`. It reconstructs the entire output,
   including economic values, input identity, issues and no-action status.
7. Present the draft using [assets/output-template.md](assets/output-template.md). A professional
   checks factual extraction, contractual definitions and the sufficiency of the supplied evidence.

## Validation loop
The CLI reads one JSON path or `--selftest`. [evals/evals.json](evals/evals.json) separates
executable contract/arithmetic tests from proposed model routing and safety evaluations.
A valid `needs-data` report retains useful known subtotals without declaring missing totals known.
`review-ready` means the configured supplied-data review is ready for a human; it does not mean
eligible, suitable, independently verified, approved or funded.

## Human approval
All outputs remain draft-only, `human_review_required: true`, `action_taken: false`, and
`delivery_status: not-delivered`. The package does not authenticate a named reviewer, source,
policy, artifact or permission. Human adjudication and any separately authorized operation occur
outside this skill. See [references/controls.md](references/controls.md).

## Failure handling
Reject malformed structures, stale registry records, unsupported scope, impossible dates,
duplicate IDs, mismatched classifications and lifecycle/settlement contradictions. Preserve
valid missing data, stale domain NAV, financial discrepancies and unresolved concerns as
findings; do not fabricate balances, legal criteria, documents or approval. Source access failure
requires the missing approved source, not a guessed replacement or repeated live operation.

## Output contract
The common evidence envelope binds the full input snapshot. Results contain the full position
records, notice/movement ledger, commitments, account/fund summaries, policy-dated NAV review,
legal eligibility evidence inventory, manager-diligence references and specialist questions.
The two cash schedules show known obligations and the incremental forecast scenario. Exact
source records and upstream issue identities survive in the result and handoff context.

## Privacy and records
Use opaque client/account IDs and masked names. Local scripts read supplied files and print JSON;
they do not configure production access, retention or data collection. Store only the minimum
approved snapshot/report under the firm’s privacy and records controls. Do not send documents,
contact administrators or deliver this draft externally without separate authorization.

## Gotchas
- Remaining commitment includes unpaid inside-commitment calls; adding those calls again double counts them.
- Only the settled recallable component restores remaining commitment in this ledger convention.
- A fund’s outside-commitment classification and a household’s external cash-flow boundary are different facts.
- NAV dates are preserved; current NAV is never inferred by adding cash movements to an old valuation.
- Supplied legal criteria and documentary labels cannot prove eligibility or substantive source truth.
- SME/legal acceptance, source extraction, real-model evaluations and controlled integrations remain release gates.
