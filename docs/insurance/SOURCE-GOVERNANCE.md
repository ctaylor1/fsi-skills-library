# Insurance source and acceptance governance

Phases 1–3 implement an offline skills library. It does not ship production policy,
claims, actuarial, filing, vendor-data or payment connections. System/API names in
source maps identify expected evidence providers, not an assertion that a connector
is present or that a caller may access it.

## Reviewed source profiles

A deployment must establish accountable owners and permitted access for the actual
contract, rule, model and data sources. Record jurisdiction/entity/product scope,
version, effective dates, valuation/as-of basis and locator. Treat extracted facts
and user-supplied flags as assertions until checked against authoritative evidence.
Do not resolve conflicting policy/PAS/legal sources through a universal precedence
rule: identify the legally operative contract and applicable law with the owner.

The shared contract binds supplied content and retains uncertainty. It cannot
authenticate source systems, people, consent, professional authority or legal
applicability. Illustrative configurations are not approved institutional rules.
An input validator may accept incomplete evidence so the skill can report gaps;
that is not a readiness/approval decision.

## Primary orientation references reviewed 2026-09-17

| Area | Reference | Scope |
| --- | --- | --- |
| P&C unpaid claims | [CAS unpaid-claims methods](https://www.casact.org/sites/default/files/database/studynotes_friedland_estimating.pdf) | Educational actuarial source: ultimate minus paid is total unpaid; reported-loss basis distinguishes IBNR. Not an approved firm methodology. |
| Actuarial modeling | [ASOP 56](https://www.actuarialstandardsboard.org/asops/modeling-3/) and [ASB standards](https://www.actuarialstandardsboard.org/standards-of-practice/) | Select applicable standards and effective versions; deterministic arithmetic alone is not actuarial acceptance. |
| Life/annuity valuation | [2026 NAIC Valuation Manual](https://content.naic.org/sites/default/files/pbr_data_valuation_manual_current_edition.pdf) | Distinct product/method requirements; no life valuation capability is implemented by P&C reserving. |
| Insurance AI | [NAIC model bulletin](https://content.naic.org/sites/default/files/inline-files/2023-12-4%20Model%20Bulletin_Adopted_0.pdf) | Model guidance and actual state implementation are different. No universal compliance verdict. |
| Distribution | [NAIC annuity working group](https://content.naic.org/committees/a/annuity-suitability-wg), [FINRA 2330](https://www.finra.org/rules-guidance/rulebooks/finra-rules/2330) | State, product, transaction and practitioner capacity matter; Phase 2 adds supplied-evidence sales/replacement review, without establishing state adoption or securities applicability. |
| Accounting and capital | [NAIC SAP](https://content.naic.org/insurance-topics/statutory-accounting-principles), [RBC](https://content.naic.org/insurance-topics/risk-based-capital), [ORSA](https://content.naic.org/insurance-topics/own-risk-and-solvency-assessment), [IFRS 17](https://www.ifrs.org/issued-standards/list-of-standards/ifrs-17-insurance-contracts/) | Different bases and regimes; rate/form filing is not prudential reporting. |
| Delegated authority | [Lloyd's current oversight guidance](https://www.lloyds.com/market-resources/delegated-authorities/market-knowledge/oversight-and-monitoring-of-contracts) | Market-specific oversight; producer licensing alone does not establish binder or claims authority. |
| Standards | [ACORD P&C standards](https://www-dev.acord.org/standards-architecture/acord-data-standards/Property_Casualty_Data_Standards) | Public orientation only. Current licensed schemas, forms and code sets are not bundled or fully verified. |
| Health | [CMS-0057-F](https://www.cms.gov/newsroom/fact-sheets/cms-interoperability-prior-authorization-final-rule-cms-0057-f) | Specific payer/service/date scope; not a universal claim appeal rule. |

US-oriented fixtures do not establish all-state support. International reference
frameworks do not establish domestic applicability. Licensed ACORD, medical,
vendor, rating-manual and proprietary model resources require appropriate access;
the library supplies no substitute licensing claim.

## Remaining acceptance

Separate package structure, deterministic regression, actual handoff behavior,
bounded agent evaluation, human domain acceptance and institutional deployment.
Planned evaluations and README counts are not completion evidence. Broader model
benchmarks, professional review, source integration and execution controls remain
separate gates after this phase's local implementation checks.

## Phase 2 evidence profiles — 2026-09-18

The 17 operating foundations carry package-local primary orientation references and
native field schemas. Source maps distinguish source-system expectations from
available access. Rate methods use supplied, reviewed ultimate-loss and prospective
assumptions; policy/claims/distribution/life/reinsurance profiles bind actual scope,
effective period and source version. No illustrative threshold, notice interval,
consent flag, benefit offset or institution-policy row establishes applicable law.

The two root policy/billing packages use supplied contractual and operational
records; [NAIC policy endorsement guidance](https://content.naic.org/article/consumer-insight-do-you-know-how-use-insurance-rider-or-endorsement)
and [model 915](https://content.naic.org/sites/default/files/model-law-915.pdf) are
orientation, not implemented state law or a universal notice/refund rule. Other
packages link their CAS/ASB, NAIC, FINRA or SEC references directly. Current adopted
law, institution-approved rules and proprietary contract/medical/rating records
must be reviewed for the intended deployment.

Fresh evaluations used invented source packets, not live customer records. Their
raw prose, mappings, outputs and before/after repairs are retained in the
[Phase 2 evidence](phase2-validation/README.md). They validate bounded usefulness and
implementation behavior; source truth, source extraction quality across broader
inputs and professional acceptance are distinct outstanding work.

## Phase 3 analytical evidence profiles — 2026-09-18

The 21 specialist packages separate supplied data from selected methodology and
professional conclusions. Package-local sources include CAS ratemaking context,
the SOA experience-study calculation report, applicable ASOPs, NAIC competition,
market conduct, statutory accounting, capital and ORSA materials, and scoped
state/benefit/claims guidance. References distinguish educational or model guidance
and historical opinions from current adopted law. Exact methods are documented as
bounded package conventions, not as formulas mandated by those references.

Market concentration requires a reviewed denominator and complete inventory.
Actuarial inputs identify event definitions, timing, cashflow basis and selected
assumptions; the package does not select them. CAT statistics require compatible
joint annual loss samples; supplied standalone event rates do not establish a
dependence model. Capital ratios preserve the named denominator and never imply
that a simple additive model implements a regulatory RBC formula. ORSA evidence
and finance proposals remain subject to accountable human review.

Premium basis IDs, compensation rights, recovery interests, benefit definitions,
dispute deadlines, SIU collection authority and market-conduct rules must resolve
to actual reviewed sources. A synthetic profile, supplied lawful-collection flag,
document hash or matching balance cannot authenticate those assertions. Clinical,
legal, actuarial and regulatory determinations stay with the responsible specialist.

[Phase 3 evidence](phase3-validation/README.md) retains independent synthetic case
construction, input-guide defects, original attempts and separately mapped replays.
These establish bounded usefulness and implementation behavior. They do not verify
production extraction quality, current licensed source access or institutional
approval, and no customer action or external submission is performed.
