---
name: suspicious-activity-report-drafter
description: >-
  Draft a fact-based Suspicious Activity Report (SAR) narrative and case package
  from an approved, adjudicated investigation — subjects and parties,
  accounts and instruments, a dated chronology, aggregate amounts with tie-outs, suspected
  typologies mapped to observed indicators, an evidence index, and the investigative rationale
  (the 5 Ws and How) — as a controlled draft for compliance quality review and authorized human
  filing. Use when an FIU investigator or SAR quality reviewer must turn a concluded
  investigation into an audit-ready SAR draft, tie amounts and dates to source evidence, confirm
  party coverage and typology consistency, and route for MLRO/BSA sign-off. HARD BOUNDARY:
  drafts and packages only — it never makes the suspicion or file/no-file determination, files
  or e-files a SAR, submits to FinCEN, closes or dispositions the case, writes a system of
  record, sends the package, or adds speculation beyond the evidenced facts; every regulated
  decision and the filing stay with the authorized human.
license: MIT
compatibility: Amazon Quick Desktop; requires case-management, transaction-monitoring/investigation, transactions, KYC/AML, sanctions/PEP/adverse-media screening, typology-library, and records-archive MCP integrations (all read-only), plus document-intelligence and approved-source retrieval for citations.
metadata:
  aws-fsi-category: "Compliance & Financial Crime"
  aws-fsi-skill-type: "Artifact-creation skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Draft & package"
  aws-fsi-agent-pattern: "Interactive production copilot"
  aws-fsi-delivery-wave: "Wave 3 - regulated casework"
  aws-fsi-action-mode: "Draft-only; no system-of-record change"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Restricted (AML/BSA — SAR confidentiality; tipping-off controls)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Compliance & Financial Crime (FIU)"
  aws-fsi-primary-user: "FIU investigator / SAR quality reviewer"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Suspicious Activity Report Drafter

## Purpose and outcome
Take a **concluded, human-adjudicated** transaction-monitoring investigation and marshal its
facts into a controlled, source-mapped **draft SAR package** that a compliance quality reviewer
and MLRO/BSA Officer can act on. The package assembles the subjects and parties, accounts and
instruments, a dated chronology, the amount/chronology tie-outs, a typology assessment against
the approved library, a fact-based **5W+H narrative**, an evidence index, and the investigative
rationale — each mapped to an approved source. The outcome is an audit-ready SAR draft queued
for quality review and sign-off: the suspicion / file-no-file determination, any case closure,
and the filing itself remain with the authorized human. This skill matches
[assets/output-template.md](assets/output-template.md).

## Use when
- "Draft the SAR narrative and case package for this concluded investigation."
- "Assemble a fact-based SAR and tie the amounts and dates back to source evidence."
- "Package the subjects, chronology, typologies, and rationale for SAR quality review."
- "Which evidence is still missing before this SAR draft goes to the MLRO?"

## Do not use
- To **decide** whether the activity is suspicious or whether to file → that is the human
  compliance determination on an already-adjudicated investigation.
- To **file or e-file a SAR**, submit to FinCEN, or set a filing status of record → never
  automated; a separate authorized human action via BSA E-Filing.
- To **investigate or disposition** an alert/case → `transaction-monitoring-alert-investigator`.
- To **adjudicate a sanctions match** → `sanctions-match-adjudicator`.
- To **disposition adverse media** → `adverse-media-investigator`.
- To **verify beneficial ownership** → `beneficial-ownership-verifier`.
- Any request to **close a case, disposition, file, send/submit, or write a system of record**,
  or to add **speculation** → refuse; package and route to a human.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill sits **downstream** of the
adjudicated investigation and **upstream** of SAR quality review, MLRO/BSA approval, and human
filing. It emits a durable `case_id` + draft package and pulls corroboration from specialist
skills; it must not perform their work, the investigator's, or the human filer's. A SAR draft
is produced **only** from a case approved for SAR drafting; otherwise it fails closed.

## Inputs and prerequisites
- An approved SAR case-intake object: `config_version`, `case_id`, `case_approved_for_sar`,
  `approving_investigation`, `filing_context`, `subjects[]`, `accounts_instruments[]`,
  `activity{}`, `transactions[]`, `typologies[]`, `typology_library{}`, `narrative_inputs{}`,
  `evidence[]`, `investigation_rationale{}`, `required_approvals[]`, `recorded_approvals[]`.
  Schema and field list: [scripts/validate_input.py](scripts/validate_input.py).
- Read access to case management, transaction-monitoring/investigation, transactions, KYC/AML,
  screening, the typology library, and the records archive — all read-only.
- The **approved output template**, **typology library**, and **quality checklist** are
  versioned config.

## Source hierarchy
See [references/source-map.md](references/source-map.md). Case management is the system of
record for case state, the `case_id`, and the SAR-drafting approval; the investigation supplies
findings/rationale; transactions supply the chronology and tie-out inputs; KYC for parties;
screening for context (route, do not conclude). **Cite every fact.** An uncited assertion is
treated as unsupported and downgraded to a gap.

