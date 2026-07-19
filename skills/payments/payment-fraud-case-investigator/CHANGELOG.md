# Changelog — payment-fraud-case-investigator

All notable changes to this skill package are documented here. Versions follow semver;
initial authoring in this repository starts at `0.1.0` regardless of AWS-baseline status
(tracked separately in `aws-fsi-baseline-status`).

## [0.1.0] - 2026-07-17

### Added
- Initial authoring of the **payment-fraud-case-investigator** skill (R3, Investigate &
  casework; Case agent + evidence bundle).
- `SKILL.md` with frontmatter, workflow, validation loop, output contract, and the R3
  hard boundary (evidence + recommendation only; no fraud determination, closure, block,
  reversal/return, or SAR filing).
- References: `source-map.md` (ranked read-only sources + citation format), `controls.md`
  (prohibitions, allowed recommendation dispositions, output screens, segregation of duties),
  `handoffs.md` (upstream monitoring/triage; downstream/lateral specialists — sanctions, BEC,
  SAR drafting, payment repair, disputes; human adjudicator/FIU), and `domain-rules.md`
  (six evidence pillars, documented scoring weights/bands, disposition mapping).
- Scripts (Python stdlib-only, `--selftest`): `validate_input.py` (schema + evidence-gap
  screen), `calculate_or_transform.py` (deterministic case builder — durable `case_id`,
  chronology, cited evidence bundle, risk score/band, recommendation), and
  `validate_output.py` (fails closed on missing/invalid `case_id`, disallowed disposition,
  uncited evidence, band inconsistency, or closure/determination/filing language).
- Evals: trigger positive/negative, routing (sanctions, BEC, SAR, repair), a golden task over
  seven de-identified cases, deterministic self-tests, and a safety check that runs
  `validate_output.py` on a non-compliant fixture and must fail closed (exit 1).
