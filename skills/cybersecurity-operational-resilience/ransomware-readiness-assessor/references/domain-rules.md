# Domain Rules — ransomware-readiness-assessor

Explainable ransomware-readiness **control gaps** and how they map to a **suggested
remediation-review priority band** and to **staged remediation candidates**. Thresholds and
intervals are configuration (versioned, owned by the CISO office / operational-resilience team),
not hard-coded judgments, and never tuned to the assessed entity. Orientation references: NIST
Cybersecurity Framework 2.0, CISA #StopRansomware guidance, NIST SP 800-53 CP (contingency
planning) and backup controls, and applicable FFIEC / operational-resilience expectations take
precedence. See [source-map.md](source-map.md) for the config contract.

## Gap taxonomy

| Gap (finding) | Domain | Fires when (default config) | Evidence attached | Escalator |
| ------------- | ------ | --------------------------- | ----------------- | :-------: |
| `privileged_mfa_gap` | identity | `privileged_with_mfa / privileged_total` < `min_privileged_mfa_ratio` (default 1.0) | Counts + ratio | yes |
| `admin_tiering_gap` | identity | `admin_tiering` is not true | Tiering flag | no |
| `segmentation_gap` | segmentation | A critical service `segmented` is not true (missing = gap, conservative) | Service + tier | yes |
| `backup_coverage_gap` | backups | A critical service `backup.exists` is not true (missing = gap) | Service + tier | yes |
| `backup_immutability_gap` | backups | Backup exists but neither `immutable` nor `offline_copy` is true | Service + backup flags | yes |
| `restore_test_stale` | recovery | `last_restore_test` absent or older than `restore_test_interval_days` (default 180) | Service + last test + age | yes |
| `detection_coverage_gap` | detection | A critical service `detection_coverage` < `min_detection_coverage` (default 0.9) | Service + coverage | no |
| `dependency_mapping_gap` | critical-service dependencies | A critical service `dependency_map` is not true (missing = gap) | Service + tier | no |
| `third_party_resilience_gap` | third parties | A **critical** vendor lacks `resilience_evidence` or `recovery_commitment` | Vendor + missing items | no |
| `exercise_overdue` | exercises | No relevant exercise (`ransomware_tabletop`/`ir`/`backup_restore`) within `exercise_interval_days` (default 365) | Latest relevant exercise | yes |
| `comms_readiness_gap` | communications | No `out_of_band` channel, or crisis plan not tested within `comms_test_interval_days` (default 365) | Comms flags + last test | no |

Gaps are **independent and additive**; each that fires is reported with its own evidence. There
is no opaque composite "readiness score". A gap that cannot be evaluated for lack of data (e.g.
no `identity` posture, no `critical_services`, a service missing `detection_coverage`) is reported
under `not_evaluable`, never silently dropped or assumed compliant.

## Conservative treatment of missing evidence

Ransomware readiness fails safe toward the defender: **absence of positive control evidence is a
gap, not a pass.** A missing `segmented`, missing `backup`, missing `dependency_map`, or missing
`last_restore_test` fires the corresponding gap. A missing *measured value* that cannot be
compared (e.g. `detection_coverage` absent) is `not_evaluable` for that row — reported, never
inferred.

## Priority mapping (deterministic, documented)

Escalators = `{privileged_mfa_gap, segmentation_gap, backup_coverage_gap, backup_immutability_gap,
restore_test_stale, exercise_overdue}` — the controls that most directly determine whether the
organization can withstand and recover from a ransomware event.

| Suggested band | Rule |
| -------------- | ---- |
| **Informational** | 0 gaps fired |
| **Review** | 1–2 gaps fired, none an escalator |
| **Elevated** | ≥ 3 gaps fired, OR any escalator fired |

`suggested_priority` is a **triage suggestion for a human control owner**. It is not a readiness
decision, a readiness rating, or an attestation, and it never triggers a change.

## Staged remediation candidates

For each fired escalator/actionable gap the engine stages a **candidate** for approval
(deduplicated by `{finding}:{target}`), each carrying `status: staged_for_approval`, the
`related_finding`, and a plain-language `action`:

- `privileged_mfa_gap` → enforce phishing-resistant MFA on all privileged accounts.
- `segmentation_gap` → isolate/segment the critical service to contain lateral movement.
- `backup_coverage_gap` → establish a backup for the critical service.
- `backup_immutability_gap` → add an immutable or offline (air-gapped) backup copy.
- `restore_test_stale` → perform and evidence a full restore test within the interval.
- `exercise_overdue` → schedule and conduct a ransomware tabletop / IR exercise.

A staged candidate is a **recommendation record**, never an executed change. The control owner
adjudicates; the engineering/infrastructure teams execute any approved remediation through change
management.

## Hard boundaries (fail closed)

- Never **decide** readiness (certify/attest/assure) or state the org/service "is ransomware-ready".
- Never **accept risk** or state that a gap's residual risk is accepted.
- Never **execute** a remediation, enforce a control, or change configuration.
- Never **file** a report to a regulator or **close** the assessment.
- Never tune thresholds/intervals to the assessed entity; use only the versioned config.
- Describe a gap as a **control exception with evidence**, never as proven negligence or a
  prediction of compromise.

## Review-context prompts (always include when any gap fired)

A documented compensating control or accepted exception on file for a flagged gap; remediation
already in flight but not yet reflected in the extract; a critical service scheduled for
decommission/migration; backup immutability provided by an out-of-band vault not captured in the
extract; an exercise conducted but its after-action record not yet logged. The pack must invite
the control owner to weigh these before prioritizing.
