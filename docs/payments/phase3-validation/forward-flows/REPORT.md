# Independent Phase 3 forward review: platform, commercial and liquidity

Reviewed on 2026-09-18. This reviewer authored fresh synthetic sources and numerical expectations without reading package evals, fixtures, regression tests, golden files or previous results. Read only each package's SKILL.md, input schema and domain helper. No repository file was changed by this review.

Result: **21 independently authored scenarios, 61 native CLI calls, 115 assertions passed, 0 failed**. The one structurally rejected case used a duplicate registered source identity; all other scenarios ran native input validation, calculation and output validation bound to the original request. All domain/support resource hashes matched before and after the run. These checks establish bounded behavior for these cases, not source authenticity, professional acceptance, legal clearance or production readiness.

## Practitioner request 1: Marketplace payouts

“Two separately incorporated sellers share the platform's collection arrangement. Can we propose payouts after a partial refund, reserves and a pending payout?”

Raw synthetic evidence: one settled USD 1,000 customer charge; seller 1 allocation 600, seller 2 allocation 300, platform fee 70, processor fee 30. Seller 1 has an 80 partial refund, 100 paid, 50 held in reserve and 120 pending. Seller 2 has a 25 chargeback and 20 reserve. Both propose 200 to their own entity's account. Six operational responsibilities are assigned to the platform under explicit synthetic contracts; this does not determine regulatory permissions.

Independent calculation:
- Seller 1 amount still owed: 600 − 80 − 100 = **420 USD**. Available before proposal: 420 − 50 − 120 = **250 USD**. A proposed 200 leaves 50 economically uncommitted, subject to separate exact initiation review.
- Seller 2 available before proposal: 300 − 25 − 20 = **255 USD**. A proposed 200 leaves 55. Seller 1 and seller 2 cannot pool or substitute balances.
- The gross charge ties exactly to allocations. Fees do not reappear in either seller's entitlement.

Native output matched both calculations. A proposed 251 for seller 1 produced an insufficiency gap. Changing seller 1's payout destination to seller 2's account suppressed its capacity. A missing refund amount, incomplete ledger, and a pending rather than settled charge each suppressed capacity. Duplicate source registration failed input validation. None authorized a payout or inferred that a platform role label supplies permissions.

## Practitioner request 2: Corporate ERP and supplier remittance

“We have an invoice credit, a partial settlement across two invoices, a pending payment and a new multi-invoice proposal. What is still payable and what remittance is required?”

Raw synthetic evidence for one buyer/supplier/currency:
- Invoice A: 500 USD, linked credit 50, previous settled allocation 200.
- Invoice B: 300 USD, previous settled allocation 100, pending allocation 50.
- The previous payment is 300 with allocations A=200/B=100. A separate 50 payment for B is pending.
- Proposed payment 300 allocates A=200/B=100. Each payment has one remittance identifying exactly its allocation IDs and supplier. Proposed documents are explicitly DRAFT references, not proof of delivery.

Independent calculation: A open and remaining before proposal **250 USD**; B open after settlement **200 USD**, remaining after its pending allocation **150 USD**. The proposed split stays within each invoice and sums to 300. All three remittances tied without treating the pending payment as settled.

Changing the pending outcome to unknown suppressed B's reliable balance and routed investigation before replacement. A missing credit amount, incomplete history, a duplicate business invoice number (including different case/whitespace and new ERP ID), and duplicate ERP credit identity each returned evidence gaps and affected balances stayed unknown. Omitting one remittance allocation produced a remittance mismatch. No ERP posting, invoice closure or payment authorization occurred.

## Practitioner request 3: Weekend funding and stress

“Can our FedNow master-account arrangement and a separate RTP prefunded position meet weekend obligations, even if funding windows close and Monday funding fails? We also have a euro book.”

Raw synthetic USD evidence at Friday 2026-09-18 16:00 EDT:
- FedNow account, entity Bank A: balance 1,000, held 100, an additional 200 reservation bound to Saturday's 700 obligation. Sunday obligation 500. Firm Monday receipt 600 arrives within the evidenced Monday 09:00–17:00 funding window.
- RTP funding-agent prefunded account, entity Bank B: balance 800. Saturday outflow 600 and Sunday outflow 500. Friday 17:00 receipt 200 misses its evidenced 16:30 funding cutoff. A forecast receipt 900 is not firm and is excluded.
- Stress removes the FedNow Monday receipt and increases outgoing obligations by 20%.

Independent calculation:
- FedNow opens at **700 USD available** after hold/reservation. Saturday consumes 700 and releases the already-deducted 200 reservation, leaving **200**. Sunday reaches **−300**. Monday restores the ending position to **300**, but cannot cure the prior weekend funding shortfall. Peak base shortfall is **300 USD**.
- FedNow stress: available economic starting resources 900 − Saturday 840 − Sunday 600 = **−540 USD**; no Monday receipt. Peak/ending deficit **540 USD**.
- RTP excludes both unavailable funding receipts: 800 − 600 − 500 = **−300 USD** base; **−520 USD** under the 20% obligation stress. The FedNow account's Monday balance cannot be netted against this separate position.
- A separately scoped EA SCT Inst EUR account starts at 5,000 and incurs 1,000, ending **4,000 EUR**. It remains separate and supplies no automatic USD conversion or transfer.

All native results matched. Missing opening balance, incomplete history, a FedNow-to-prefunding model substitution, duplicated economic outflow/settlement identity, and unsupported EUR currency on the US rail each suppressed the affected numerical position. Customer-payment 24×7 capability never implied funding-channel availability.

## Findings and retained evidence

No actionable implementation defect was found in these cases. Important operating limits remain explicit: source/contract ownership is supplied rather than authenticated; account availability windows and firm status need real Treasury evidence; fee/reserve ledgers and ERP histories must be complete; profiles do not authorize account access or customer fund movement.

- `run_forward.py`: independent synthetic source construction, numerical expectations and exact native invocation logic.
- `*-request.json`: all native inputs, with source registry and original evidence.
- `*-output.json`, `*.stdout`, `*.stderr`: native artifacts and exact output-validation results.
- `commands.json`: 61 exact argv lists, exits and output locations.
- `assertions.json`: all 115 independent assertions and details.
- `summary.json`: aggregate results and source stability.
- `code-hashes-before.json`, `code-hashes-after.json`: domain, bundled helper and reference hashes.

No natural-language model benchmark, real-system connector test, specialist approval or production acceptance is claimed.
