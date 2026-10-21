# Adjacent-Skill Handoffs — model-roll-forward-auditor

## Version 0.2.0 contract

Retained through Phase 1 until shared-check and future reviewer parity is established. This is a supplied-balance continuity checker only: it does not read/update a workbook, compare formulas, assess assumptions or provide independent assurance. Require unique line items, model version IDs, explicit balances (null means structural break) and nonnegative explicit tolerances. A tied subset does not establish model correctness.


Produces a cited roll-forward continuity-audit packet (`audit_id`) and stops. It does not approve
the model or opine on value.

## Downstream (route the human/analyst to)
| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `document-version-comparator` | A document/version content diff is needed | doc refs |
| `issuer-capital-structure-mapper` | The debt-stack context is needed | company id |
| `research-publication-preparation-assistant` | The model feeds a research note pre-publication | model id |

## Upstream (may call this skill)
Deal-execution and analyst workflows may request a roll-forward audit after rolling the model.
This skill is interactive (`aws-fsi-scheduled-agent: no`).

## Duplicate-execution prevention
- This skill only **checks continuity and evidences breaks**; it never approves the model or
  opines on value — those belong to the deal team.
- Downstream reuses the `audit_id` packet rather than recomputing.
