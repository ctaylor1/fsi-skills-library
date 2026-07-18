# Changelog — subrogation-opportunity-screener

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `new`).

- **Scope:** explainable subrogation-recovery signals + cited evidence + referral economics +
  suggested screening band (Refer / Review / No-Action). Read-only; no subrogation, liability, or
  limitation determination, and no recovery action.
- **Signals (deterministic):** third-party liability indicated, recovery above floor, limitation
  window open, supporting evidence present, recovery not waived, collectible responsible party,
  positive expected recovery — each explainable and evidenced (see
  `scripts/calculate_or_transform.py`).
- **Referral economics:** recovery base × liability share × collectibility factor − pursuit cost =
  net expected recovery (triage economics, not a promise of recovery).
- **Controls:** R2; hard boundary against subrogation/liability/limitation determination and any
  recovery action (demand, filing, lien, negotiation, waiver, release, closure); versioned-config
  floors/factors only; time-critical limitation safeguard (never let a live window lapse silently);
  counter-consideration prompts required; `external-delivery` approval.
- **Scripts:** `validate_input` (claim schema, limitation/evidence/collectibility evaluability
  warnings), signal + economics engine, `validate_output` (evidence/citation completeness,
  deterministic band tie-out, determination/action-language screen, disclaimer, counter-considerations).
- **Evaluations:** trigger/routing, golden Refer case, missing-limitation and waived-recovery edges,
  deterministic script checks, no-determination safety + injection, external-delivery authorization.
- **Handoffs:** downstream to `claims-fraud-referral-assistant`, `reserving-analysis-assistant`,
  `claims-file-reviewer`, `reinsurance-treaty-interpreter`; upstream from `claims-triage-assistant`
  and `claims-file-reviewer`; the subrogation decision itself routes to a licensed recovery
  specialist / counsel.

### Pending before release
- Domain SME (recovery/subrogation) + control-owner blind review; legal review of the limitation
  safeguard and no-determination language.
- Confirm the versioned floor/factor/limitation config source and its owner, and the
  jurisdiction-specific limitation-rules pack.
- Wire read-only MCP integrations (claims, policy, recovery ledger, limitation rules, party records,
  config) at deployment.
