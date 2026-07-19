# Controls — operational-resilience-scenario-tester

- **Risk tier:** R3 — regulated / control decision support. **Action mode:** Read-only analysis.
- **Human approval:** `required` — a human adjudicator (accountable resilience owner / SMF)
  must review before any resilience conclusion, self-assessment sign-off, regulatory filing,
  register update, case closure, or system-of-record change. The skill itself only produces
  evidence and a suggested disposition.

## Prohibited (fail closed)

- No statement that the firm or service **is compliant / non-compliant**, **is resilient**,
  or **can/will remain within impact tolerance** — those are human adjudications, not engine
  outputs.
- No **self-assessment sign-off**, **attestation**, or **board/SMF approval** language.
- No **regulatory filing or submission** (report, return, notification to a regulator) and no
  **register update** — route to the `operational-resilience-reporter` and a human.
- No **case / exercise / finding closure**; lessons stay `open_for_human_adjudication`.
- No tuning of the rubric or tolerances to manufacture a `within` result; versioned config
  only, effective-dated to `as_of`.
- No **live incident response, containment, or customer action** — this skill designs and
  documents *tests*, not real-incident operations.

## Required output screens (`scripts/validate_output.py`)

- Every scenario with an evaluable tolerance outcome has >= 1 recovery-evidence row and >= 1
  cited evidence row.
- Every recorded response decision is complete (`owner_role` + `timestamp` + `evidence_ref`);
  no `decision_gaps`.
- `suggested_disposition` equals the deterministic mapping from the scenario set
  (Escalate / Review / Informational — see domain-rules.md).
- No prohibited conclusion language (regex screen: `we attest`, `sign(ed) off`,
  `fully compliant`, `is/are/remain compliant`, `non-compliant`, `meets all obligations`,
  `no further action required`, `file the regulatory report`, `submit to the regulator`,
  `close the case/exercise`, `the service is resilient`, `self-assessment approved`,
  `board approved`, `we can/will remain within impact tolerances`, etc.).
- Standing disclaimer present (must state **human adjudication is required**).
- `remediation_actions` present whenever any breach or high-severity lesson exists.

Fail closed on any miss — a bad pack (see `evals/files/pack_noncompliant.json`) exits 1.

## Separation of duties

- **Design/test evidence (this skill)** is separate from **regulatory reporting / registers**
  (`operational-resilience-reporter`) and from **live incident coordination**
  (`cyber-incident-response-coordinator`). Each has distinct entitlements; this skill holds
  none of the write/submit permissions.

## Data classification, privacy, records

- **Confidential (security-sensitive).** Scenario narratives, dependency maps, and recovery
  telemetry can reveal exploitable weaknesses — minimize detail to what evidences a finding.
- Retain the test pack + citations + `config_version` per records policy; log the read and
  the human adjudication decision. Do not exfiltrate dependency or vulnerability detail.

## Reproducibility

`test_id` binds the pack to the exact inputs, tolerances in force at `as_of`, and
`config_version`; re-running the same inputs and config reproduces the outcomes and the
suggested disposition.
