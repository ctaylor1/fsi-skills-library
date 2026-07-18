---
name: transaction-reporting-quality-checker
description: >-
  Validate the quality of regulatory transaction reports (MiFIR/RTS 22, EMIR, CFTC/SEC-style
  regimes): completeness against the front-office source of record, timeliness against the
  reporting deadline, identifier validity (LEI/ISIN/MIC), mandatory-field population,
  field-mapping and economic reconciliation, and unresolved rejects — then package the
  exceptions with cited evidence and a suggested remediation priority. Use when a regulatory
  reporting or operations analyst asks to "check/validate our transaction reports", "find
  reporting gaps, over-reports, or late reports", "reconcile submitted reports to executions",
  or "package reporting exceptions for remediation". HARD BOUNDARY: this skill produces
  quality-control findings only; it NEVER makes a compliance or breach determination, decides
  that a transaction is not reportable, or submits, amends, cancels, or suppresses a report —
  those are human/authorized-system actions that require approval.
license: MIT
compatibility: Amazon Quick Desktop; requires OMS/EMS, market & reference-data, post-trade/clearing, and regulatory-reporting/ARM MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Capital Markets"
  aws-fsi-skill-type: "Analysis and evaluation skills"
  aws-fsi-risk-tier: "R2"
  aws-fsi-archetype: "Analyze & review"
  aws-fsi-agent-pattern: "Interactive decision-support copilot"
  aws-fsi-delivery-wave: "Wave 2 - analytical production"
  aws-fsi-action-mode: "Read-only analysis"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "external-delivery"
  aws-fsi-data-classification: "Highly Confidential (customer NPI/PII)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Capital Markets operations & compliance"
  aws-fsi-primary-user: "Regulatory reporting / operations analyst"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Transaction Reporting Quality Checker

## Purpose and outcome
Given a batch of submitted regulatory transaction reports and the front-office executions
they should mirror, run a **deterministic quality-control pass** and produce an
**exception pack**: each defect (completeness gap, timeliness breach, invalid identifier,
missing mandatory field, field-mapping/economic mismatch, unresolved reject) is named,
explained in plain language, and attached to cited source and report evidence. The pack
carries a **suggested remediation priority** derived deterministically from the exception
set. A successful output lets a reporting/operations analyst decide what to remediate and
where to route it — the compliance determination, and any report action, remains human.

## Use when
- "Check our MiFIR / RTS 22 transaction reports for completeness and timeliness."
- "Reconcile the submitted reports back to the OMS executions and flag mismatches."
- "Which reports are late, missing, over-reported, or have invalid LEIs/ISINs?"
- "Package this batch's reporting exceptions with evidence for remediation."
- An analyst needs a consistent, cited exception write-up to attach to a remediation ticket.

## Do not use
- The user wants a **compliance/breach determination** ("are we in breach?", "declare this
  compliant"), a **regulator submission/amendment/cancellation**, or a decision that a
  transaction **is not reportable** → out of scope. Provide evidence and route to a licensed
  compliance officer / reporting-operations human (see Human approval).
- The mismatches are actually **trade-record breaks across systems** needing an approved,
  lineage-tracked repair → `trade-break-resolver`.
- The defect is **upstream in the report input pipeline / transformations / controls** rather
  than the trade data → `regulatory-reporting-data-validator`.
- The anomaly suggests **potential market abuse** rather than a data-quality defect →
  `market-surveillance-alert-investigator` (or first-line `surveillance-alert-triager`).
- The exceptions must be assembled into an **examination/inquiry response package** →
  `regulatory-exam-response-packager`.
- The real question is **execution quality / venue / routing** → `best-execution-reviewer`.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill emits an exception pack with
a durable `qc_id`; downstream repair, validation, surveillance, and exam-packaging skills
consume it. It must not duplicate their repair, determination, or filing steps.

## Inputs and prerequisites
- The **report regime** (e.g. MiFIR-RTS22) and an **as-of date**.
- **Submitted reports** for the batch — each with `transaction_ref`, status, submission
  timestamp, the reported field values, and a `source_ref` citation.
- **Source executions** (front office / OMS as position of record) — each with
  `transaction_ref`, execution timestamp, economic terms, a `reportable` flag, and a
  `source_ref`. Schema: [scripts/validate_input.py](scripts/validate_input.py).
- The **versioned reporting config** (deadline, required fields, identifier formats,
  economic fields, tolerances) — see [references/domain-rules.md](references/domain-rules.md).
- Read access to OMS/EMS, reference data, and the regulatory-reporting/ARM archive.

## Source hierarchy
See [references/source-map.md](references/source-map.md). The **front-office execution** is
the position of record for economic terms and reportability; the **submitted report** is
what was actually filed; **reference data** resolves LEI/ISIN/MIC; the **versioned config**
supplies deadlines, required fields, and formats. When a report and the source of record
conflict, cite both and flag it as an exception — never silently trust the report.

## Workflow
1. **Scope & load** — confirm the regime, as-of date, and batch; load submitted reports and
   the matching source executions; validate structure with `validate_input`.
2. **Reconcile & check (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py) to match reports to
   reportable executions on `transaction_ref` and compute exceptions:
   completeness (missing / over-report), timeliness (late vs deadline), identifier validity,
   mandatory-field population, economic/field-mapping mismatch, and unresolved rejects. Each
   fired exception returns its evidence rows and citations.
3. **Assemble evidence** — for each exception, attach the specific report and/or source rows
   and the rule/threshold it failed, with citations.
4. **Suggest priority** — map the exception set to a remediation band
   (Clean / Review / High / Blocking) per the documented deterministic mapping. This is a
   triage suggestion for a human, explicitly **not** a compliance determination.
5. **Write the pack** — plain-language explanation per exception + evidence + suggested
   priority + the **false-positive checks** to run before escalating + `not_evaluable` gaps.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py)
