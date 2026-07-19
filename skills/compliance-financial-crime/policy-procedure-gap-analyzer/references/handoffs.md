# Adjacent-Skill Handoffs — policy-procedure-gap-analyzer

This skill produces a cited **gap-analysis pack** (`analysis_id`) and stops. It does not
remediate, draft the corrected policy, attest, file, or close a finding.

## Upstream (may feed this skill)

| Upstream skill | What it hands over | Why here |
| -------------- | ------------------ | -------- |
| `regulatory-change-impact-analyzer` | A ruleset of changed/new obligations + effective dates | Determine which policies/procedures now have gaps or obsolete steps |
| `contract-obligation-extractor` | Extracted contractual/SLA obligations | Compare obligations against internal procedures for coverage gaps |

## Downstream (route the human/reviewer to)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `policy-document-assistant` | The reviewer decides to draft/rewrite the policy or procedure to remediate a gap | `analysis_id` + finding ids |
| `regulatory-exam-response-packager` | Findings feed an examination response or issue log | `analysis_id` + evidence |
| `audit-evidence-packager` | An `evidence_gap` finding needs an evidence artifact collected and indexed | control_id + requirement id |
| `risk-control-self-assessment-assistant` | Control gaps/conflicts feed an RCSA design/effectiveness assessment | finding set + severities |
| `enterprise-risk-assessment-builder` | Aggregate gaps roll up into an enterprise risk view | severity_counts + findings |

For anything requiring a **compliance judgment, remediation sign-off, attestation, or a
regulatory filing**, route to the accountable **compliance officer / policy owner /
internal audit** — those are human decisions, not another skill. Never invent a skill to
"approve" or "close" a finding.

## Duplicate-execution prevention

- This skill computes and evidences **findings only**; it must not reach a compliance
  disposition, close a finding, draft the remediated policy, or file — those belong to the
  human reviewer and the downstream skills.
- Downstream skills reuse the `analysis_id` findings and evidence rather than recomputing the
  gap analysis. A scheduled monitor is **not** used here (`aws-fsi-scheduled-agent: no`);
  continuous obligation monitoring is `regulatory-change-impact-analyzer`'s role.
