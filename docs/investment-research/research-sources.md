# Research sources and applicability

Review date: 2026-10-20. These references informed the architecture and control design;
they are not bundled legal advice or automatic regime selection. Institution owners
must establish current applicability before deployment.

| Source | Design implication and limit |
|---|---|
| [SEC EDGAR APIs](https://www.sec.gov/search-filings/edgar-application-programming-interfaces) | Keep accession/version, issuer identity, filing time and precise location; an API is not an investment conclusion. |
| [SEC non-GAAP interpretations](https://www.sec.gov/rules-regulations/staff-guidance/corporation-finance-interpretations/non-gaap-financial-measures) | Distinguish reported and adjusted measures; staff interpretations have a specific scope. |
| [FINRA 2241](https://www.finra.org/rules-guidance/rulebooks/finra-rules/2241) and [2242](https://www.finra.org/rules-guidance/rulebooks/finra-rules/2242) | Equity and debt research supervision have different definitions, applicability and exclusions; a checklist does not clear a report. |
| [FCA PS25/4](https://www.fca.org.uk/publications/policy-statements/ps25-4-investment-research-payment-option-fund-managers) | Research-payment options require the relevant firm/regime and safeguards; not a universal publication rule. |
| [Federal Reserve SR 26-2](https://www.federalreserve.gov/supervisionreg/srletters/sr2602.htm) | Supersedes SR 11-7/SR 21-8. Banking model-risk guidance is scoped; generative/agentic AI is excluded and simple arithmetic is not automatically a model under this guidance. Do not apply as universal IR law. |
| [IFRS 18](https://www.ifrs.org/issued-standards/ifrs-18-presentation-and-disclosure-in-financial-statements/) | Record accounting regime and adoption rather than assuming identical reported measures. |
| [FASB standards](https://www.fasb.org/page/PageContent?pageId=/standards/accounting-standards-updates-issued.html) | Segment/disaggregation comparability depends on entity, fiscal period, adoption and applicable update. |
| [FRED real-time periods](https://fred.stlouisfed.org/docs/api/fred/realtime_period.html) | Preserve vintage for macro research; date-based vintage evidence alone does not prove intraday availability. |
| [FSB private-credit report](https://www.fsb.org/uploads/P060526.pdf) | A nonbinding analytical/data-gap reference, not authority to authenticate instruments or credit performance. |
| [CFA Standard V(A)](https://www.cfainstitute.org/standards/professionals/code-ethics-standards/standards-of-practice-v-a) | Diligence and reasonable-basis principles apply within their professional scope, not as universal legislation. |

Phase 1 fixtures are synthetic and offline. No vendor license, subscription, source
entitlement or redistribution permission is supplied by this repository.

## Phase 4 specialist method references

Primary sources checked during the 2026-10-20 implementation. These inform the
bounded method definitions; actual observations, source rights and institution
applicability must still be supplied and reviewed. They do not certify these
packages as complete implementations of the referenced frameworks.

| Source | Implemented implication and limit |
|---|---|
| [FRED vintage dates](https://fred.stlouisfed.org/docs/api/fred/series_vintagedates.html) and [real-time periods](https://fred.stlouisfed.org/docs/api/fred/realtime_period.html) | Preserve releases and the information set at cutoff; no ALFRED connector or independent external inventory verification is bundled. |
| [BEA quarterly annualization](https://www.bea.gov/help/faq/122) | Compounded quarterly comparison is a calculation convention, not a prediction or inferred probability. |
| [BIS monetary-policy transmission](https://www.bis.org/speeches/20150616-monetary-policy-transmission-whats-known-and-whats-changed) and [ICMA bond/yield methods](https://www.icmagroup.org/assets/documents/Media/Bondmarketsbook/Bond%20markets_structures%20and%20yield%20calculations.pdf) | Theme transmission remains a supplied hypothesis; duration is only a local first-order price/yield sensitivity, with no calibrated causal coefficient or portfolio recommendation. |
| [IMF public debt projection guide](https://www.elibrary.imf.org/view/journals/005/2021/005/article-A001-en.xml) | Preserve nominal debt/GDP, primary-balance sign, FX valuation and stock-flow scope; the complete IMF tool is not implemented. |
| [IMF gross financing needs guide](https://www.imf.org/en/publications/tnm/issues/2025/01/24/a-guide-and-tool-for-projecting-public-gross-financing-needs-555913) | Distinguish maturity/cash financing needs, noncash stock adjustments, actual cash draw and financing access. |
| [MSRB sources of repayment](https://www.msrb.org/Sources-Repayment) and [official statements](https://www.msrb.org/Official-Statements) | Preserve GO versus pledged revenues, actual security/document scope and fiscal periods; no legal pledge or tax determination. |
| [Regulation AB Item 1111](https://www.ecfr.gov/current/title-17/chapter-II/part-229/subpart-229.1100/section-229.1111), [Item 1113](https://www.ecfr.gov/current/title-17/chapter-II/part-229/subpart-229.1100/section-229.1113), [Item 1121](https://www.ecfr.gov/current/title-17/chapter-II/part-229/subpart-229.1100/section-229.1121) | Keep collateral inventory, security priority, fees/triggers/reserves and period distributions distinct. The simplified supplied profile is neither arbitrary-deal modeling nor a Regulation AB compliance opinion. |

Each new package's source-map and domain-rules references retain the narrower
definition and supported-profile details. No third-party filing/data is distributed
as a synthetic test fixture; source authentication and professional review remain
separate from numerical reconstruction.
