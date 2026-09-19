# Domain rules — Claim Intake Preparation

- `receipt` is recorded only from a source reference and timezone-aware receipt timestamp. This describes supplied receipt evidence; the script never receives or sends a notice itself.
- Normalization carries supplied fields and uses exact, case-insensitive configured vocabulary mappings. Unknown mappings become null plus exceptions; dates require valid calendar dates.
- Submission requirements must be explicitly supplied for the claim type and versioned. Bundled auto/property rules are illustrative only. Unknown requirements, missing chronology or deadline evidence yield `Unknown`, never `Ready`.
- Missing support produces gaps; it cannot block notice receipt. Form presence, an accepted version and a supplied signed flag describe administrative completeness, not document authenticity or coverage.
- `prepared-for-review` requires recorded receipt, complete normalization/completeness and checked timeliness. Every other combination remains `exceptions-for-review`.
- `claim_package` must link to the same FNOL, policy and loss/report dates with reviewed assignment evidence. FNOL notification ID and assigned claim ID are separate identities.
- Legacy FNOL-only inputs remain accepted but report unknown completeness/timeliness. Legacy readiness-only inputs are not native inputs: wrap them in `claim_package` alongside a raw notice, vocabulary config and identity mapping. Unknown/missing fields remain unknown; do not manufacture a migration value.

## Scope limit
Controlled vocabulary and configured administrative submission checks; no universal jurisdiction checklist, legal deadline determination, source authentication or notice delivery.
