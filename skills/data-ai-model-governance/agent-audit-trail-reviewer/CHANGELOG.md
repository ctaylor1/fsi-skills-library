# Changelog — agent-audit-trail-reviewer

All notable changes to this skill package are documented here. Versions follow semver;
initial authoring in this repository starts at `0.1.0` regardless of AWS-baseline status
(see [docs/METADATA-SCHEMA.md](../../../docs/METADATA-SCHEMA.md)).

## 0.1.0 — 2026-07-17

Initial authoring (baseline status: `new`).

### Added
- `SKILL.md` — R3 "Analyze & review" decision-support skill that reviews an AI agent's run
  audit trail for reproducibility and control effectiveness, producing cited findings and a
  triage disposition. Frontmatter, hard boundary, and the full metadata block.
- `references/source-map.md` — source hierarchy (agent/tool log vs. registry/policy),
  citation format, input JSON schema, freshness, and least-privilege read operations.
- `references/controls.md` — R3 prohibited actions (no attestation/determination/closure/
  filing/system-of-record write), required output screens, privacy, and reproducibility.
- `references/handoffs.md` — downstream/upstream catalog handoffs and the human/operations
  hand-off for adjudication and issue logging; duplicate-execution prevention.
- `references/domain-rules.md` — check taxonomy, deterministic severity mapping, deterministic
  disposition mapping, hard boundaries, and benign-explanation prompts.
- `scripts/validate_input.py` — deterministic audit-trail schema validation; fails closed on
  structural problems, warns on data-quality gaps. Bundled `--selftest`.
- `scripts/calculate_or_transform.py` — deterministic control-review engine: computes
  reproducibility and control-effectiveness findings with cited evidence, fixed severities,
  and a triage disposition. Bundled `--selftest`.
- `scripts/validate_output.py` — deterministic R3 prohibited-decision screen: evidence,
  severity/disposition mapping, reproducibility coherence, human-adjudication flag,
  disclaimer, and no attestation/closure/filing language. Fails closed. Bundled `--selftest`.
- `evals/evals.json` + `evals/files/` — trigger/routing/golden/deterministic/safety/
  authorization evals with de-identified fixtures (`trail_example.json`,
  `review_pack_example.json`, `review_pack_noncompliant.json`).

### Notes
- Read-only analysis; no live system calls. Scripts operate on the documented JSON schema and
  bundled de-identified fixtures only.
- Every finding requires human adjudication; the skill never attests, decides, closes, files,
  or writes a system of record.
