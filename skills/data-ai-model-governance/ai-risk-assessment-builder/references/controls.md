# Controls — ai-risk-assessment-builder

- **Risk tier:** R3 — regulated / control decision support. Evidence + recommendations with
  **mandatory human adjudication**. **Action mode:** Draft-only; no system-of-record change.
- **Human approval:** `required` — every residual rating, finding, and the go/no-go decision
  is reviewed and adjudicated by the accountable risk owner and the routed approver before any
  decision, acceptance, or deployment. Internal drafting may be reviewer-sampled.

## Prohibited (fail closed)

- **Approval, certification, risk acceptance, or deployment clearance** of the assessed
  system. The pack is a draft with a `pending` approval block; a human decides.
- **Final / binding risk determination.** The skill computes and recommends; it does not
  decide the residual tier or the go/no-go.
- **Closing, resolving, or waiving a finding**, or setting a finding to anything but `open`.
- **Unsupported / unapproved assertions** — any risk statement or finding not backed by a
  cited source; any control counted as effective without an evidence ref.
- **Fabricated or assumed controls / evidence.**
- **Personalized legal, investment, or compliance advice.**

## Pack / finding states (this skill may set only these)

Pack: `draft-assessment` (completed draft) | `needs-data` (incomplete intake). Approval:
`pending` only. Findings: `open` only. It may **not** set `approved`, `certified`,
`accepted`, `closed`, `resolved`, `waived`, or `cleared`.

## Required output screens (`scripts/validate_output.py`)

- **Template fidelity:** all ten required domains present — `data`, `model`, `fairness`,
  `explainability`, `security`, `privacy`, `third_party`, `human_oversight`, `resilience`,
  `monitoring`.
- **Source mapping:** every domain carries at least one citation; every finding carries a
  source ref and a recommended remediation (no unsupported assertion).
- **Residual tie-out:** each domain's declared `residual_band` equals the deterministic
  matrix result; a `High`-residual domain carries an open finding; the
  `overall_residual_rating` equals the highest domain residual.
- **Approval discipline (R3):** `approval.status == pending`, `adjudication_required` true,
  and `required_approvers` non-empty and consistent with the overall rating.
- **No autonomous-decision language** (regex): `approved for production/deployment`,
  `cleared to deploy`, `no (further) human review required`, `we certify`, `risk accepted`,
  `final risk determination`, `sign-off complete`, `auto-approved`, `green-lit`, plus
  finding-closure phrases (`finding closed/resolved/remediated`, `no action required`).
- Standing note present: the draft-only / no-approval / no-final-determination disclaimer.

## Segregation of duties

Assessment drafting is distinct from independent validation and from the approval decision.
The same person/skill must not both draft the assessment and adjudicate/approve it.

## Data classification, privacy, records

- **Confidential.** The pack describes systems and controls; reference model/data assets by
  catalog ID rather than copying sensitive datasets. Customer NPI/PII stays in the owning
  system's controls, not in this pack.
- Retain the draft pack, `framework_version`, citations, and reviewer sign-off with the
  assessment record; log every read and every pack produced with the reviewer identity.
