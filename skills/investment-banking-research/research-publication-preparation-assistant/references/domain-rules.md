# Domain Rules — research-publication-preparation-assistant

Compliance configs govern (versioned). Orientation: verify a note is *prepared* for supervisory
and compliance review. Checks and flags only — never publish, approve, or rate.

## Checks (deterministic)
| Check | Rule | Gap/flag when |
| ----- | ---- | ------------- |
| `disclosure_completeness` | Every required disclosure is present | A required disclosure is missing |
| `rating_validity` | The note's rating is in `rating_scale` | Rating not in the scale |
| `rating_target_consistency` | Rating change direction agrees with target change direction | Upgrade with a target cut, or downgrade with a target raise |
| `restricted_list` | The ticker is not on the restricted list | Ticker is restricted → hard-stop flag, route to compliance |
| `checklist_completeness` | Every pre-publication checklist item is present | A required item is missing |

Rating direction rank (documented): `Sell < Hold < Buy` (configurable). Configs are **versioned
contracts**; scales/lists are never guessed.

## Disposition mapping (review-only)
- `ready-for-compliance-review` — no gaps or flags (a restricted flag always blocks this).
- `gaps-for-review` — ≥1 gap or flag. A triage suggestion for the human, **not** a publication
  decision.

## Hard boundaries (fail closed)
- Never publish/distribute/approve; never set/determine/change the rating or target; never clear a
  restricted ticker; never assume a missing disclosure is present.
