# Insurance Phase 5 — bounded specialist extensions

Implemented 2026-10-04 following the user request to implement the next phase.
Five explicitly planned specialist jobs now have installable packages, native
methods, source profiles, routing and tests. Insurance grows from 64 to **69**
packages. This completes the bounded Phase 5 authoring scope; it does not establish
comprehensive health-payer capability or additional adopted regional rule sets.

## Recurring jobs and accountable owners

| Package / router intent | Trigger and owner | Native work product and limit |
| --- | --- | --- |
| `parametric-trigger-reviewer` / `parametric-trigger` | Contract-defined event; parametric claims specialist | Final/revised index evidence, exact contract tiers, event cap and aggregate paid ledger; conditional unpaid scenario, no coverage or payment decision |
| `health-plan-pricing-reviewer` / `health-plan-pricing` | Cohort renewal/experience review; health pricing actuary | Aligned incurred experience/member months, explicit cumulative trends, adjustments and expenses; conditional PMPM and comparison, no selected/filed premium or statutory MLR |
| `health-utilization-review-packager` / `health-utilization` | Utilization/prior-authorization request; payer clinical review team | Source-attributed criterion/observation matrix and separately supplied administrative clock; no medical-necessity or benefit decision |
| `health-claim-payment-reviewer` / `health-claim-payment` | Coded claim/payment discrepancy; payer payment-integrity analyst | Original/replacement/void chain, exact coding profile, contract allowance, independent benefit allocation and net-paid reconciliation; no adjudication or payment |
| `health-provider-network-reviewer` / `health-provider-network` | Provider inventory/access review; network and credentialing owners | Contract, credential and directory exceptions plus complete-population access comparisons; no NPI-to-licensure inference or network certification/change |

Each job has a distinct trigger, evidence contract, owner and useful draft. Actual
institutions must establish recurring demand, source access, responsibility and
acceptance before deployment. No hypothetical market expansion warrants a duplicate
package. Existing member appeals, P&C reserving/rate adequacy, life underwriting,
CAT monitoring and individual health/disability/LTC/annuity underwriting retain their
separate roles and remaining gaps.

## Implementation

The five packages follow the repository structure: instructions, controls, source
map, exact native schema, handoffs, a practitioner template, native calculations,
input/output validators, synthetic fixtures and executable regression cases. Each
installs independently with its dependencies bundled locally.

The new `shared/insurance-specialist` support requires explicit market, program,
product, jurisdiction, method, dates, rule basis and owner. It adds no legal,
clinical, coding or regulatory defaults. Commercial, self-funded, Medicare
Advantage, Medicaid and other program scope must come from reviewed actual sources.
The public sources in [PRIMARY-SOURCES.md](phase5-validation/PRIMARY-SOURCES.md)
inform these boundaries; they are not production rule profiles.

All floating-point numeric tokens are rejected: parsing can round a fractional
source token into an apparently whole float. JSON integer tokens and exact decimal
strings remain supported. Parametric/payment/utilization operations reject bounded
precision overflow or rounding. Pricing uses exact rational intermediates and
explicitly displays recurring ratios to 50 significant digits. Network fractions
use exact comparisons against supplied thresholds, without sampling extrapolation.

Source completeness requires explicit evidence. Duplicate economic events,
conflicting revisions, unavailable inventories, unrelated scope and unresolved
upstream issues withhold dependent results. Recorded facts can remain visible when
only another dependency is missing; their provenance and uncertainty remain explicit.
The common evidence envelope retains original input and recomputes outputs, including
rejection of altered outputs even if hashes are regenerated. Hashes do not authenticate
sources, reviewers or permissions.

Router registry 5.0.0 requires participant and line for these five intents, checks
optional installed inventory and rejects action requests. Actual native input is
validated at handoff. Integration tests map utilization request provider/service
details into payment review while independently supplying claim, code, contract
and benefit evidence. Clinical evidence never becomes payment authorization.

Earlier Insurance runtime helpers and validation archives remain unchanged. The
Phase 3/4 tests now check the remaining individual-underwriting gaps rather than
requiring the five newly implemented jobs to stay absent. Catalog additions and
router overrides persist through catalog regeneration; the external workbook still
needs reconciliation. Concurrent Wealth, Asset Management and Financial Crime work
was preserved, not attributed to this phase.

## Verification and remaining acceptance

See the [validation record](phase5-validation/README.md) for command logs, independent
source-mapping attempts, retained findings, repairs and final replays. Software and
synthetic agent checks establish bounded behavior only. Real sources, licensed code
or clinical content, applicable methods, qualified practitioner/control-owner review,
privacy/access, operational recovery and deployment acceptance remain open. There
are no live connectors, external communications, filings, claim payments or system
changes. No commit, merge, release or deployment was performed.
