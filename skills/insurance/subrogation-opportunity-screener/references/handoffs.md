# Adjacent-Skill Handoffs — subrogation-opportunity-screener

This skill produces a cited **recovery-opportunity screening / referral pack** (`screening_id`)
and stops. It does not pursue recovery, issue a demand, file, negotiate, waive, or close.

## Downstream (route the human/specialist to)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `claims-fraud-referral-assistant` | Screening surfaces fraud indicators (staged loss, inconsistent damage/injury, misrepresentation) alongside recovery potential | `screening_id` + evidence |
| `reserving-analysis-assistant` | Anticipated recovery should feed reserve development / salvage-and-subrogation credits | `screening_id` + referral economics |
| `claims-file-reviewer` | A full file review (documentation, chronology, reserve support) is needed before referral | claim_id + open issues |
| `reinsurance-treaty-interpreter` | Recovery may flow to reinsurers and a treaty recoverability/reporting question arises | claim_id + recovery amounts |

**Human / licensed-specialist handoff (primary):** the actual subrogation decision — whether to
pursue, issue a demand, file suit, negotiate, or waive/release — belongs to a **licensed
recovery/subrogation specialist or counsel**, not to any skill. This screener hands that person a
source-linked referral with the recovery signals, the economics, and the limitation posture, and
stops. Confirm the controlling limitation period with counsel; the screen only reports the
diaried date.

## Upstream (may route to this skill)

`claims-triage-assistant` and `claims-file-reviewer` may flag a claim with apparent third-party
liability and route it here for a recovery screen. A scheduled monitor is **not** used
(`aws-fsi-scheduled-agent: no`); this skill is interactive.

## Duplicate-execution prevention

- This skill computes and evidences **recovery signals + a triage band** only; it must not reach
  a subrogation, liability, or limitation determination, contact the third party, or take/recommend
  a recovery action — those belong to the human specialist and downstream skills.
- Before referring, it checks `recovery_not_waived` (waiver absent and no prior/open recovery) so
  it does not refer a recovery that is already waived or being pursued elsewhere.
- Downstream skills reuse the `screening_id` evidence rather than recomputing signals.
