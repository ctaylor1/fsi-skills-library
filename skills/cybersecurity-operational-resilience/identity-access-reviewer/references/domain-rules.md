# Domain Rules — identity-access-reviewer

Explainable access-review **findings** and how they map to a **review-priority band** and to
**staged revocation candidates**. Thresholds and the SoD ruleset are configuration (versioned,
owned by the IAM control owner / access-governance team), not hard-coded judgments, and are
never tuned to an individual. Orientation references: the firm's logical-access and SoD
standards, NIST SP 800-53 AC family, and applicable SOX/FFIEC access-control expectations take
precedence. See [source-map.md](source-map.md) for the config contract.

## Finding taxonomy

| Finding | Fires when (default config) | Evidence attached | Escalator |
| ------- | --------------------------- | ----------------- | :-------: |
| `sod_conflict` | A user holds both entitlements of a toxic pair in `config.sod_rules` (across any of their accounts) | The user, the two entitlements + grant IDs | yes |
| `dormant_privileged` | A **privileged** grant sits on an account inactive ≥ `dormancy_days` (default 90); missing `last_login` counts as dormant | Grant + account + gap days | yes |
| `inactive_account` | Any account inactive ≥ `inactivity_days` (default 90); missing `last_login` counts as inactive | Account + gap days | no |
| `orphaned_account` | Account owner is `terminated` in HR, or the `user_id` is absent from the identity roster | Account + owner status | yes |
| `unapproved_privileged` | A privileged grant has no `approval_ref` | Grant | no |
| `stale_certification` | A grant's `last_certified` is older than `certification_interval_days` (default 365) or absent | Grant + last_certified | no |
| `privileged_without_mfa` | A privileged grant sits on an account with `mfa_enabled == false` | Grant + account | yes |
| `over_entitled` | An account holds ≥ `max_entitlements` grants (default 15) | Account + count | no |

Findings are **independent and additive**; each that fires is reported with its own evidence.
There is no opaque composite "risk score". A finding that cannot be evaluated for lack of data
(e.g. no `sod_rules` configured) is reported under `not_evaluable`, never silently dropped.

## Priority mapping (deterministic, documented)

Escalators = `{sod_conflict, dormant_privileged, orphaned_account, privileged_without_mfa}`.

| Suggested band | Rule |
| -------------- | ---- |
| **Informational** | 0 findings fired |
| **Review** | 1–2 findings fired, none an escalator |
| **Elevated** | ≥ 3 findings fired, OR any escalator fired |

Priority is a **triage suggestion for a human control owner**. It is not an access decision
and it never triggers an access change.

## Staged revocation candidates

For each escalator/actionable finding the engine stages a **candidate** for approval
(deduplicated by `grant_id`), each carrying `status: staged_for_approval` and the
`related_finding`:

- `sod_conflict` → stage one side of the toxic pair (the privileged side when only one is
  privileged) for the owner to choose.
- `dormant_privileged` → stage the dormant privileged grant.
- `unapproved_privileged` → stage the unapproved privileged grant.
- `orphaned_account` → stage every grant on the orphaned account.

A staged candidate is a **recommendation record**, never an executed change. The control owner
adjudicates; IAM operations executes any approved removal through the provisioning process.

## Hard boundaries (fail closed)

- Never **decide** access (grant/deny/approve/reject) or state that access is approved/denied.
- Never **execute** a revocation, disable an account, deprovision, or remove a grant.
- Never **certify / recertify** an entitlement, sign an attestation, or close the review.
- Never tune thresholds or SoD rules to the individual; use only the versioned config.
- Describe a toxic pair or a dormant privileged grant as a **control exception with evidence**,
  never as proven misuse or intent.

## Review-context prompts (always include when any finding fired)

Approved standing exception or break-glass account; a recent role change / transfer still in a
grace period; a service or shared account operating by design (verify owner + credential
rotation); a planned leave of absence explaining inactivity; a certification in progress but
not yet recorded. The pack must invite the control owner to weigh these before adjudicating.
