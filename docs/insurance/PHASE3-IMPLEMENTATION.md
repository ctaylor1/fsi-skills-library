# Insurance Phase 3 — analytical and specialist depth

Status: implementation and bounded local verification complete, 2026-09-18.
User-authorized after the Phase 2 checkpoint. Professional and deployment acceptance
remain separate.

Implement the 21 distinct jobs in [the phase manifest](../../catalog/insurance-phase3-capabilities.json), taking insurance from 40 to 61 packages. The scope follows [the roadmap](IMPLEMENTATION-PLAN.md): market/product economics, portfolio analysis, experience and life actuarial work, premium audit/compensation, recovery/disability/disputes, fraud/SIU, assumed reinsurance, exposure/CAT, finance/capital/ORSA and market conduct.

Each package must deliver a substantive bounded native method, complete source/schema/method references, practitioner output template, executable positive/adverse checks and standalone dependencies. Explicit supported profiles do not establish comprehensive line/jurisdiction coverage. Do not invent rates, assumptions, deadlines, source access, actuarial selection or legal authority. Shared source hashes prove content consistency only.

Exit criteria: metadata/catalog regeneration and installed routes; native receiver compositions preserving scope and uncertainty; meaningful arithmetic/evidence tests; fresh independent practitioner evaluations with original input replay after observed repairs; whole-library validation and retained evidence. The existing Phase2 computation/helper checkpoint is preserved unless a concrete integration defect justifies a documented change. Phase4/5 and domain specialist/institutional acceptance remain distinct work.

## Implemented native workflows

| Package | Bounded method and useful output |
| --- | --- |
| `insurance-market-strategy-researcher` | Source-bound market shares and concentration only with a complete reconciled inventory; fact/inference/hypothesis register with contrary evidence and falsification work. No invented market total or automatic strategy recommendation. |
| `insurance-product-economics-modeler` | Separate carrier underwriting/pretax and MGA commission/service economics; supplied assumptions, explicit premium denominators and period capital return. Unknown amounts remain unknown. |
| `insurance-portfolio-performance-analyzer` | Aggregate premiums, incurred losses, expenses, claim counts and exposures; comparable-period ratio changes and an exact segment-mix/within-segment loss-ratio bridge. No averaging segment ratios or inferred causal attribution. |
| `insurance-experience-study-builder` | Individual time-at-risk intervals with delayed entry, right censoring and segment transfer; constant-intensity ACT/365 actual/expected study and event risk sets. No annual death-probability conversion, table graduation or credibility selection. |
| `life-annuity-pricing-modeler` | Supplied annual mutually exclusive mortality/lapse assumptions, survival-weighted beginning/end-of-year cashflows and deterministic discounted margin. No selected pricing basis or profitability approval. |
| `long-duration-liability-valuation-reviewer` | Dated supplied liability cashflow PV and a dated movement/booking-adjustment bridge. This is not a statutory reserve or accounting measurement engine. |
| `insurance-alm-scenario-analyzer` | Matched dated asset/liability cashflows, supplied parallel spot-rate shocks, PV surplus and cumulative liquidity gaps. No reinvestment, dynamic behavior or asset-adequacy opinion. |
| `insurance-premium-audit-reviewer` | Source-identified auditable exposures, supplied units/rates/modifiers, minimum/fixed charges and final-cent premium tie-out; explicit stable basis IDs prevent relabelled exposure double counting. |
| `insurance-producer-compensation-reconciler` | Contract-trigger earned amounts, exact split shares and source-authorized chargebacks tied to original earnings; producer control differences. Cancellation alone does not establish a chargeback right. |
| `claim-recovery-case-reviewer` | Rights/limitation evidence, preservation ownership, gross/cost/net recovery and supplied pro-rata loss interests. No determination of standing, demand, settlement or disbursement. |
| `disability-care-benefit-reviewer` | Carrier/administrator criterion-by-period evidence and supplied continuous-calendar daily-indemnity waiting days, offsets and caps. No clinical assessment, benefit adjudication or claimant representation. |
| `claimant-dispute-packager` | Claimant-owned adverse-reason/evidence/request matrix, contrary evidence and chronology, reviewed notice route and supplied deadline. Health appeals retain their specialized receiver. |
| `insurance-fraud-pattern-analyzer` | Exact typed identifier links across observed windows, source-bound common-entity exclusions, deduplicated claimed exposure and mature outcome fractions. Signals and retrospective rates do not establish fraud or historical detection precision. |
| `insurance-siu-investigation-assistant` | Case-level falsifiable hypotheses and innocent alternatives, supporting/contradictory evidence, supplied-digest custody continuity and lawful draft tasks. No fraud verdict, covert collection or referral submission. |
| `reinsurance-underwriting-reviewer` | Assuming-reinsurer occurrence-XOL losses through per-event and annual aggregate limits, signed participation, costs and exhaustive supplied scenario probabilities. No reinstatements, risk-transfer opinion, price selection or binding. |
| `insurance-exposure-aggregation-analyzer` | Policy/location/peril identity, currency-separated TIV and geographic/model-readiness gaps. No silent deduplication, FX conversion or loss-model inference. |
| `catastrophe-scenario-analyzer` | Supplied jointly sampled annual event losses produce occurrence/aggregate exceedance statistics and average annual loss; standalone event rates support AAL only. No summed marginal PMLs or inferred joint distribution. |
| `insurance-financial-close-reviewer` | Scoped subledger/GL balances with a reviewed debit-positive convention, balanced proposed journals and remaining account breaks. No posting or close certification. |
| `insurance-capital-solvency-analyzer` | Approved additive capital components, explicitly named requirement denominator, ratio/threshold comparisons and stress bridges. No statutory RBC formula engine or solvency opinion. |
| `insurance-orsa-packager` | Material risks, scenarios/horizons, capital/liquidity reconciliation and governance evidence. The output identifies unresolved evidence; it does not turn checklist completion into ORSA approval. |
| `insurance-market-conduct-reviewer` | Supplied scoped rules, evaluable case chronology, pending versus missing evidence and ratio-of-sums monitoring metrics. No invented deadlines, sample extrapolation or compliance verdict. |

