# Domain Rules — market-window-readiness-pack

The approved launch checklist governs (versioned). Orientation: a deal is launch-*ready* when
every required item — especially gate items (due diligence, board approval) — is attested with
evidence. Readiness is not a launch decision, and it says nothing about market timing.

## Checks (deterministic)
| Check | Rule | Gap when |
| ----- | ---- | -------- |
| `attested` | Every `required_item` has status `attested` with an evidence_ref | Status is `not_attested`, missing, or `attested` without evidence |
| `na_justified` | An item marked `na` carries a non-empty justification | N/A with no justification |
| `gate_item` | Gate items must be `attested` (never `na`) | A gate item is not attested |
| `readiness_score` | `attested_required / total_required` | Reported for review; a score < 1.0 always yields gaps |

Config (`required_items`, `gate_items`) is a **versioned contract**; the output records the
version. Gates/thresholds are policy, never guessed.

## Disposition mapping (review-only)
- `ready-for-review` — no gaps (the banker still decides launch and timing).
- `gaps-for-review` — ≥1 gap. A triage suggestion for a human reviewer, **not** a launch decision.

## Hard boundaries (fail closed)
- Never decide/approve launch, clear pricing, or give market-timing advice.
- Never assume a missing attestation is satisfied; never accept an unjustified N/A; never waive a
  gate item.