## Workflow
1. **Validate intake** — run [scripts/validate_input.py](scripts/validate_input.py); fail
   closed on structural problems, warn on tie-out breaks and gaps (they force `needs-evidence`).
2. **Confirm authorization (hard boundary)** — if `case_approved_for_sar` is not true, the
   package is `blocked` and routed to `transaction-monitoring-alert-investigator`; draft no
   narrative of record.
3. **Assemble (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py): builds the fourteen
   sections, computes the **amount/chronology/count tie-outs**, checks **party coverage** and
   **typology consistency**, and assembles the fact-based 5W+H narrative + evidence index.
4. **Set packaging status** — `blocked` (hard boundary) → `needs-evidence` (any gap: tie-out
   break, uncovered party, unsupported typology, incomplete/uncited 5W+H, uncited fact) →
   `ready-for-quality-review` (complete, reconciled). Never a determination/filing state.
5. **Attach recommendation + routes + approval ledger** — an advisory review path, specialist
   corroboration routes, and the required-approval ledger (pending in a fresh draft).
6. **Validate output** — run [scripts/validate_output.py](scripts/validate_output.py); fail
   closed on any control breach. Present the draft for quality review; do not send or file it.

## Validation loop
Run `validate_input` before and `validate_output` after. The output check enforces: allowed
draft status only (no determination/closure/filing state); all fourteen template sections
present; no unsupported claims (chronology, narrative, evidence index, rationale, and supported
typologies all cited); tie-outs reconcile for a `ready` package (and a claimed `pass` truly
reconciles); no speculation/conclusions of guilt; required approvals recorded; hard-boundary
consistency; and screens for determination/closure, filing, and send/submit language. Fail
closed on any miss. See [references/controls.md](references/controls.md) and
[references/domain-rules.md](references/domain-rules.md).

## Human approval
`required`. This skill drafts and recommends; humans decide. The suspicion / file-no-file
determination, SAR quality review, MLRO/BSA compliance approval, any case closure, and the
filing itself require the authorized human role. Obtaining the recorded approvals and filing
are the human steps — the draft merely lists the approvals as pending and never files.

## Failure handling
- **Tie-out break** (amount/chronology/count) → mark `amount_tie_out.status = break`, set
  `needs-evidence`, list the break; never force a `pass`.
- **Uncited fact / gap** → mark the section a gap, set `needs-evidence`, list what is missing;
  never fill a gap by assumption or speculation.
- **Unadjudicated case** → hard boundary: `blocked`, route to the investigator; make no
  determination.
- **Sanctions/adverse-media/ownership question** → package the evidence and route to the
  specialist; do not conclude.
- **Stale/conflicting sources** → cite both with dates/versions and flag the conflict.
- **Tool timeout / partial data** → return a partial draft with an explicit incompleteness flag
  and `needs-evidence`; assume no automatic retry.

## Output contract
1. **Draft SAR package** — the fourteen template sections, each cited, keyed to
   [assets/output-template.md](assets/output-template.md).
2. **Packaging status** — `ready-for-quality-review` | `needs-evidence` | `blocked` (never a
   determination/filing state).
3. **Tie-outs** — amount, chronology, and count reconciliation with computed vs. declared.
4. **Recommendation + routes** — advisory review path and specialist corroboration handoffs.
5. **Approval ledger** — every required role with status (pending until a human signs).
6. **Machine-readable** — the package JSON keyed by `case_id`.
7. **Standing note** — draft-only; no determination, closure, filing, system write, or send.

## Privacy and records
**Restricted — AML/BSA.** SAR-confidentiality and tipping-off controls apply: never produce
customer-facing text that reveals SAR or monitoring activity, and keep the draft within the
authorized SAR workflow. Mask subject/account identifiers to what the narrative requires (names
and identifiers are masked in the package). Retain the draft, citations, tie-outs, and
config/template versions per BSA recordkeeping; log every read and every package assembly with
the drafter identity. Do not compile personal data beyond the SAR scope.

## Gotchas
- **Drafting ≠ determining or filing.** `ready-for-quality-review` means "complete and queued,"
  not "suspicious" or "filed." The determination and the filing are always a human's.
- **Fact-based only.** The narrative states observed facts and cites them; no "obviously",
  "must be laundering", or conclusions of guilt. Let the facts speak.
- **Tie-outs must reconcile.** A break is a gap, not a rounding nuisance — `needs-evidence`, and
  a claimed `pass` is re-checked by the output validator.
- **A gap is not a pass.** An uncited fact, uncovered party, or under-evidenced typology forces
  `needs-evidence`; it is never quietly asserted.
- **No SAR from an unadjudicated case.** Drafting from a case not approved for SAR would itself
  make the suspicion determination — hard boundary, `blocked`, route to the investigator.
- **Tipping-off is a legal risk.** Keep the draft and its existence internal to the SAR workflow.
