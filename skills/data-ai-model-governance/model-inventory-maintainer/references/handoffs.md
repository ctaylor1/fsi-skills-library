# Adjacent-Skill Handoffs — model-inventory-maintainer

This skill produces a cited **inventory change proposal** (`proposal_id`) and stops. It does
not adjudicate, post to the inventory, approve a model, or close a finding.

## Upstream (may call this skill)

| Upstream skill | Supplies | Handoff artifact |
| -------------- | -------- | ---------------- |
| `ai-use-case-intake-classifier` | A newly intaken use case that needs an inventory record | record context + asset_kind |
| `ai-risk-assessment-builder` | Risk assessment for a model/agent to be inventoried | risk drivers + materiality factors |
| `model-change-impact-analyzer` | A proposed model change requiring an inventory update | current_record + proposed change |

## Downstream (route the human/adjudicator to)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `model-validation-assistant` | The record needs independent validation before approval | `proposal_id` + record_id |
| `model-risk-documenter` | Model documentation / SR 11-7 write-up is needed | record_id + inventory attributes |
| `data-lineage-documenter` | Lineage gaps found need full lineage authoring | reconciliation breaks (lineage) |
| `agent-permission-scope-reviewer` | An agent record's tool/permission scope needs review | record_id + declared scope |
| `agent-audit-trail-reviewer` | Agent behavior/audit evidence must be reviewed | record_id + agent-log refs |

## Duplicate-execution prevention

- This skill computes and evidences an **inventory change proposal only**; it must not
  adjudicate, post, approve, attest, or close — those belong to Model Risk Governance and the
  posting system of record.
- Downstream skills reuse the `proposal_id` and `record_id` rather than recomputing the
  inventory delta; validation/documentation is not duplicated here.
- The materiality tie-out and reconciliation are deterministic and reproducible from the same
  inputs and `config_version`, so re-runs do not create divergent proposals.
