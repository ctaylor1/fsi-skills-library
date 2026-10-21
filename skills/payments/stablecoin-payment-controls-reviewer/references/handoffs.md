# Adjacent-Skill Handoffs — stablecoin-payment-controls-reviewer

This skill produces a cited **control-findings pack** (`review_id`) and stops. It does not
adjudicate, resolve, file, approve, or close.

## Downstream (route the human/reviewer to)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `stablecoin-settlement-assessor` | Compare a concrete participant/corridor/asset/chain settlement use case with a fiat alternative | Reviewed controls, original sources and unresolved conditions; construct and validate the separate native assessment input |
| `sanctions-match-investigator` | Screening surfaced a wallet/counterparty sanctions match needing adjudication | `review_id` + the screening finding |
| `aml-alert-triager` | Transaction-monitoring/AML alert needs triage. A separately scoped ledger may use `transaction-monitoring-scenario-evaluator`; full case investigation still requires the accountable FIU investigator. | `review_id` + txn evidence |
| `suspicious-activity-report-drafter` | Reviewer decides a SAR may be warranted (draft-only, human-filed) | `review_id` + evidence |
| `payment-settlement-reconciler` | On-chain vs ledger break needs resolution | recon finding + break detail |
| `payment-transaction-reconciler` | General mint/burn or ledger reconciliation work | recon finding |
| `gl-reconciler` | Reserve/GL tie-out to the general ledger | reserve figures |
| `payment-lifecycle-diagnoser` / `bank-payment-exception-investigator` / `payment-repair-planner` | A specific payment failed, is stuck, or needs repair | txn reference |
| `iso-20022-message-interpreter` | A raw ISO 20022 (pacs/pain/camt) message must be parsed | the message |
| `third-party-risk-assessor` | Custodian / reserve-bank third-party risk due diligence | custodian identity |
| `regulatory-reporting-data-validator` | Reserve/transaction regulatory report data quality | report dataset |
| `regulatory-change-impact-analyzer` | A new/changed stablecoin rule must be assessed | rule reference |
| `payment-scheme-change-tracker` | A card/payment network rule change affects controls | rule reference |
| `audit-evidence-packager` / `regulatory-exam-response-packager` | The cited findings feed an audit or exam response | `review_id` + evidence |

## Upstream (may call this skill)

`omnichannel-case-orchestrator` and payments risk/compliance reviewers may request a control
review. A scheduled monitor is **not** used here (this skill is interactive,
`aws-fsi-scheduled-agent: no`); continuous rail monitoring belongs to
`instant-payment-risk-monitor`.

## Duplicate-execution prevention

- This skill evaluates and evidences **controls only**; it must not adjudicate a sanctions
  hit, investigate an alert to disposition, resolve a break, approve a launch, file, or close
  — those belong to the human reviewer and the downstream skills above.
- Downstream skills reuse the `review_id` evidence rather than recomputing the control
  findings.

Phase 1 handoff: retain case/participant/rail/jurisdiction, original source references and unresolved issues using payment-contract.md. Validate the target native input independently; renamed skills are not assumed input-compatible. Local IDs and hashes grant no authority and do not persist or accept a case. Only invoke installed capabilities within the requested scope.
