# Phase 2 implementation — Investment Research

Implemented 2026-10-20: analytical expansion, model-reviewer parity and reviewed
native adapters. This delivers bounded supplied-evidence methods, not professional
or institutional acceptance. [Validation evidence](phase2-validation/README.md)
records the actual checks and their limits.

## Portfolio and ownership

The phase creates 16 analytical packages and expands 16 existing packages. With
the router and dossier, 34 of the 42 target capabilities are installed. The eight
Phase 3/4 capabilities remain planned. The library contains 387 packages; IR has
34 packages. The shared financials normalizer and generic document comparator
retain their Finance & Operations and Data, AI & Model Governance owners.

| New methods | Implemented analytical scope |
|---|---|
| research-coverage-planner | Evidence questions, coverage requirements, critical dependencies and explicit gaps. |
| research-universe-screener | Reproducible filters with identity, missing/stale observations and exclusion registers. |
| company-business-model-analyzer | Revenue drivers, unit economics, concentration and supplied business-model evidence. |
| financial-statement-analyzer | Comparative statements, financial ratios, trends and cash conversion with period/basis controls. |
| earnings-quality-analyzer | Accruals, cash realization, nonrecurring adjustments and reported/normalized distinctions. |
| research-financial-model-reviewer | Independent arithmetic graph recomputation, reconciliations, assumptions and configured economic/funding checks; legacy continuity mode. |
| dividend-residual-income-modeler | Annual indexed dividend discount or clean-surplus residual-income valuation, including bank/insurer equity profiles. |
| asset-based-valuation-modeler | Source-supported assets, realizability haircuts, liabilities and equity-per-share bridge. |
| sum-of-the-parts-valuation-builder | Segment equity/enterprise values with financing and corporate-cost reconciliation and double-counting controls. |
| valuation-reconciliation-analyzer | Method comparisons preserving security/class, share count/basis, accounting context and discount timing; no mandatory blend. |
| issuer-credit-researcher | Corporate financial/structural credit analysis; no agency rating or financing approval. |
| issuer-liquidity-refinancing-analyzer | Dated cash, maturities, usable facilities, explicit repayment, refinancing and stress scenarios. |
| covenant-headroom-analyzer | Explicit reviewed contractual definitions and numerator/denominator components; indicative headroom, no legal compliance opinion. |
| credit-relative-value-analyzer | Same-basis credit spread comparisons with currency, instrument, duration/options, rating and staleness exclusions. |
| credit-recovery-scenario-analyzer | Supplied estate/priority waterfall with collateral and claim limits; legal priority remains supplied. |
| investment-thesis-developer | Supplied variant view, catalysts, risks and observable falsification evidence with revisit/coverage state. |

Existing methods gain structured analytical profile composition, market-share
comparability, sizing assumptions/reconciliation, filing materiality triage,
historical segment decomposition, source-bound annual forecast rows, direct-row
DCF, financial-sector equity comps, actual DCF reruns, instrument/guarantee/priority
links, explicit reviewed document amendments, comparative credit surveillance,
multi-baseline earnings and publication applicability/disclosure preparation.
The [support matrix](support-matrix.md) and each package's schema describe the
actual implemented scope. Prior native input modes and mathematical regressions
remain supported; expanded modes explicitly select ir-phase2/1.0.

New skills are version 0.1.0, expanded skills 0.3.0 and the router 0.2.0. Common
analytical output contract version 2.0.0 is distinct from package release versions.

## Model reviewer and retirement

The model reviewer recomputes supplied formulas through a bounded arithmetic AST,
rejects cycles/unknown cells, compares supplied values and reconciliation residuals,
and checks stated assumption/economic limits. It neither reads arbitrary Excel
workbooks nor establishes complete formula inventory, economic correctness, source
truth or model approval. Findings remain explicit; approval is never inferred.

The original auditor was retired only after exact-output parity checks covering
the full original fixture, missing balances/structural breaks, signed balances,
round-six residuals, tolerance boundaries, IDs and invalid inputs. Its source bytes
are retained unchanged in phase2-validation/legacy-auditor. Historical names and
paths resolve to research-financial-model-reviewer with mode legacy-roll-forward.
Wrap the original input as {"mode":"legacy-roll-forward","input": ORIGINAL}.
The reviewer returns the exact original artifact in legacy_result and binds the
outer result to the complete wrapped original. Prefixed compatibility scripts and
fixtures retain direct legacy regression behavior without a duplicate active skill.

## Evidence, timing and valuation boundaries

The canonical analysis contract reuses the existing source vocabulary and eligibility
checks. Methods validate financial identities, dimensions, periods, timestamps and
their own formulas. Every used row citation must occur in the top-level declared
evidence references so it is subject to the same permission gate. Unknown bases,
booleans, nonfinite values, duplicate JSON object keys, unsupported shapes and wrong
source identities fail or remain explicitly unresolved. Ineligible source evidence
withholds the analytical result and source projection. All outputs reconstruct
against separately retained originals.

