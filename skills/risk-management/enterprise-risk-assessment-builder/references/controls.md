# Controls — enterprise-risk-assessment-builder

- **Risk tier:** R3 — regulated/control decision support. **Action mode:** Draft-only; no
  system-of-record change. The skill produces a **draft** enterprise risk assessment for
  human adjudication; it stages nothing for execution and writes no system of record.
- **Human approval:** `required` — before any residual rating is accepted, the assessment is
  approved/finalized, a risk is closed, an attestation is signed, or anything is filed or
  written to the risk register.

## Prohibited (fail closed)

- **Accepting a residual rating** or **approving/finalizing** the assessment.
- **Closing a risk**, **signing an attestation**, or recording a management **sign-off**.
- **Filing** with a regulator or **writing the risk register / GRC system of record**.
- **Taking control credit** for a control that is **not tested** or **not evidenced**.
- **Unsupported assertions** — any rating, effectiveness claim, or KRI value without a cited
  source.
- **Personalized advice** or a binding risk decision presented as final.

## Case states (this skill may set only these)

`draft-for-review` (default) and `needs-evidence` (a risk whose residual cannot take control
credit because a linked control is untested/unevidenced, or that otherwise lacks required
evidence). It may **not** set `approved`, `accepted`, `final`, `closed`, `signed`, or
`filed`. Every approval slot is emitted `pending`.

## Required output screens (`scripts/validate_output.py`)

- **Template fidelity** — all ten required sections present (Scope & Basis; Risk Inventory;
  Inherent Risk Assessment; Control Environment; Residual Risk & Appetite; Key Risk
  Indicators; Treatment Actions; Evidence Register; Limitations & Assumptions; Approvals &
  Attestations).
- **Residual tie-out** — residual band equals the deterministic mapping (inherent band minus
  recorded control credit); over-appetite flag consistent with residual vs appetite.
- **No unsupported assertions** — control credit only where a credited control is `proven`
  **and** evidenced.
- **Treatment coverage** — every over-appetite residual records a treatment action.
- **No decision/closure/filing language** (regex: "risk accepted", "assessment approved/
  finalized", "signed off", "risk closed", "filed with", "submitted to the regulator",
  "written to the risk register", "no further action required").
- **Approvals recorded & pending** — the three required roles present; none pre-granted.
- **Standing note present.**

Fail closed on any miss.

## Segregation of duties

Drafting the assessment (this skill / 1st line) is distinct from 2nd-line challenge
(Enterprise Risk Management) and from Risk Committee / CRO approval. The same person must not
both draft and approve. The skill never performs the reviewer's or approver's role.

## Data classification, privacy, records

- **Confidential.** Minimize customer/employee identifiers; the assessment operates on risk,
  control, and indicator metadata, not raw customer records.
- Retain the draft, its inputs, scoring/appetite/template versions, and citations per the
  firm's records schedule; log the preparer identity and every source read.
- Jurisdiction: US default; additional jurisdiction packs (appetite, taxonomy, regulatory
  overlays) configured per deployment.