after. The output check confirms: every exception has evidence + citation, every exception
code is recognized, the priority maps deterministically from the exception codes, no
determination/report-action language is present, the standing disclaimer is present, and
false-positive checks are included when any exception fired. **Fail closed** on any miss.

## Human approval
`external-delivery`: human review is required before the exception pack is delivered to
compliance or written to the reporting case / system of record. No approval is needed for
the analyst's own read. The skill never submits, amends, cancels, or suppresses a report and
never records a compliance determination.

## Failure handling
- **No matchable population** (no `transaction_ref` in both sides) → report that
  reconciliation/timeliness could not run; do not imply the batch is clean.
- **Missing timestamps** → timeliness is reported as `not_evaluable`; never assert a report
  is on time or late without the timestamps to prove it.
- **Missing economic value on a side** → that field's reconciliation is `not_evaluable`;
  do not treat an absent value as a match.
- **Ambiguous / duplicate `transaction_ref`** → surface the ambiguity; do not guess the pair.
- **Stale reference data or config** → cite the version used; if the effective version is
  uncertain, fail closed and ask.
- **Tool timeout** → return the exceptions computed so far with a clear "incomplete" flag and
  the unprocessed remainder.

## Output contract
1. **Summary** — regime, as-of, population counts (reportable / submitted / matched), and the
   suggested remediation priority.
2. **Exceptions** — per exception: code, plain-language reason, severity, and cited evidence
   (source and/or report rows).
3. **Not evaluable** — checks that could not run and why (missing timestamps, absent values).
4. **False-positive checks** — the items to verify before escalating (exemption/waiver,
   timezone/cut-off normalization, correction-in-flight, source correctness, effective
   reference-data snapshot).
5. **Machine-readable** — exceptions + evidence + `qc_id` for downstream skills.
6. **Standing disclaimer** — "Quality-control findings only; not a compliance determination.
   No regulatory report has been submitted, amended, cancelled, or suppressed."
See [references/controls.md](references/controls.md).

## Privacy and records
Transaction reporting data includes counterparty LEIs and may include national/client
identifiers (PII). Minimize client identifiers in output to what evidences an exception;
mask or reference rather than reproduce full national IDs. Retain the QC pack + citations +
config version per records policy; log the read and any external-delivery approval. Never
exfiltrate reporting or client data.

## Gotchas
- **An exception is not a breach.** A high exception count justifies remediation *priority*,
  never a compliance conclusion or a regulator submission — those are human decisions.
- **Reportability is a source attribute, not a guess.** Over/under-reporting is judged from
  the `reportable` flag on the source of record; do not infer that a transaction "should not"
  have been reported.
- **Timezones and cut-offs cause false lates.** Normalize execution and submission timestamps
  to the regime's reporting clock before treating a report as late.
- **The source of record can be wrong too.** A mismatch means the report and source disagree;
  it does not by itself prove the *report* is the defective side — say which is which only
  from evidence, and let the human adjudicate.
- **Config is a versioned contract.** Deadlines, required fields, and identifier formats come
  from the versioned config, never hard-coded to a single desk or day.
- **Corrections in flight** can look like unresolved rejects or missing reports; the
  false-positive checks exist to catch this before escalation.
