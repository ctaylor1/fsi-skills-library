# Changelog — conflicts-of-interest-reviewer

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `new`). R3 regulated
decision-support: findings, cited evidence, and recommendations with **mandatory human
adjudication** — the skill never clears, approves, waives, closes, or files.

- **Scope:** classify each disclosed item against a conflict taxonomy (outside business
  activity, personal financial interest, gifts/entertainment, personal relationship, personal
  trading/MNPI, dual-role/cross-side, related-party transaction, incentive misalignment,
  information barrier); name affected parties + incentive; check required disclosures,
  controls, and approvals; compute a deterministic residual-risk band with cited evidence.
- **Deterministic engine (`scripts/calculate_or_transform.py`):** inherent severity from type +
  magnitude thresholds; per-type required-control check (disclosure/control/approval); residual
  risk = inherent with one band of credit **only** when the full required set is evidenced and
  current; matter residual = max across findings; deterministic recommended review path.
- **Controls:** R3; hard boundary against clearance/approval/waiver, matter closure, filing,
  and any binding "no conflict"/insider-dealing determination; versioned-config thresholds
  only; tipping-off / SAR-confidentiality respected; mandatory human adjudication.
- **Scripts:** `validate_input` (matter schema, evaluability warnings), the conflict engine,
  `validate_output` (evidence/citation completeness, deterministic residual + review-path
  tie-out, prohibited-decision-language screen, disclaimer, mitigation prompts). Each has a
  `--selftest` over a bundled fixture. Python stdlib-only, self-contained, no live calls.
  `validate_output` **recomputes** each finding's `open_gap` and `residual_risk` from its own
  `inherent_severity` + disclosure/control/approval status (never trusting the self-reported
  band) so a pack that under-states an unmitigated conflict fails closed instead of routing to
  the lightest review path.
- **Evaluations:** trigger/routing, golden escalate case (`matter_example.json`), stale-
  disclosure edge, deterministic script checks, no-decision safety fail-closed on
  `review_with_decision.json` (expect exit 1), injection + adjudication authorization.
- **Handoffs:** downstream to `employee-trading-preclearance-assistant`,
  `suitability-reg-bi-reviewer`, `surveillance-alert-triager` /
  `market-surveillance-alert-investigator`, `policy-procedure-gap-analyzer`,
  `risk-control-self-assessment-assistant`, `regulatory-exam-response-packager`,
  `adverse-media-investigator`. The adjudication decision itself is a human hand-off.

### Pending before release
- Domain SME (compliance / ethics) + control-owner blind review; legal review of the
  determination-language screen and the tipping-off boundary.
- Confirm the versioned conflicts-policy config (per-type requirements, de-minimis and
  materiality thresholds, staleness window) and its owner.
- Wire read-only MCP integrations (case management, policy/regulatory corpus, KYC/AML,
  sanctions/PEP, records archive, config) at deployment.
