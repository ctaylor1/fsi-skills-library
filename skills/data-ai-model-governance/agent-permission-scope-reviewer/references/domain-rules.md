# Domain Rules — agent-permission-scope-reviewer

The versioned **least-privilege control ruleset** and how findings map to a **recommended
disposition band**. Thresholds and the rule set are configuration (owned by AI / Model Risk
Governance and IAM), not hard-coded judgments, and are recorded as `policy_version` on every
review. Orientation references: the firm's identity & access-management standard, the AI-
system risk policy, and NIST-style least-privilege / segregation-of-duties guidance take
precedence over anything here.

## The seven least-privilege dimensions

Every operation in the manifest is evaluated against: (1) **user need / justification**,
(2) **data classification**, (3) **least privilege / access mode**, (4) **approval gate**,
(5) **audit logging**, (6) **segregation of duties**, (7) **revocation / recertification**.

## Rule set (approved rule ids)

| Rule id | Dimension | Fires when (default config) | Severity |
| ------- | --------- | --------------------------- | -------- |
| `LP-NEED-01` | Need | Operation has no `declared_need` **or** no `justification_ref` | High |
| `LP-WRITE-NOGATE` | Approval gate | Effective write (`writes: true` or `access_mode: auto-write`) **and** `approval_gate` != `required` | Critical |
| `LP-CLASS-MODE` | Least privilege | `data_classification` in {`Highly Confidential`, `Restricted`} **and** `access_mode` == `auto-write` **and** `approval_gate` != `required` | Critical |
| `LP-CLASS-UNDECLARED` | Data classification | Operation's `data_classification` not present in the manifest's `data_classifications_in_scope` | High |
| `LP-LOG-OFF` | Logging | `logged` == false for a `Confidential`+ source (missing `logged` → `not_evaluable`) | High |
| `LP-SOD-COMBO` | Segregation | The agent holds an effective-write operation **and** an `approve` `segregation_group` operation together | High |
| `LP-REVOKE-MISSING` | Revocation | `revocation` absent, **or** `recert_days` > `max_recert` (default 365; 90 for `Restricted`) | Medium |
| `LP-ENV-PROD` | Least privilege | `environment` == `production` **and** effective write **and** `approval_gate` == `none` | High (escalates `LP-WRITE-NOGATE` context) |

Findings are **additive and independent** except `LP-SOD-COMBO`, which is evaluated at the
agent level. Each fired rule reports its own cited evidence. There is no opaque composite
"risk score"; severity comes from the rule, not from a black-box model.

## Severity → recommended disposition (deterministic, documented)

Severity rank: `Critical` (4) > `High` (3) > `Medium` (2) > `Low` (1).

| Recommended band | Rule |
| ---------------- | ---- |
| **Remediate-before-approval** | Any `Critical` finding present |
| **Conditional-adjudication-required** | Max severity is `High` (no Critical) |
| **Review-minor-findings** | Max severity is `Medium` or `Low` |
| **No-exceptions-adjudication-required** | No findings fired |

The recommended disposition is a **recommendation for a human adjudicator**. It is not an
access approval or denial and it never grants, revokes, or provisions an entitlement. Even
`No-exceptions-adjudication-required` still requires human adjudication before any grant.

## Not-evaluable handling

If an operation is missing a field a rule needs (e.g., no `data_classification`, no
`access_mode`), the affected rule is reported `not_evaluable` for that operation with the
reason — never treated as compliant by default (fail closed on assumptions).

## Hard boundaries (fail closed)

- Never render an **access decision** (approve/deny/clear) — recommend only.
- Never **grant, revoke, provision, de-provision, or rotate** an entitlement/credential.
- Never **close the review**, accept risk, or **file a waiver/exception**.
- Never invent a rule id or severity outside this approved set.
- Never assume a missing field is safe; mark it `not_evaluable`.
