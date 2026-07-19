# Controls — cyber-incident-response-coordinator

- **Risk tier:** R3 — regulated/control decision support. **Action mode:** Read-only analysis.
- **Human approval:** `required` — before any regulated decision, severity classification,
  notification/filing, customer commitment, incident closure, or system-of-record change. The
  skill produces a coordination record with recommendations and evidence; humans decide and act.

## Prohibited (fail closed)

- No **regulated decision or determination**: official severity, "notification is/ is not
  required", root-cause attribution as fact, threat-actor attribution as fact, or any
  customer/regulator commitment.
- No **incident closure** or `resolved-final`/`closed`/`filed`/`reported` record state.
- No **filing or submission**: breach notification, regulatory operational-resilience report,
  SAR, or law-enforcement referral — route to the human/adjacent skill.
- No **response action or staging**: revoke, isolate, block, quarantine, patch, or restore —
  the coordinator tracks these; the entitled technical team executes them.
- No **decision marked adjudicated** without a named human `decided_by`.

## Required output screens (`scripts/validate_output.py`)

- No autonomous decision/closure/filing/binding-classification language (regex screen over
  narrative, notes, decision text, post-incident actions, and reminder text).
- No self-attributed **executed response action** language over the same text
  (revoke/isolate/patch/restore/block/quarantine/contain/disable and "containment/eradication/
  recovery is complete") — the coordinator tracks these; the entitled technical team executes them.
- `record_status` is not a closed/filed/reported/submitted state.
- Every terminal decision (adjudicated/approved/rejected) names a human `decided_by`.
- `severity_suggested` equals the deterministic mapping recomputed from the `impact` block.
- Every evidence item and every chronology entry carries a `source_ref` (citability).
- Standing disclaimer present: "Coordination record only; recommendations and evidence for
  human adjudication. No regulated decision, severity classification, incident closure,
  regulatory filing, or system-of-record write has been performed by this skill."

Fail closed on any miss — the pack is not presentable until it passes.

## Conduct / integrity

- Preserve chain of custody: never alter evidence; record source_ref, hash, and custody.
- Attribute conclusions to the human adjudicator; describe facts, not intent or blame.
- Do not speculate on attribution, root cause, or legal exposure as fact.

## Data classification, privacy, records

- **Confidential (security-sensitive).** Minimize sensitive detail (credentials, secrets,
  exploit specifics, raw customer records) to what the coordination record requires; reference
  evidence by `source_ref` rather than copying payloads.
- Retain the coordination record + citations + config version per records policy; log reads and
  any human approval captured at handoff. Never exfiltrate incident data.

## Reproducibility

`coordination_id` binds the output to the exact inputs, `as_of`, and **config version**;
re-running with the same inputs and config reproduces the pack deterministically.
