---
name: investment-committee-memo-builder
description: Prepare committee review packets for private deals or explicit public-security, manager and allocation modes, with source-linked thesis, scenarios, mandate gates and pending decisions. Use for investment committee preparation; no investment decision, trade, commitment, manager appointment or allocation optimization.
license: MIT
compatibility: Python 3.10+ offline JSON helpers; live source connectors and authenticated delivery require separate deployment integration.
metadata:
  aws-fsi-category: "Asset Management"
  aws-fsi-skill-type: "Artifact-creation skills"
  aws-fsi-risk-tier: "R2"
  aws-fsi-archetype: "Draft & package"
  aws-fsi-agent-pattern: "Interactive production copilot"
  aws-fsi-delivery-wave: "Wave 2 - analytical production"
  aws-fsi-action-mode: "Draft-only; no system-of-record change"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "existing-updated"
  aws-fsi-human-approval: "external-delivery"
  aws-fsi-data-classification: "Highly Confidential (MNPI / client-confidential)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Asset Management investment & product"
  aws-fsi-primary-user: "Private equity / private credit / asset-management investment team"
  aws-fsi-version: "0.2.0"
  aws-fsi-recertification-date: "2027-09-20"
---

## Phase2 explicit modes

Read [Phase2 method](references/phase2-domain-rules.md), [schema](references/phase2-schema.md), [source map](references/phase2-source-map.md), [controls](references/phase2-controls.md), and [handoffs](references/phase2-handoffs.md) for the new mode. Use [Phase2 template](assets/phase2-output-template.md) for its draft. New explicit modes preserve the no-mode/private-deal CLI. public-security compares three uniquely named downside/base/upside scenarios with probabilities summing to one; total return includes supplied income. Expected return is a scenario expectation, not a forecast. Proposed security and resulting sector weights are checked against hard mandate bounds. manager mode checks manager identity, current supplied diligence status, material issues, allocation fraction and mandate limit. allocation mode checks current/proposed weights sum to one, per-asset bounds and liquid-weight minimum; expected return is sum(weight × supplied expected return), one-way turnover = half sum(abs(weight change)). No covariance estimate or optimization is implied.

The legacy workflow below applies to the original no-mode schema (and explicit private-deal for IC). Unknown supplied modes fail closed. New results are internal-review investment-foundation/1.0 artifacts with detached input; old fixture behavior is preserved.


Read [references/domain-rules.md](references/domain-rules.md) for the supplied-input validation boundary and current deterministic limits before using the scripts.


# Investment-Committee Memo Builder

## Purpose and outcome
Assemble a **draft** investment-committee memorandum for a private-markets deal (buyout,
private credit, growth) from approved inputs — the financial model, diligence materials,
transaction documents, market/company data, approved research, and portfolio context. The
outcome is a controlled, fully-cited memo that **ties out to the model**, includes a
mandatory downside case, sizes the position against fund limits, and ends with the explicit
questions the committee must decide. The deliverable is a decision-ready draft; the
investment decision itself stays with the human committee.

## Use when
- "Draft the IC memo for [deal] from the diligence, the LBO model, and the comps."
- "Assemble the memo: thesis, structure, valuation, returns, scenarios, risks, sizing,
  decision questions."
- "Tie the memo figures out to the model and check the scenarios are consistent."
- "Check this draft memo for unsupported claims and concentration-limit breaches."

## Do not use
- **Building the model / returns** (LBO, three-statement, DCF, sensitivities) → upstream
  skills (see handoffs). This skill consumes model outputs; it does not derive them.
- **Making or recording the investment decision / committee vote** → refuse; the committee
  decides. `committee_decision` stays `pending`.
- **Sending, circulating, or submitting** the memo → out of scope (draft-only).
- **A lending credit-committee memo** → `credit-memo-drafter` (Banking).
- **Personalized investment advice** ("should I invest my money") → refuse.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). Upstream skills produce the model,
diligence, scenarios, market data, and portfolio inputs; this skill assembles and ties them
into a memo keyed by `deal_id`. Downstream, an approved deal routes to
`investment-thesis-monitor`; a memo may roll into a `board-committee-pack-builder` pack. The
decision, legal terms, and MNPI/wall-crossing sign-off are **human** handoffs.