Annual indexed valuations require their timing convention and discount origin.
The evidence/review as_of date is not silently treated as that origin. These methods
do not claim date-calibrated spot or stub-period valuation. Reconciliation withholds
a combined range for incompatible timing, security/class, accounting basis, units
or shares. Bank/insurer dividend/residual and equity-comps profiles do not create
a corporate FCFF or three-statement fallback for financial institutions.

Earnings actuals cannot precede the declared release; a frozen baseline and its cited
source must be known strictly before release. Source knowledge cannot occur after
the observation's asserted knowledge time. Multiple baselines retain fiscal calendar,
period, measure and accounting context. No authenticated consensus feed is bundled.

Instrument/document inventories require explicit completeness assertions; complete
rows alone do not establish complete issuer debt or governing-document inventories.
Conditional facilities, restricted cash, unresolved amendments and unknown principal
do not become usable funds, legal definitions or zeros. Intra-date netting and
supplied legal priority remain stated modeling assumptions.

## Reviewed adapters

The [adapter registry](../../catalog/investment-research-adapters.json) supports
exactly five pairings:

1. Annual three-statement forecast rows to DCF.
2. Complete selected-currency/unit maturity inventory to dated liquidity analysis.
3. Explicit reviewed governing covenant definitions to headroom analysis.
4. DCF equity valuation to same-identity method reconciliation.
5. Independent model-review findings to initiation preparation.

Each requires actual installed producer and consumer packages, retained producer
input/output, matching identity/as_of/cutoff/use/purpose/audience/barrier context,
source eligibility and intact package manifests. It validates and reconstructs the
producer, maps declared fields, validates the receiving input, computes the receiving
result and validates it against that mapped original. Issues and permitted evidence
survive. Different source versions under the same ID are a conflict, not a merge.

Mapped receiver fields must be empty or exactly equal to the projection. Conflicting
forecasts, obligations, test definitions or prior review findings require adjudication;
they are never silently overwritten. Explicit share-count basis and timing survive.
Outside-horizon maturity exclusions are visible; unresolved past-due obligations
block the bounded maturity mapping. Hashes identify the adapter implementation,
registry, original/result and package manifests, not authenticated truth.

Use tools/review_ir_handoff.py REQUEST.json or the router's portable
scripts/review_handoff.py REQUEST.json --library-root LIBRARY_ROOT. Validate a saved
handoff using OUTPUT.json --input REQUEST.json. Separately installed native packages
are an explicit offline dependency. A route plan does not execute a handoff, and no
other method pairing is claimed compatible.

## Validation and preservation

Independent expected-value/adverse suites, actual CLI checks, detached reconstruction,
cross-package adapter tests and separate-agent fresh forward cases support the
engineering result. The validation record preserves initial findings and their
corrections, including earnings knowledge-time inconsistencies, CLI postlude failure,
share-basis loss and conflicting receiver-obligation replacement.

The pre-edit baseline covers 17,892 source files. Preservation checks compare every
baseline source outside declared Phase 2 ownership and verify every archived auditor
source against its pre-edit digest. Phase 1 validation evidence is unchanged. No
commit, push, publication, trade or live system/model change is performed.

## Remaining work

Phase 3 covers controlled model updates, corporate events and research QA; Phase 4
covers macro, cross-asset, sovereign, public-finance and structured-credit methods.
Live licensed data, entitlements, workbook ingestion, broader sector/market methods,
additional reviewed adapters and practitioner/institutional acceptance remain open.
Catalog regeneration is reproducible from the current saved catalog plus approved
additions/overrides; the external authoritative workbook was not reloaded.

## Method and governance references

The engineering design distinguishes enterprise cash flows from equity cash flows
and keeps financing claims in the appropriate bridge. [CFA Institute, Free Cash
Flow Valuation](https://www.cfainstitute.org/insights/professional-learning/refresher-readings/2026/free-cash-flow-valuation).
Residual-income inputs explicitly preserve the clean-surplus relationship; it is
an assumption requiring review. [CFA Institute Research Foundation, Earnings
Quality](https://rpc.cfainstitute.org/sites/default/files/-/media/documents/book/rf-publication/2004/rf-v2004-n3-3927-pdf.pdf).

Banking model-risk governance is not universal publication or agent approval.
SR 26-2 replaces SR 11-7/SR 21-8 and explicitly excludes generative/agentic AI from
its scope; institution-specific governance remains necessary. [Federal Reserve,
SR 26-2](https://www.federalreserve.gov/supervisionreg/srletters/sr2602.htm) and
[current guidance](https://www.federalreserve.gov/frrs/guidance/supervisory-guidance-on-model-risk-management.htm).
The earlier [research-source applicability register](research-sources.md) remains
relevant; none of these sources grants data rights or deployment authorization.
