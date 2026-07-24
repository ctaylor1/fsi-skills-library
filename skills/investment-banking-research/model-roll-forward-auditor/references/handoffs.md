# Adjacent-Skill Handoffs — model-roll-forward-auditor

Produces a cited roll-forward continuity-audit packet (`audit_id`) and stops. It does not approve
the model or opine on value.

## Downstream (route the human/analyst to)
| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `financial-document-version-comparator` | A document/version content diff is needed | doc refs |
| `capital-structure-maturity-mapper` | The debt-stack context is needed | company id |
| `research-publication-preparation-assistant` | The model feeds a research note pre-publication | model id |

## Upstream (may call this skill)
Deal-execution and analyst workflows may request a roll-forward audit after rolling the model.
This skill is interactive (`aws-fsi-scheduled-agent: no`).

## Duplicate-execution prevention
- This skill only **checks continuity and evidences breaks**; it never approves the model or
  opines on value — those belong to the deal team.
- Downstream reuses the `audit_id` packet rather than recomputing.
