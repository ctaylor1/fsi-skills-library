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

## Coverage snapshot (106/173 built, verified 0/0 + all self-tests green)

| Delivery wave | Built | Total |
| ------------- | ----- | ----- |
| Wave 1 — stabilize existing | **20** | 20 ✅ |
| Wave 1 — platform controls | **8** | 8 ✅ |
| Wave 1 — low-risk productivity | **4** | 4 ✅ |
| Wave 2 — analytical production | **61** | 61 ✅ |
| Wave 3 — regulated casework | **12** | 71 (59 remaining) |
| Wave 4 — gated orchestration | 1 | 9 (8 remaining) |
| **Total** | **106** | **173** |

**Waves 1–2 complete; Wave 3 in progress (12/71).** All 106 built skills pass
`validate_skills.py` (0/0), `check_handoffs.py` (0 dangling), and `run_selftests.py`
(431/431). Wave-3 batch 1 was cut short by the usage limit; 4 half-written skills were
removed (to rebuild) and 2 over-long descriptions trimmed — clean checkpoint. **67 remain**
(Wave 3: 59, Wave 4: 8). Remainder work-lists prepped in scratchpad
(`wave3_remaining_args.json`, `wave4_args.json`); generic build workflow at
`workflows/scripts/build-fsi-wave-wf_f38affd7-d73.js`. Resume when the usage limit resets.

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