Each package includes native validation/calculation/output scripts, documented
schemas and methods, primary orientation sources, controls, handoffs, output
templates and executable positive/adverse cases. Dependencies are bundled for
standalone use. Planned natural-language evaluations remain explicitly unexecuted
unless supported by a separate run record.

## Routing and composition

The router activates the 21 installed packages while retaining line, participant
and deployment-inventory checks. Carrier disability/LTC review, claimant dispute
preparation, initial fraud referral, portfolio signals and SIU casework have
different owners. Underwriting selection, medical decisions, hazard-model generation
and unsupported accounting/regulatory engines remain explicit boundaries.

Two actual native receiver chains are exercised: capital stress results to ORSA
reconciliation, and a portfolio identifier signal to a selected SIU claim. Reviewed
basis/context mappings bind the original source artifact to receiver fields;
missing mappings, invalid native values and dropped unresolved issues cannot
produce complete handoffs. These are explicit examples, not universal adapters or
an automatically orchestrated lifecycle.

Existing underwriting, rating, filing and reserving guidance now points to the
installed bounded methods. Their native computations and the shared insurance
contract/foundation remain unchanged. Router metadata, manifests and approved
catalog overrides preserve these changes through regeneration.

## Evaluation and acceptance

Fresh independent agents author raw synthetic cases and expected business results
before invoking the native scripts. Original inputs, failed attempts, interface
supplements, outputs and practitioner interpretations are retained separately in
[Phase 3 validation](phase3-validation/README.md). Frozen source packets are never
rewritten to turn a failure into a pass. Hashes show content identity, not source
authenticity or professional acceptance.

Independent review found two benefit-output defects: unsupported monthly methods
still emitted daily estimates, and incomplete offset inventories emitted zero
offsets and overstated net figures. Both were corrected with dependency-specific
gates and verified by replaying the same inputs. Four interface documentation
omissions (experience exit enums, reinsurance enums/capacity, close profile sign
convention and ORSA reviewer field) were corrected with separately disclosed
mapping supplements. Author/integration checks also tightened source binding for
common-entity fraud exclusions and market-conduct metric aggregation.

Final checks pass: 308 insurance and 1,517 whole-library executable package checks;
37 insurance integration methods and 362 repository methods; 296 packages with no
structure errors/warnings or dangling handoffs. The new workflows contain 342
regression methods, included within package checks. The final 46-input replay
matches all reviewed results across 138 native command checks, including the three
expected rejections of one malformed input. See the retained validation record for
exact counts, commands, original observations, repairs and acceptance limits.

The library retains its established `compatibility` frontmatter. Its own validator
accepts that format; generic skill-creator validation rejects the field. No passing
generic ecosystem compatibility claim is inferred.

Source connections, current institution-approved profiles, domain specialist
review, broader model evaluation and deployment controls remain outstanding.
Next implementation milestone: Phase 4 architecture and measured automation in
[the roadmap](IMPLEMENTATION-PLAN.md).