## Inputs and prerequisites
- An IC build request: `deal` metadata + recommended action (a *proposal*); `sources[]` with
  approval flags; `model` outputs (entry/exit, returns, leverage); `valuation`; `scenarios`
  (Base/Upside/**Downside**); `risks` with mitigants; `sizing` (commitment, fund NAV,
  single-name & sector limits); `thesis_points`; `decision_questions`; `approvals`. Schema:
  [scripts/validate_input.py](scripts/validate_input.py).
- Read access to the model, VDR/diligence, transaction docs, market data, the **approved**
  research library, portfolio exposures/limits, and the versioned IC template + limit config.
- **Data-quality minimums:** the model source and a downside scenario are required; every
  material claim must carry a `source_id`; market/research sources must be **approved**.

## Source hierarchy
See [references/source-map.md](references/source-map.md). The **model** is the system of
record for figures — the memo ties out to it and never restates looser numbers. Diligence and
transaction documents are authoritative for facts and terms; market/research must be approved
and versioned. Cite every figure and claim `{system}:{ref}@{date/version}`; when sources
conflict, cite all and surface it as a decision question.

## Workflow
1. **Validate & normalize** — run `validate_input`; on missing/unapproved inputs stop at
   `needs-data` and name the producing skill. Do not draft on a malformed request.
2. **Tie out to the model (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py): reconcile
   `entry_multiple`, `equity_value_proxy`, and `leverage_x` to the model; block on any break.
3. **Check scenarios** — require a downside; enforce ordering downside ≤ base ≤ upside; tie
   the base case to the model returns.
4. **Size the position** — compute position as % of NAV; block on a single-name limit breach;
   block on a hard sector-limit breach; disclose an explicitly discretionary breach or entry above the peer range.
5. **Trace every claim** — map each thesis point, risk, scenario, valuation, and sizing input
   to an approved source; block unsupported/unapproved claims.
6. **Assemble the memo** — populate the nine required template sections
   ([assets/output-template.md](assets/output-template.md)) from approved inputs only, with a
   traceability appendix and an approvals block. Leave `committee_decision: pending`.
7. **Validate output** — run `validate_output`; fail closed on any miss.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py)
after. The output gate is **independent** (it re-derives findings from the memo record):
template fidelity (all nine sections), no unsupported/unapproved claims, model/scenario/sizing
tie-outs, recorded `preparer`+`reviewer` approvals, `committee_decision == pending`, no
prohibited language, and the standing draft-only note. Correct and re-run until clean or stop
at `needs-data`.

## Human approval
`external-delivery`. A human must review the draft and **record** the preparer and reviewer
sign-offs before the memo is circulated to the committee; the committee makes and records the
decision. This skill proposes and packages — it never approves, commits, circulates, or files.
See [references/controls.md](references/controls.md).

## Failure handling
- **Missing / unapproved input** → `needs-data`; list exactly what is missing and the
  producing skill; never invent a figure or comp to fill the gap.
- **Tie-out break** → block; surface the model-vs-memo discrepancy rather than restating.
- **Missing downside / unordered scenarios** → block; a memo without a modeled downside is
  incomplete.
- **Concentration-limit breach** → single-name and hard sector breaches block; an explicitly discretionary sector breach is disclosed.
- **Conflicting sources** → cite all and raise a decision question; do not silently pick one.
- **Tool timeout** → return the partial draft with an explicit incomplete flag; assume no
  retry and no step-up authorization.

## Output contract
1. **Draft memo** — the nine required sections, each cited to its source(s).
2. **Traceability appendix** — claim → citation → as-of/version → approved.
3. **Tie-out + scenario + sizing checks** — machine-readable results and any flags.
4. **Approvals block** — `preparer`/`reviewer` status; `committee_decision: pending`.
5. **Decision questions** — the explicit items the committee must decide.
6. **needs-data list** — anything blocking a clean draft.
7. **Standing note** — "Draft investment-committee memorandum for human review. It is not
   investment advice, records no committee decision, and has not been circulated, sent, or
   submitted."

## Privacy and records
**Highly Confidential (MNPI / client-confidential).** Deal materials are frequently MNPI:
restrict to the deal team + committee, honor information-barrier / wall-crossing controls, and
never disclose deal existence or terms outside the entitled group. Retain the draft,
traceability appendix, citations, and template/limit-config versions with the deal record; log
every source read and draft generation with the preparer identity for audit and
recertification.

## Gotchas
- **Draft ≠ decision.** The memo is an input to the committee; the skill never records the
  vote. `committee_decision` staying `pending` is a feature, not an omission.
- **Tie out, don't restate.** If the memo figure and the model disagree, the model governs —
  fix the memo, or disclose the adjustment with a citation.
- **The downside is mandatory.** Dropping it (or ordering scenarios wrong) blocks output.
- **Approved ≠ present.** A market/research source that exists but is not marked approved is
  treated as unapproved and its claims are blocked.
- **Sizing is a limit check, not a recommendation.** A single-name breach blocks; a sector
  breach is disclosed to the committee, not silently suppressed.
- **No selling language.** Guarantees, "risk-free", and "can't-lose" wording fail the output
  screen; present balanced evidence and open questions instead.

## Phase 1 support boundary

Bounded private-deal memo; generic public/manager/allocation templates remain planned

This package performs only its documented local supplied-input operations. Live source access, authenticated permissions, production engines and professional acceptance are separate deployment requirements. Generated resources are pinned in `references/package-manifest.json`; maintain the canonical shared source. Legacy identifiers resolve through the repository migration registry.
