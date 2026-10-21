# Asset Management Phase 2 — foundational business coverage

Implemented on September 21, 2026 under the user's Phase 2 authorization. The category
now contains **54 packages**, with **29 new foundations** and **three expanded packages**.
The AM integration checkpoint catalog contains **331 packages across 15 categories**. The approved 64-capability
AM roadmap retains ten planned capabilities in Phases 3 and 4.

## Delivered workflows

| Family | Delivered foundation |
| --- | --- |
| Manager and client business | AUM/fee/profit economics; product lifecycle gates and payback; distribution eligibility, fees and conflicts; service cadence/SLA; investor reporting. Institutional RFP extends the existing proposal package. |
| Investment research and decisions | Systematic study leakage/cost controls; private-deal diligence, monitoring and private credit; institutional manager diligence; public-security, manager and allocation committee modes. Neutral security research retains its existing Investment Research owner. |
| Institutional portfolios | Institutional policy; asset-class and security candidate feasibility; long-only lot-rounded rebalancing; selected US equity tax-lot review; buy-side trade-intent participation and evidence review. |
| Performance and fund operations | Linked-subperiod TWR, Modified Dietz and bounded conventional XIRR; private-fund multiples; journal/trial-balance, accrual and supplied NAV workpapers; asset servicing, investor operations and provider oversight. |
| ETF/index and private capital | Tracking/weight controls; ETF basket/cash and secondary-market checks; capital activity, commitment pacing and explicit whole-fund waterfall tiers; institutional solution fit against dated liabilities and governance. |
| Governance | Applicability of supplied reviewed rules; approved exact-source claims, disclosures and paired performance presentation checks. |

The exact identifiers and scope live in the [Phase 2 manifest](../../catalog/asset-management-phase2-capabilities.json)
and [support matrix](SUPPORT-MATRIX.md). Each package contains its native schema, method
rules, primary-source map, review limits, handoffs, output template and executable evaluations.
Default proposal, household manager diligence and private-deal committee interfaces remain
available. New institutional and committee jobs require explicit documented modes.

## Shared implementation and handoffs

Canonical reusable resources are versioned in `shared/asset-management` and
`shared/investment-analytics`. Generated package-local copies are pinned by version,
SHA-256 and license; isolated installations do not depend on sibling-relative imports.
The expanded build covers **83 affected portable packages**, including prior migrations.
No professional research workflow is copied into AM or a shared-resource bundle.

The new foundation contract binds native object, currency, economic date, knowledge
cutoff, audience, source metadata and method to the detached original input. The common
artifact wrapper preserves those fields and fixes mixed units to `native-schema`.
Actual producer and receiver validators run at handoff time. Recomputed hashes cannot
replace source reconstruction, and additional receiver fields require explicit sourced
mappings. A real rebalance-to-trading review copies an unchanged draft quantity, adds
separately supplied market/control evidence, retains open issues and calculates the
receiver's participation/cost review without creating an order. Exact artifacts are
retained in [validation evidence](phase2-validation/README.md).

The router now covers **46 declared intents** with explicit mode selection, subject
checks, installation status and future capability gaps. It plans workflows; it does not
install or launch packages. All **40 new or expanded native modes** are exercised through
the actual common-wrapper/native-validator integration.

## Method and evidence limits

Local calculations are transparent, bounded challenge methods. Portfolio construction
checks supplied candidates and can bind a supplied optimizer result to the current
model; it does not optimize or assert optimality. Production accounting/NAV strike,
complex pricing/risk, legal interpretation, full tax treatment, nonconventional IRR,
PME and unsupported waterfall features require separately accepted engines or specialist
work. The [engine contract](../../shared/investment-analytics/engine-contract.md) makes
these dependencies explicit; no live vendor connector is implied.

Numerical facts are supplied observations or assumptions with required provenance links.
Narrative business claims require exact source support and declared audience/approval
scope. Restricted content is withheld or rejected. Hashes, reviewer names, rights fields
and approval references remain supplied assertions. Technical checks do not establish
source truth, professional acceptance, live permissions or production readiness.

## Validation and preserved work

[The validation record](phase2-validation/README.md) reports final checks separately from
independent authoring and review checkpoints. Fresh forward reviews exposed evidence,
precision and unresolved-completion defects; the original failures and repaired replays
are retained. Tests include independently expected arithmetic, stale/future knowledge,
audience exclusion, missing provenance, tampered results, changed original inputs,
unknown scope, unsupported engine methods and source-bound receiver validation.

Final AM verification passed 443 native evaluations and 563 isolated checks across 83 packages,
with zero AM structure errors/warnings. Whole-library validation remains affected by
concurrent compliance work: the final repository-test snapshot has three inventory
failures, and the separate library-eval snapshot has13 compliance failures. These do not
establish an AM regression or a clean whole-library release.

Prior Phase 1 validation artifacts and unrelated Insurance, Payments and Wealth files
were checked against pre-Phase-2 hashes. Existing working-tree changes remain intact.
This implementation does not commit, merge, push, release, publish or perform institutional
actions. Phases 3 and 4 remain outside this authorization.
