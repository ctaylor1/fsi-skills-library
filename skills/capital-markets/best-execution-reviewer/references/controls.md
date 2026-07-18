# Controls — best-execution-reviewer

- **Risk tier:** R3 — regulated / control decision support. **Action mode:** Read-only analysis.
- **Human approval:** `required` — the best-execution committee (and, for any regulatory step,
  a licensed compliance officer) must adjudicate before any determination, closure, remediation
  instruction, filing, or system-of-record change.

## Prohibited (fail closed)

- No **best-execution or compliance determination** — never state or imply that an execution,
  desk, or period **was / was not best execution**, **is compliant**, or **is / is not in
  breach**. Findings are evidence for the committee.
- No **case / exception closure or disposition** — never "close", "disposition as passed/
  cleared", or "no further action required".
- No **filing or amendment** — never file, amend, cancel, or self-report a regulatory report
  (RTS 27/28, Rule 605/606, or any regime), and never sign off / attest.
- No **remediation instruction** to a desk or venue routing change presented as an action taken.
- No **system-of-record write** to the committee log, case system, or OMS annotation.
- No **opaque scoring** presented as decisive; findings are explainable and evidenced, and the
  disposition is a deterministic triage suggestion, not a score.

## Required output screens (`scripts/validate_output.py`)

- Every fired finding has ≥ 1 cited evidence row, and every fired finding type is recognized.
- `suggested_disposition` equals the deterministic mapping from the fired-finding set
  (see domain-rules.md).
- No regulated **decision / closure / disposition / filing / attestation** language in the
  narrative, notes, or finding reasons (regex screen: "is compliant", "no breach",
  "we determine", "close the case", "no further action required", "sign off", "attest",
  "self-report to the regulator", "file … report with", etc.).
- Standing disclaimer present: "Best-execution review evidence only; not a best-execution or
  compliance determination. No case has been closed, no exception has been dispositioned, no
  filing has been made, and no system of record has been updated."
- False-positive prompts (`fp_checks`) included when any finding fired.

## Fairness / conduct

- Best execution is **multi-factor**; do not reduce it to a single price/bps number, and apply
  the client-class weighting from the versioned policy (retail vs professional).
- Describe execution outcomes factually; an **undocumented exception is a records finding**, not
  an allegation of misconduct — route conduct questions to the communications reviewer.

## Data classification, privacy, records

- **Highly Confidential (client NPI/PII possible).** Minimize client identifiers in output to
  what evidences a finding; mask/reference rather than reproduce account/client numbers.
- Retain the findings pack + citations + `policy_version` per records policy; log the read and
  any approval to deliver into the committee record.

## Reproducibility

`review_id` binds the output to the exact executions, benchmarks, and **policy version**;
re-running with the same inputs and policy reproduces the findings and the suggested
disposition. Escalation and any regulated decision are recorded by the human committee, not
by this skill.
