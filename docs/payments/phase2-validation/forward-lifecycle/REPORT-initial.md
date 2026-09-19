# Phase 2 independent forward evaluation: bank and card lifecycle

Current evaluation uses fresh synthetic evidence derived from actual SKILL.md, reference schemas and native domain contracts. No golden outputs or regression tests were read. All artifacts are under this directory; no repository edits, network/live actions, approvals or funds movement occurred. Every Python command uses `/tmp/fsi-p0-venv/bin/python -B` with `PYTHONDONTWRITEBYTECODE=1`.

## US bank: design, exact initiation, outcome and servicing

The use case is an urgent USD 1,250 domestic disbursement requiring instant, 24x7 availability and best-effort recovery only. Synthetic provider access, actual endpoint reach, timing/calendar evidence, funding and contracted fees are registered and separately cited. The supplied funding descriptions distinguish ACH bank funding, FedNow master-account liquidity and RTP prefunding.

| Case | Practical result |
|---|---|
| b1-design-urgent | ACH conflicts with instant/24x7 requirements. FedNow and RTP are candidates for human review. No automatic preferred rail or cheapest-rail choice is made. Overall needs-evidence retains the incompatible ACH candidate rather than silently dropping it. |
| b2-design-conflicting-evidence | Unreachable FedNow endpoint, two contradictory RTP funding rows and omitted commercial fees remain explicit unknowns. Neither nominal rail availability nor a public profile overrides missing provider evidence. |
| b3 / b4 exact initiation | Retained new individual USD 500 and alternative two-item USD 500 + 750 batch inputs. Exact sourced instruction, intent, screening, account verification, currency policy and independent batch totals are provided. Initial native calculation fails because the initiation domain handoff lacks the new foundation's required_inputs field. Input validation itself passes. |
| b5 authentication without intent | Login/MFA identity evidence is present; payment-specific intent is absent. Initial full native calculation is blocked by the same unrelated handoff construction error, so a successful end-to-end guardrail result cannot yet be claimed. |
| b6 / b7 ACH mandate | Distinct debit-collection branch has exact intent and a one-off USD 100 mandate capped at 150; the paired variant revokes it. Native calculations initially fail at the same handoff integration boundary. |
| b8 future delegation | Execution September 25, delegation expiry September 20, review September 18. Native calculation initially fails at the handoff boundary; isolated domain analysis incorrectly labels it ready with no findings because delegation checks only the review date. |
| b9 previous payment with new ID | Retains prior payment detail binding plus a new instruction ID. Initial native calculation is blocked at handoff construction; duplicate behavior needs the later native retest. |
| b10 reported completion | A separately supplied normalized payment outcome trace reports ACSC but has no linked settlement proof. Result remains settlement_reported, not settled. |
| b11 linked settlement | Adding distinct payment-linked settlement evidence and ACCC makes the normalized payment trace settled in the offline adapter. This is supplied evidence, not live verification. |
| b12 normal bank return | USD 100 linked return against a separately supplied USD 1,250 settled original has exact original binding, complete empty prior-service ledger and independent scoped permission. Plan is ready for human review; execution false and original-ledger rollback false. |
| b13 recovery request | USD 1,250 cancellation/recovery plan remains a request. Its actual financial effect stays unknown until counterparty/system response; no guaranteed recovery. |
| b14 return from acceptance only | Even a synthetic policy allowing accepted state cannot substitute for original settlement/posting; funds-movement-not-evidenced remains a gap. |

The USD 500 individual and USD 500+750 batch are alternative initiation controls under the same program, not proof that their aggregate became the separate P-BANK-1250 outcome. A later exact USD 1,250 chain input may be supplied, but identity mapping must remain explicit. The normalized outcome and servicing original are independent supplied evidence; no successful initiation review manufactures a submitted or settled payment.

## UK merchant partial card refund

Original purchase GBP 240 is source-reported posted. A completed GBP 70 partial refund and pending GBP 50 refund are both linked to the original, leaving GBP 120 capacity before the proposed new GBP 100 refund. A supplied UK merchant/network/debit/action profile and separate action-specific refund policy are included; these synthetic facts do not establish scheme authority or customer statutory rights.

