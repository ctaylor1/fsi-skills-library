# Domain Rules — policy-procedure-gap-analyzer

Explainable gap-analysis **findings** and how they map to a **severity** and a triage
**remediation priority**. Comparators, the review-cycle window, and the severity/priority
mapping are configuration (versioned, owned by the compliance/policy-governance function),
not hard-coded judgments. The regulatory corpus and the firm's policy-governance standard
take precedence over anything here.

## Finding taxonomy

| Finding | Fires when | Evidence attached |
| ------- | ---------- | ----------------- |
| `coverage_gap` | An in-effect, applicable requirement has **no active** mapped policy/procedure control (retired controls do not count) | Requirement citation + obligation |
| `parameter_conflict` | An active control's numeric parameter **weakens** the requirement bound (see comparators) | Control value + requirement bound + both citations |
| `evidence_gap` | The requirement expects retained evidence but **no active mapped control records an evidence pointer** | Control ref + requirement id |
| `version_drift` | An active control references a **superseded requirement version** (obsolete steps likely) | Control version vs requirement version |
| `stale_review` | An active control's `last_reviewed` is older than `config.review_max_days` (default 365) | Last-reviewed date + threshold |

A requirement not yet in effect (`effective_date` > `as_of`) or marked not applicable is
reported as **informational**, never a gap. A requirement whose parameter kind has no
matching control parameter is reported as **not_evaluable**, never silently passed.

## Parameter comparators (deterministic)

| Requirement `parameter.kind` | Control `parameter.kind` | Conflict when |
| ---------------------------- | ------------------------ | ------------- |
| `retention_min_years` | `retention_years` | control value **<** requirement value |
| `reporting_threshold_max_usd` | `reporting_threshold_usd` | control value **>** requirement value (would miss reportable items) |
| `training_max_interval_months` | `training_interval_months` | control value **>** requirement value (less frequent than required) |

Comparators are additive across requirements; each is evaluated independently and cited. New
comparators are added to the versioned config, not invented per analysis.

## Severity mapping (deterministic, documented)

Base severity by finding type, then drop one band for `guidance`-level requirements:

| Finding type | Base severity |
| ------------ | ------------- |
| `coverage_gap`, `parameter_conflict` | High |
| `evidence_gap`, `version_drift` | Medium |
| `stale_review` | Low |

Guidance drop: High → Medium, Medium → Low, Low → Low. `stale_review` is control-level
(`criticality: control`) and stays Low.

## Remediation priority (deterministic)

| Priority | Rule |
| -------- | ---- |
| **Priority-1** | any High-severity finding |
| **Priority-2** | any Medium (no High) |
| **Priority-3** | only Low |
| **None** | no findings |

Priority is a **triage suggestion for a human reviewer** — it is not a compliance
determination, an attestation, or a remediation sign-off, and it never closes a finding or
authorizes a filing.

## Hard boundaries (fail closed)

- Never state or imply the firm/program **is compliant**, "fully compliant", or that "no
  gaps exist"; never **attest**, **certify**, or **sign off**. Findings are decision support.
- Never **close a finding**, mark **remediation complete**, or **file/submit** anything to a
  regulator or examiner — those are human/authorized-system actions (R3).
- Never rewrite the policy/procedure system of record; recommend the change and route it.
- Never tune comparators or the review window to make a gap disappear; use only the
  versioned config.
- If completeness, requirement version, applicability, or mapping is uncertain, stop and
  surface the gap rather than guessing.

## Reviewer prompts (always include)

Invite the reviewer to weigh: whether a mapped control operates in practice (documented vs
actual operations), whether an evidence pointer is current, whether a conflict reflects a
pending approved exception, and whether a guidance-level gap is an accepted risk. The pack
supports the human adjudication; it does not replace it.
