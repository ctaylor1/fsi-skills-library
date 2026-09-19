# Payments Phase 4 implementation

The user authorized the next phase on 2026-09-18 after Phase 3. This implements the
[Phase 4 roadmap](ROADMAP.md): regional/corridor depth, wallet and mobile-money
programs, advanced platform/commercial flows, concrete stablecoin assessment,
digital-money references and optional agent-commerce evidence. Four new packages
bring Payments to **38 packages**, plus PCI in Cybersecurity. Seven optional native
modules extend six existing packages. Authenticated execution remains a separate
deployment capability and is not implemented.

## Delivered workflows

| Workflow | Native implementation | Scope and boundary |
| --- | --- | --- |
| [Cross-border design](../../skills/payments/cross-border-payment-designer/SKILL.md), new | Correspondent/remittance/commercial corridor alternatives, payer debit and beneficiary receipt, explicit FX orientation and fees, linked economic legs, entity-scoped regulatory/screening evidence | Bounded US/USD, EA/EUR, UK/GBP, BR/BRL, IN/INR and CA/CAD scenarios. Quotes, permissions, reach, screening and receipt are supplied evidence, not authenticated facts. |
| [Regional bank design](../../skills/payments/bank-payment-workflow-designer/references/regional-schema.md), optional | Pix, UPI and Interac e-Transfer domestic credit-push profiles, actual-case beneficiary/account/alias and institution access evidence | Separate BR/IN/CA entrypoint. Core US/EA/UK bank and initiation modes retain their scope; raw local network and native initiation adapters are not supplied. |
| [Corridor funding](../../skills/payments/payment-liquidity-and-funding-analyzer/references/corridor-schema.md), optional | Separate entity/account/currency time paths; explicit gross FX transfers, debit/credit access windows, funding dependencies and failed-transfer stress | Future credits cannot repair earlier cash deficits. No implicit FX, cross-entity pooling, credit facility or executable funding is inferred. |
| [Wallet/mobile money](../../skills/payments/wallet-and-mobile-money-program-designer/SKILL.md), new | Pass-through versus stored-value liability models, ledger/backing reconciliation, funding/redemption channels and cash-agent responsibilities | US/EA/UK design plus bounded domestic KE/KES mobile-money evidence. Provider authorization, eligible backing and access remain institution/country review. |
| [Advanced platform flows](../../skills/payments/platform-payment-flow-designer/references/advanced-platform-schema.md), optional | Multi-level legal ownership, unique economic collections, seller/connected-account allocations, reserves, refunds/chargebacks and pending batch payouts | Separate owners/currencies remain separate. Seller allocation, pending payout and actual settlement are different states. |
| [Commercial cards](../../skills/payments/commercial-payment-workflow-designer/references/commercial-card-schema.md), optional | Corporate/purchasing/fleet/virtual-card spend controls, supplier/invoice/remittance binding, credential limits and payment outcomes | Authorization and holds do not establish payment. Partial settlement does not mean an entire invoice is paid. Credit underwriting remains adjacent work. |
| [Stablecoin settlement](../../skills/payments/stablecoin-settlement-assessor/SKILL.md), new | Concrete participant, use case, corridor, asset, chain and fiat alternative; quote-bound all-in costs and custody/redemption/liquidity/finality/provider conditions | Separate from the older control-policy reviewer. No peg, redemption access, universal confirmation count or legal permission is assumed. |
| [Business models](../../skills/payments/payment-business-model-analyzer/SKILL.md), new | Payment-company roles/value chains, gross/net/pass-through bridges, defined take rates and comparable segment economics | Closes the remaining original company/competitor request. No invented current company data, cross-currency aggregation or securities recommendation. |
| Agent-commerce [initiation](../../skills/payments/payment-initiation-control-reviewer/references/agent-commerce-schema.md), [credential](../../skills/payments/payment-credential-authentication-reviewer/references/agent-commerce-schema.md) and [platform](../../skills/payments/platform-payment-flow-designer/references/agent-commerce-schema.md), three optional modules | Exact consent, allowed items/merchants, cart/proposal binding, pending spend/counts, replay, expiry/revocation, credential scope and merchant responsibilities | Normalized evidence review, not AP2/ACP serialization, signature/trust verification, token release, atomic reservation or payment submission. Unsupported public-protocol subdelegation stays a gap. |

Digital-money distinctions remain a [reference module](../../skills/payments/stablecoin-settlement-assessor/references/digital-money-reference.md).
Tokenized bank deposits, CBDCs, stablecoins and programmable settlement are not
interchangeable instruments. Research, pilots and prospective availability are not
present production access. No dedicated tokenized-deposit or CBDC execution skill
was created solely for technology coverage.

The singular `payment-business-model-analyzer` is the installed destination for the
original architecture's plural proposal label. It was not a previously installed
package; no historical package was renamed. All four additions are retained through
provisional catalog additions, and changed package metadata through approved overrides.
The source workbook remains unchanged pending reconciliation.

## Optional modules and compatibility

The source-bound 1.0 envelope is retained. The shared foundation now permits an
installed domain module to declare a bounded `SUPPORTED_JURISDICTIONS` set. Missing
that declaration preserves the original US/EA/UK behavior; request data cannot
widen it. Regional resources are separate from the existing core rail registry.
The Kenya wallet scope likewise does not enable Kenya in other packages.

Each extension has separate input/calculation/output entrypoints. Existing CLI
schemas and fixtures remain available. Integration checks copy packages outside
the repository, remove their optional modules/resources, and compare original core
outputs. New modes are standalone and source-bound; all handoffs still require
assembly and validation of target-native inputs. In particular, a BR/IN/CA design
does not turn the original initiation reviewer into a local network adapter.

The router activates the four previously planned original requests and adds
regional, wallet, corridor-funding, advanced-platform, commercial-card and explicit
agent-module intents. It preserves participant clarification, incomplete context,
installed-target checks and action refusal. `unprofiled-region` remains an honest
gap. Routing to a skill does not establish rule coverage or downstream readiness.

## Sources and ownership

Public orientation uses BCB, NPCI, Interac, CBK, CFPB, FCA, EU legal sources, BIS,
current instrument/project references and protocol-owner documentation. Source maps
record review dates and limits; case-level accountable review owners and current
institution documents remain required. No licensed participant manuals are bundled.
See [source governance](SOURCE-GOVERNANCE.md).

Current AP2 v0.2 terminology and ACP dated snapshots are recorded separately in
the [protocol reference](../../shared/payments/agent-commerce-protocols.md). The
library's generalized intent/cart/budget model is an internal analysis contract,
not proof of conformance to either protocol. Static protocol, rule or source hashes
do not establish authenticity, identity, live revocation or legal authority.

## Validation and acceptance

[Phase 4 validation](phase4-validation/README.md) records package and repository
checks, optional-mode isolation, independent fresh forward evaluations, observed
findings, unchanged-case retests and preserved historical evidence. Counts are
reported by their actual unit; regression methods inside package commands are not
additional independent evaluations.

Authoring and bounded agent evaluation are separate from the roadmap's specialist
and deployment gates. No licensed institutional rule-pack acceptance, human
payments/country/legal specialist sign-off, broad model benchmark or authenticated
deployment acceptance is claimed. These remain required before operational use.
No additional implementation phase is presumed beyond the agreed four; subsequent
work should address those acceptance gates or a specifically justified expansion.