| Case | Practical result |
|---|---|
| u1 partial-refund | Completed70 + pending50 are deducted; remaining capacity120. New100 proposal is ready for human review, with no execution or rollback. It would leave20 only if the pending/new actions complete as assumed; that future outcome is not established. |
| u2 request130 | Exceeds120 available capacity and stays needs-evidence. |
| u3 pending history in USD | Currency conflict invalidates ledger reliance; completed, pending and remaining amounts become null. No implicit FX. |
| u4 missing ledger, caller marks complete | Finds service-history-unknown but initially reports completed0/pending0/remaining240. This numeric result contradicts the missing-history boundary; retained as a defect awaiting fix/retest. |
| u5 explicitly incomplete ledger | Completed, pending and remaining totals are all unknown/null. |

## Issuer debit program and card operations

The synthetic US consumer debit program declares an issuer bank also acting as sponsor/program manager, a separate processor, and a network settlement counterparty. It supplies account/funding responsibilities, custody/account-title terms, controls and a settlement flow. The script creates a draft blueprint but always retains a regulatory-applicability specialist gap; it does not determine licensing, deposit protection, profitability or launch approval. Assigning issuing accountability to the processor and omitting custodian identity adds specific unresolved design findings.

The card transaction has USD240 authorization, an explicit240 hold, distinct90 and150 presentments, and240 clearing. A currently supplied issuer profile permits multiple presentments and presentment-based hold reduction.

- **Clearing alone is not merchant funding.** c3 shows clearing240, while settlement/funding/posting remain null. Remaining hold scenario0 is expressly a profile-based reconstruction, not verified available balance. Completion/funds availability remains false.
- **Settlement plus posting still does not prove merchant funding.** c4 adds network settlement240 and issuer posting240, but funding remains null. A refund operation creates controlled action requirements and a separate servicing handoff, not a refund.
- Missing operating profile (c5) leaves hold remainder unknown. Explicit90 hold release overlapping with inferred presentment release (c6) also leaves it unknown instead of double deducting.
- Reused event/source identities across USD and EUR transactions (c7) quarantine both sets of stage amounts; no cross-currency total is created.
- Program regulatory uncertainty explicitly carried via upstream_issues (c8) remains in findings and handoff context.

Customer-facing answer: “The supplied records show the purchase cleared. They do not show that your merchant has received funding. Even the later issuer posting and network settlement records are separate from merchant-funding evidence.”

## Composition and limits

These packages expose handoff contracts and required inputs, not a complete adapter pipeline. Target inputs still require independent native schema assembly and validation. Design intent_evidence_available is only a dependency declaration; it is not exact payer authorization. Neither a draft blueprint nor a review-ready initiation result authorizes execution. A servicing plan does not create its return/refund instruction; any actual new movement still needs its exact control review and institution approval/execution, followed by source-linked outcome evidence.

Regional rail profiles are read from the repository's currently reviewed synthetic/offline context. Public source links were not fetched because this evaluation is explicitly local and read-only. No legal conclusion or live availability was inferred. The policy dates, refund deadlines, funding and prices used here are test evidence, not claimed universal scheme rules.

## Evidence and reproduction

- `run_bank_service.py`, `run_card.py`, `forward_support.py`: fresh synthetic input construction and exact native CLI runner.
- `command-results-bank.json`, `command-results-card.json`: each input hash, command, status, stdout path and stderr.
- Each scenario retains `*-input.json`, `*-output.json` when successful, and per-mode `.stdout`/`.stderr`.
- Source hashes are retained before/after each package group. Final fixes require a fresh final-source rerun and closeout hashes before this report can state those defects are resolved.
- `b8-domain-only-interim.json` is deliberately labelled an isolated domain diagnostic, not a validated full output pack.

Run with `PYTHONDONTWRITEBYTECODE=1 /tmp/fsi-p0-venv/bin/python -B SCRIPT.py`. Do not treat initial failure evidence as current after a later fix; the final retest section will identify superseding artifacts while retaining the original evidence.
