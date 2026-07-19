# Build Status

Progress tracker for the 173-skill FSI portfolio. The **live** built/pending list is
computed from the filesystem — run:

```bash
python tools/status_report.py          # coverage by wave + next-to-build
python tools/status_report.py --list   # every skill's built/pending state
python tools/validate_skills.py        # spec + standards validation of what's built
python tools/run_selftests.py          # execute every skill's deterministic + safety evals
python tools/check_handoffs.py         # flag handoff refs to skills not in the catalog
python tools/spec_card.py <name>       # emit exact frontmatter + build spec for a skill
```

This file is the human narrative: conventions locked, what's done, and what's queued next.

## Locked conventions

- **Layout:** category-nested — `skills/<category>/<skill-name>/SKILL.md`.
- **License:** MIT (frontmatter `license: MIT`; repo `LICENSE` kept).
- **Skill type:** every skill carries `aws-fsi-skill-type` (one of six: Artifact-creation ·
  Utility · Workflow/orchestration · System-interaction/operational · Analysis/evaluation ·
  Guidance/domain-expertise), derived from archetype + curated overrides. See
  [METADATA-SCHEMA](docs/METADATA-SCHEMA.md#skill-type-aws-fsi-skill-type).
- **Pace:** foundation + gold-standard exemplars first, then wave-by-wave.
- **Scripts:** deterministic, self-contained validators/transformers over documented JSON
  schemas + de-identified fixtures (no live system connectors in this repo).
- Spec: [agentskills.io/specification](https://agentskills.io/specification);
  standards: [docs/BUILD-STANDARDS.md](docs/BUILD-STANDARDS.md).

## Coverage snapshot — ✅ COMPLETE: 173/173 built, verified 0/0 + all self-tests green

| Delivery wave | Built | Total |
| ------------- | ----- | ----- |
| Wave 1 — stabilize existing | **20** | 20 ✅ |
| Wave 1 — platform controls | **8** | 8 ✅ |
| Wave 1 — low-risk productivity | **4** | 4 ✅ |
| Wave 2 — analytical production | **61** | 61 ✅ |
| Wave 3 — regulated casework | **71** | 71 ✅ |
| Wave 4 — gated orchestration | **9** | 9 ✅ |
| **Total** | **173** | **173 ✅** |

**All 173 skills built and verified.** Final integrity check:
- `validate_skills.py`: **173/173, 0 errors / 0 warnings**
- `check_handoffs.py`: **0 dangling references**
- `run_selftests.py`: **703/703 pass** (all validators green; every safety fixture fails closed)
- 0 incomplete packages; 0 catalog↔metadata mismatches.
- Risk tiers match plan exactly (R1=8, R2=77, R3=79, R4=9); 12 read-only scheduled monitors;
  all 6 skill-types represented; 14 categories; all 9 R4 orchestrators carry a fail-closed
  executed-without-approval safety check.

### Pre-commit review & hardening (2026-07-19)
Ran `ruff` (clean, with `ruff.toml`), compiled all 519 Python files, validated all 700 JSON
files, and confirmed all 175 safety self-tests fail via the intended guardrail (0 pass-by-crash).
A fan-out adversarial code review (14 category reviewers) found **41 real defects** (9 high,
20 medium, 12 low); a targeted fix workflow resolved all of them, each proven by a new
fail-closed fixture. Independent re-verification (constructing the bypass directly, not
trusting the agents' fixtures) then caught **1 additional** R4 skill the review missed and it
was fixed. Highlights:
- **Systemic R4 approval-gating**: plan-hash tamper check failed *open* when the hash was
  stripped, across all 9 orchestrators (root: the exemplar). Now every non-rejected plan must
  carry a matching hash or fail closed; plus approver-role enforcement, `required_role` in the
  hash, token↔hash binding, denylist→allowlist for permissible actions. **All 9 independently
  re-verified fail-closed.**
- **Material logic bug**: `financial-spreading-assistant` DSCR was ~2× overstated (interest
  read from the wrong dict); corrected and regression-tested.
- Paraphrase-bypassable narrative guardrails (fraud finding, denial-side decisions, executed
  response actions, decided-status) hardened; ~10 config-divergence validators fixed.
- Self-test count grew 703 → 751 (new fail-closed regression tests).

### Remaining before production release (per-skill, not blocking authoring)
Each skill's CHANGELOG lists its "Pending before release": domain-SME / control-owner blind
review, jurisdiction/rule-set sign-off, and wiring the real MCP integrations at deployment
(all bundled scripts are deterministic validators over schemas + fixtures, not live connectors).

## Done

- [x] Reviewed source workbook (9 worksheets) and the Agent Skills specification.
- [x] Generated machine-readable catalog — [catalog/skills-catalog.json](catalog/skills-catalog.json) / `.csv`.
- [x] Validated all 173 names against spec (unique, ≤64 chars, hyphenation OK).
- [x] Foundation docs — README, [BUILD-STANDARDS](docs/BUILD-STANDARDS.md),
      [SKILL-TEMPLATE](docs/SKILL-TEMPLATE.md), [RISK-TIERS](docs/RISK-TIERS.md),
      [ARCHETYPES](docs/ARCHETYPES.md), [SHARED-SERVICES](docs/SHARED-SERVICES.md),
      [METADATA-SCHEMA](docs/METADATA-SCHEMA.md), [SOURCES](docs/SOURCES.md).
- [x] Tooling — `build_catalog_from_xlsx.py`, `validate_skills.py`, `status_report.py`,
      `run_selftests.py`, `spec_card.py` (exact per-skill frontmatter), `check_handoffs.py`
      (flags handoff refs not in the catalog).
- [x] Four gold-standard exemplar packages (R1–R4) — see table below.
- [x] `aws-fsi-skill-type` taxonomy added and classified for all 173.
- [x] **Wave 1 complete** (30 skills) via green-gated author→verify workflow.

## Gold-standard exemplars (spanning R1–R4 + key archetypes) — ✅ COMPLETE

| Skill | Category | Tier | Archetype | Status |
| ----- | -------- | ---- | --------- | ------ |
| `portfolio-holdings-summarizer` | Capital Markets | R1 | Explain & summarize | ✅ built + validated |
| `account-anomaly-screener` | Banking | R2 | Analyze & review | ✅ built + validated |
| `aml-alert-triager` | Compliance & Financial Crime | R3 | Investigate & casework | ✅ built + validated |
| `loan-servicing-exception-resolver` | Banking | R4 | Orchestrate & resolve | ✅ built + validated |

All four pass `validate_skills.py` (0 errors/warnings) and the full `run_selftests.py`
suite (15/15: input/output validators pass; advice/determination/closure/executed-without-
approval safety fixtures all fail closed). These are the quality bar for scaling.

Remaining archetypes get their first instance early in Wave-2/3 scaling: **Model &
calculate** (`financial-spreading-assistant` — the lead Wave-2 build), **Reconcile &
validate** (`settlement-break-reconciler` / `gl-reconciler`), **Monitor & alert**
(`covenant-compliance-monitor`), **Draft & package** (`credit-memo-drafter`), **Domain
workflow**.

## Recommended build order (after exemplars)

1. **Finish Wave 1** — remaining stabilize-existing (15), platform-controls (8),
   low-risk-productivity (4). Lowest risk; establishes each category's shared references.
2. **Wave 2 — analytical production (61)** — grouped by category so shared
   `source-map.md` / `domain-rules.md` content is authored once per domain.
3. **Wave 3 — regulated casework (71)** — casework/triage/investigation with full
   controls + handoffs.
4. **Wave 4 — gated orchestration (9)** — approval-gated writes with rollback + audit.

## Open items for the owner

- Licensing set to MIT to match the repo; the build template's default was "Proprietary."
  Confirm MIT is the intended license for published skills.
- The 12 scheduled-agent monitors assume the Quick scheduled-agent runtime is enabled with
  read-only entitlements.
- Real MCP integrations must be wired at deployment (see each skill's `compatibility:` and
  `references/source-map.md`).
