# Controls — beneficial-ownership-verifier

- **Risk tier:** R3 — regulated/control decision support. **Action mode:** Read-only analysis.
- **Human approval:** `required` — a human KYC analyst must adjudicate before any regulated
  decision, approval, closure, or filing. This skill only recommends and evidences.

## Prohibited (fail closed)

- No **beneficial-ownership determination** — never state that a person "is" / "is confirmed"
  / "is verified" as a beneficial owner. The skill identifies *candidate* UBOs for adjudication.
- No **onboarding decision** — never approve, reject, clear, or onboard the customer/entity.
- No **case closure** and no **filing** (BOI report, SAR) — route to the human adjudicator and
  the appropriate draft-only skill.
- No **identity verification as an authoritative decision** — document freshness is evidenced,
  not adjudicated.
- No **threshold / control-prong tuning to the entity** — use only the versioned jurisdiction
  config.
- No **system-of-record write** or case-state change of any kind.

## Required output screens (`scripts/validate_output.py`)

- Every identified UBO (ownership prong + control prong) has ≥ 1 cited evidence row.
- `readiness` equals the deterministic mapping from the gap set (see `domain-rules.md`) and is
  one of `Complete-for-review` / `Remediation-needed` / `Escalate`.
- No decision/closure/filing/approval language (regex screen: "approved for onboarding",
  "close the case", "file the BOI/SAR report", "beneficial ownership is confirmed/verified",
  "identity is verified", etc.). The standing disclaimer is excluded from the scan.
- Standing disclaimer present verbatim: "Verification evidence and recommendations only; not a
  beneficial-ownership determination or KYC/onboarding approval. No case has been approved,
  closed, or filed, and no system of record has been updated. Human adjudication is required."

A non-compliant pack (decision/filing language and/or a wrong readiness band) **fails closed**
with a non-zero exit (see `evals/files/pack_with_decision.json`).

## Tipping-off / conduct

- Beneficial-ownership work may relate to SAR activity — observe **tipping-off** controls.
  Escalation, gap, and filing considerations stay internal to compliance and never appear in
  any customer-facing output.
- Describe ownership factually; do not impute intent or wrongdoing to any owner.

## Data classification, privacy, records

- **Restricted (AML/BSA — SAR confidentiality; tipping-off controls).** Minimize personal
  data to what evidences an identified UBO or gap; mask identifiers where possible.
- Retain the verification pack + citations + `config_version` per records policy; log the read
  and any adjudication.

## Reproducibility

`verification_id` binds the pack to the exact inputs, as-of date, and **config version**;
re-running with the same inputs and config reproduces the computation, the identified UBOs,
the gap set, and the readiness band.
