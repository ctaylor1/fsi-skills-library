# Adjacent-Skill Handoffs - network-rules-change-tracker

This skill is a **scheduled, read-only, alert-only** monitor. It produces a cited exception pack
(`run_id`) with per-alert `fingerprint`s and stops. It does **not** perform the full impact
analysis behind a confirmed change, compare procedures to find gaps, extract contract clauses,
adjudicate applicability, implement anything, or close items. Those are human payments compliance
/ product / operations actions, supported by the downstream skills below.

## Downstream (route the human reviewer to)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `regulatory-change-impact-analyzer` | A flagged change is confirmed in scope and needs full obligation-to-business/policies/controls/systems/data/training/owner impact analysis and implementation-decision tracking | `run_id` + bulletin + obligation ids |
| `policy-procedure-gap-analyzer` | The reviewer needs the changed rule compared against current procedures/operations to find gaps, conflicts, and obsolete steps | affected obligation(s) + impacted procedures |
| `contract-obligation-extractor` | The change touches a member/merchant agreement and clause-level obligations, dates, and renewal terms must be pulled | contract id(s) from the mapping |
| `audit-evidence-packager` | Implementation evidence for a change must be collected, indexed, and quality-checked for an audit | `run_id` + obligation + tracker refs |
| `regulatory-exam-response-packager` | A network-rule change becomes an examination or inquiry item needing a controlled response package | `run_id` + exception evidence |

Adjudication and implementation themselves - accepting an obligation, changing a
procedure/control/contract/system, marking a change done, granting a waiver, filing/attesting, or
closing the item - are performed by the accountable **payments product / operations / compliance
owner** through their entitled systems, never by this monitor. Where no catalog skill fits a
needed follow-up (e.g., a licensed regulatory-compliance opinion), the reviewer routes to the
appropriate **human specialist**; do not invent a skill.

## Upstream (what invokes this skill)

This is a **scheduled monitor** (`aws-fsi-scheduled-agent: read-only-monitoring`): it is triggered
by its schedule (or an ad-hoc reviewer run), not by another skill. A payments compliance, product,
or operations reviewer may also run it on demand against a specific network or bulletin.

## Duplicate-execution prevention

- The monitor computes and evidences **exceptions only**; it must not reach an adjudication,
  instruct an owner, or take/recommend an implementation - those belong to the human reviewer and
  the downstream skills.
- Cross-run **deduplication** (fingerprint vs `open_alerts`) prevents the same persistent gap
  (e.g., a still-overdue obligation) from being re-raised every scheduled run; still-open items
  remain visible as open rather than being silently cleared.
- Downstream skills consume the `run_id` / alert evidence rather than re-deriving obligations,
  effective dates, or mappings.
