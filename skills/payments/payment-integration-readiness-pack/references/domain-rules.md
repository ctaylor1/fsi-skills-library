# Domain Rules — payment-integration-readiness-pack

The approved readiness checklist governs (versioned). Orientation: a payment integration is
ready when every required item — especially PCI-scope gate items — is attested with evidence.

## Checks (deterministic)
| Check | Rule | Gap when |
| ----- | ---- | -------- |
| `attested` | Every `required_item` has an attestation with status `attested` and an evidence_ref | Status is `not_attested`, missing, or `attested` without evidence |
| `na_justified` | An item marked `na` carries a non-empty justification | N/A with no justification |
| `gate_item` | Gate items (e.g. `pci_scope`) must be `attested` (never `na`) | A gate item is not attested |
| `readiness_score` | `attested_required / total_required` | Reported for review; a score < 1.0 always yields gaps |

Config (`required_items`, `gate_items`) is a **versioned contract**; the output records the
version. Thresholds/gates are policy, never guessed.

## Disposition mapping (review-only)
- `ready-for-review` — no gaps (the manager still reviews and decides go-live).
- `gaps-for-review` — ≥1 gap. A triage suggestion for a human reviewer, **not** a go-live decision.

## Hard boundaries (fail closed)
- Never approve go-live, clear a launch, or declare production-readiness.
- Never assume a missing attestation is satisfied; never accept an unjustified N/A; never waive a
  gate item.
