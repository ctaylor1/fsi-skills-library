# Payments source and rule governance

Reviewed for Phase 1 on 2026-09-17. These are orientation/verification sources, not
a redistributable or complete operating-rule pack. Record profile authority,
participant, jurisdiction, version, effective interval, review owner and review due
date. Distinguish proposal, adoption, active application and withdrawal. Source
retrieval is not authentication and a firm policy cannot override applicable law.

| Source | Phase 1 use | Limits and maintenance |
|---|---|---|
| [Federal Reserve FedNow product sheet](https://www.frbservices.org/binaries/content/assets/crsocms/financial-services/fednow/fednow-product-sheet.pdf) | Master-account/correspondent settlement; no prefunding requirement | Older launch orientation: do not use its historical transaction limits or launch dates as current rules. |
| [FedNow operating hours](https://www.frbservices.org/resources/financial-services/fednow/operating-hours) | Continuous processing versus accounting/cycle and liquidity windows | Check current operating procedures and participant arrangements before operational use. |
| [TCH RTP document library](https://www.theclearinghouse.org/payment-systems/rtp/document-library) | RTP rule and funding source index | Use applicable version and participant role; do not copy licensed materials into public packages. |
| [PCI SSC FAQ 1318](https://www.pcisecuritystandards.org/faqs/1318/) and [standard library](https://www.pcisecuritystandards.org/document_library/) | Correct 3.2.1 retention/disposal versus 3.3.1 post-authorization SAD prohibition | Full assessment requires current standard, applicability, period/sample coverage and qualified review; artifact presence alone is insufficient. |
| [CFPB Reg E 1005.11](https://www.consumerfinance.gov/rules-policy/regulations/1005/11/) | U.S. consumer EFT error-resolution distinction | Product, notice, institution calendar and exceptions require an applicable profile; not a card-scheme deadline substitute. |
| [CFPB Reg Z 1026.13](https://www.consumerfinance.gov/rules-policy/regulations/1026/13/) | U.S. billing-error distinction | Separate from Reg E and network chargeback proceedings; professional applicability review remains necessary. |
| [Visa merchant updates](https://www.visa.com/en-us/resources/visa-merchant-business-news-digest) | Current scheme bulletin discovery | Exact eligibility/stage/region rules require authorized source material; counting historical transactions is not proof of CE eligibility. |
| [SWIFT ISO roadmap](https://www.swift.com/standards/iso-20022/iso-20022-bytes/journey-continues) | Message/usage/version transition context | Normalized JSON interpretation is not raw XML/XSD validation or complete network conformance. |
| [FinCEN travel-rule guidance](https://www.fincen.gov/resources/statutes-regulations/guidance/funds-travel-regulations-questions-answers) | Reject universal stablecoin travel threshold | Scope, entity, currency and applicable jurisdiction determine obligations; do not substitute one national threshold globally. |
| [GENIUS Act](https://www.govinfo.gov/link/plaw/119/public/27) and [MiCA scope](https://www.esma.europa.eu/publications-and-data/interactive-single-rulebook/mica/article-2-scope) | Legal instrument and issuer/user distinctions | Enacted law, implementing rules and effective dates are separate; deposit tokens are not automatically payment stablecoins. |

Shared profile validation is in `shared/payments/payment_contract.py`. Deployment
rule packs need explicit provenance, licensed-use permissions and recertification.
Synthetic fixture policies are test inputs, not an authoritative compliance library.
Re-review on material rule/source changes and before a deployment uses a profile;
an annual metadata review date does not certify acceptance.

## Phase 2 public profiles — reviewed 2026-09-18

The native rail/message registries and consumer/scheme reference profiles are in
`shared/payments/`. Each records source references, version/scope and limits.
They are bounded public summaries, not authorized institution rule packs. The
initial review interval ends 2026-10-18, except RTP, which requires review by
2026-09-29 before announced September 30 and October 4 changes. Review-due dates
are freshness controls, not a declaration that the underlying rule ceases then.

| Primary source | Implemented use and version boundary |
| --- | --- |
| [FedNow procedures, February 2026 v3.5](https://frbservices.org/binaries/content/assets/crsocms/resources/rules-regulations/021326-fednow-service-operating-procedures.pdf) | Master-account/correspondent liquidity orientation; actual access, balances and arrangements must be reviewed. Free-text funding declarations do not establish rail compatibility. |
| [TCH RTP library](https://www.theclearinghouse.org/payment-systems/rtp/document-library) | Current and upcoming versions identified separately; prefunding distinguished from FedNow. Refresh before the announced changes above. |
| [Nacha ACH file details](https://achdevguide.nacha.org/ach-file-details) | Native 94-character Entry Detail field positions, routing checksum and supported transaction-code subset; not complete file or rules validation. |
| [Federal Reserve ISO migration notice](https://www.frbservices.org/news/press-releases/071525-iso20022-migration-announcement) | Fedwire ISO migration is completed, not a future readiness event. The local ISO parsers inspect selected message fields, not full Fedwire conformance. |
| [EPC SCT Inst rulebook](https://www.europeanpaymentscouncil.eu/what-we-do/epc-payment-schemes/sepa-instant-credit-transfer/sepa-instant-credit-transfer-rulebook) and [SDD](https://www.europeanpaymentscouncil.eu/what-we-do/sepa-direct-debit) | 2025 SCT Inst v1.1 orientation and distinct SDD mandate/return concepts. The November 15, 2026 address change is future at review date. |
| [Pay.UK FPS](https://www.wearepay.uk/what-we-do/payment-systems/faster-payment-system/how-faster-payments-work/), [Bacs principles v18 January 2026](https://www.wearepay.uk/wp-content/uploads/2026/02/Pay.UK-Bacs-System-Principles-V18-Jan-2026.pdf), [Bank of England CHAPS](https://www.bankofengland.co.uk/payment-and-settlement/chaps) | Distinct timing, access and recovery orientation. Institution contracts/calendars are required; FPS/Bacs raw message adapters are explicitly unsupported. |
| [FinCEN MSB registration](https://www.fincen.gov/resources/money-services-business-msb-registration) | Federal registration is separate from state permissions; actual activity and state scope require specialist review. |
| [PSD2](https://eur-lex.europa.eu/eli/dir/2015/2366/oj/eng) and [Instant Payments Regulation](https://eur-lex.europa.eu/eli/reg/2024/886/oj/eng) | EU framework and phased instant-payment obligations; national transposition, entity scope and effective dates remain separate. |
| [FCA payments/e-money](https://www.fca.org.uk/firms/payment-services-regulations-e-money-regulations), [safeguarding](https://www.fca.org.uk/firms/emi-payment-institutions-safeguarding-requirements), [fraudulent payments](https://www.fca.org.uk/consumers/fraudulent-payments) | UK permissions, current safeguarding framework and unauthorized/authorized-payment distinctions. Safeguarding is not deposit insurance; current CASS/SUP requirements require scoped review. |
| [CFPB Reg E](https://www.consumerfinance.gov/rules-policy/regulations/1005/11/) and [Reg Z](https://www.consumerfinance.gov/rules-policy/regulations/1026/13/) | Separate product-specific error-review clocks and exceptions. Bundled preparation records case scope and supplied review; it does not calculate or validate legal due dates. |
| [Visa merchant library](https://usa.visa.com/support/merchant/library.html) | Public stage/evidence orientation only. Authorized current reason-code, regional and stage rules are still needed; no universal response deadline or compelling-evidence transaction-count rule is supplied. |

`sync_payment_foundation.py --check` checks the additive resource bundles in the
ten new packages and two existing dispute packages. Canonical contract 1.0.0
continues to be checked separately by `sync_payment_contract.py --check`.
Recheck the source and the institution's actual scope before using a profile;
hash consistency and declared reviewer details do not authenticate either.

## Phase 3 source refresh — 2026-09-18

The [Federal Reserve operating-circular index](https://www.frbservices.org/resources/rules-regulations/operating-circulars.html)
identifies [FedNow April 2026 v3.6](https://www.frbservices.org/binaries/content/assets/crsocms/resources/rules-regulations/042826-fednow-service-operating-procedures.pdf),
effective April 28, as the current public procedures. The February v3.5 pointer
retained in the historical Phase 2 table above is superseded and returned 404 on
direct fetch. The current shared US-FEDNOW profile is version 2026-09-18.2 and uses
the April source. The native-message registry is version 1.0.1 with the same
source correction; supported parser fields are unchanged. Section 16 separates nonvalue request messages from funds movement;
acceptance is followed by a distinct credit transfer. The normalized collection
module does not implement private message specifications or operational clocks.

New credential orientation uses [EMVCo tokenisation](https://www.emvco.com/emv-technologies/payment-tokenisation/),
[EMVCo 3DS](https://www.emvco.com/emv-technologies/3-d-secure/),
[FIDO passkeys](https://fidoalliance.org/passkeys/) and
[Visa Account Updater FAQs](https://developer.visa.com/capabilities/vau/vau-faq).
The tokenisation index lists framework v2.4, published July 2026. No cryptographic,
protocol-conformance or liability-shift verification is claimed. Actual token
domains, provider results, consent/opt-out, deployed versions and institution rules
must be inspected. Public protocol descriptions do not establish payment intent.

Analytics, liquidity, incident and AI/operations packages cite their primary source
maps. Cohort definitions, stress assumptions, exposure/friction formulas, fault
scenario sets and evaluation gates are explicit library or supplied-institution
conventions, not regulatory thresholds or guarantees. Rule/provider fees, uptime,
label maturity, expected savings and test completion are never inferred from a
public profile. Primary source retrieval supports orientation, not deployment acceptance.

## Phase 4 regional and specialist sources — reviewed 2026-09-18

The canonical [regional profiles](../../shared/payments/regional-profiles.json)
record bounded Pix, UPI and Interac e-Transfer domestic credit-push orientation.
They do not extend the core rail/message parser or initiation adapter scope.
Case-level participant access, actual payee/account/alias and local specialist
evidence must be supplied. The initial review due date is 2026-10-18; refresh
earlier for material changes.

| Source family | Implemented use and limit |
| --- | --- |
| BCB Pix/SPI/DICT, NPCI UPI, Interac operator sources | Domestic method and beneficiary-directory orientation; no raw network conformance, live directory verification, general mandates or international-link adapter. Exact primary links and product exclusions appear in the regional registry. Some operator content is client-rendered; public index/document evidence supports only the stated scope. |
| [CFPB remittance disclosures](https://www.consumerfinance.gov/rules-policy/regulations/1005/31/), [BIS FX risk](https://www.bis.org/committees/bcbs/basel-consolidated-guidelines/module/rma/20) and correspondent/liquidity references | Currency/fee/delivery-chain reconciliation and separate funding obligations. OUR/SHA/BEN terminology does not establish fee compliance; no institution credit, netting or bridge access is presumed. |
| [CBK NPS](https://www.centralbank.go.ke/national-payments-system/), CFPB, EU and FCA sources | Bounded KE/KES cash-agent mobile money and US/EA/UK wallet design. Stored value, provider responsibilities, backing, redemption and consumer duties need actual product and country review. See the wallet source map for versioned documents. |
| Current legal texts and issuer/operator contracts | Concrete stablecoin/fiat alternatives with instrument, entity, corridor and chain review. Proposed rules, legal enactment and operational availability remain separate. The digital-money reference does not convert pilots into production access. |
| Company filings, audited policy notes and [IFRS fact-specific principal/agent discussion](https://www.ifrs.org/news-and-events/updates/ifric/2022/ifric-update-april-2022/) | Source-defined gross/net comparisons and explicit economic denominators. Management bridges are disclosed analysis conventions, not prescribed accounting or securities recommendations. |
| [AP2 v0.2 specification](https://ap2-protocol.org/ap2/specification/) and [ACP repository](https://github.com/agentic-commerce-protocol/agentic-commerce-protocol) | Optional agent-commerce evidence contracts; exact deployed versions and merchant/provider interoperability require review. AP2 v0.2 agent subdelegation is unsupported. Normalized intent/cart objects are internal inputs, not AP2/ACP serialization or signature verification. |

The [protocol reference](../../shared/payments/agent-commerce-protocols.md) records
version and deployment distinctions. Generalized agent budgeting and all financial
equations are explicit library conventions over supplied records. Stable hashes
prove local consistency only. No public document authenticates a supplied source,
reviewer identity, balance, quote, credential, legal permission or production system.
Licensed institution packs, human regional/payment specialist review and deployment
acceptance remain separate gates. Canonical bundle checks now cover 39 contracts
and 23 foundation packages plus two dispute extensions; optional region and agent
resources are checked by the same foundation synchronizer.
