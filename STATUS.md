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

## Coverage snapshot — ✅ COMPLETE: 220/220 built, verified 0/0 + all self-tests green

| Delivery wave | Built | Total |
| ------------- | ----- | ----- |
| Wave 1 — stabilize existing | **20** | 20 ✅ |
| Wave 1 — platform controls | **8** | 8 ✅ |
| Wave 1 — low-risk productivity | **4** | 4 ✅ |
| Wave 2 — analytical production | **61** | 61 ✅ |
| Wave 3 — regulated casework | **71** | 71 ✅ |
| Wave 4 — gated orchestration | **9** | 9 ✅ |
| Wave 5 — 2026 industry expansion | **47** | 47 ✅ |
| **Total** | **220** | **220 ✅** |

**All 220 skills built and verified** (173 original + 47 industry-expansion). Final integrity check:
- `validate_skills.py`: **220/220, 0 errors / 0 warnings**
- `check_handoffs.py`: **0 dangling references across 220**
- `run_selftests.py`: **955/955 pass** (all validators green; every safety fixture fails closed)
- `ruff check .`: clean. Catalog reconciles **220 ↔ 220 built dirs, 1:1**.
- 0 incomplete packages; 0 catalog↔metadata mismatches.
- Original 173 integrity check retained below (703/703 self-tests at that milestone).
- Risk tiers match plan exactly (R1=8, R2=77, R3=79, R4=9); 12 read-only scheduled monitors;
  all 6 skill-types represented; 14 categories; all 9 R4 orchestrators carry a fail-closed
  executed-without-approval safety check.

### 2026 Industry-expansion cohort (+47 skills, provisional) — ✅ complete
From the "2026 Industry Disposition" brief (54 proposals → 47 packages). Reviewed against
the 173-skill library first; flags raised and resolved with the owner:
- **Catalog:** the brief's skills aren't in the workbook the catalog derives from (the
  "Industry Disposition" tab isn't in the v2 xlsx). Owner approved extending the catalog
  **provisionally**: the 47 live in `catalog/provisional-additions.json` (each `provisional:
  true`, `source: industry-disposition-brief-2026-07`) and `build_catalog_from_xlsx.py` now
  merges them, so a workbook regen preserves them until the workbook catches up. Catalog is
  now **220** (173 workbook + 47 provisional).
- **Categorization re-homed** (owner-approved): research packages `filing-disclosure-change-
  detector`, `kpi-segment-bridge-builder` → Investment Banking & Research; trading packages
  `order-allocation-validator`, `transaction-cost-estimator` → Capital Markets; stewardship/
  proxy (#22-24) kept in Asset Management. Final +new spread: AM +19, IB&R +9, Capital
  Markets +6, Insurance +8, Payments +3, Banking +2.
- **"Utility" is a skill-type, not an archetype:** the 4 brief "Utility" packages
  (`holdings-transaction-normalizer`, `investment-source-ingester`, `credit-terms-covenant-
  extractor`, `fnol-normalizer`) were given real archetypes + skill-type `Utility skills`.
- `aws-fsi-delivery-wave: "Wave 5 - 2026 industry expansion"` for all 47.
- Build in 2 batches (~24/23) via green-gated author->verify workflows; every package must
  pass validate + selftests + check_handoffs + ruff. All named handoff targets resolve
  (existing or in-batch).
- **Progress: all 47 built + verified (batch 1 = 24 via workflow; remaining 23 hand-built in
  the main loop after the weekly workflow limit).** Repo is at **220/220**. The last 19 were
  hand-built to the same green-gate standard (SKILL.md + 4 references + 3 stdlib scripts +
  de-identified fixtures + evals + CHANGELOG each): 7 Insurance
  (insurance-regulatory-filing-packager, actuarial-model-run-assistant [chain-ladder],
  claim-damage-evaluation-comparator, fnol-normalizer, liability-evidence-matrix-builder,
  claim-settlement-authority-packet, insurance-rating-quote-worksheet), 3 Payments
  (payment-api-log-diagnostic-pack [PAN-redaction + leakage screen],
  payment-integration-readiness-pack, payment-fraud-rule-impact-analyzer), and 9 Capital
  Markets / IB&R (capital-structure-maturity-mapper, financing-alternatives-calculator,
  market-window-readiness-pack, desk-pnl-risk-attribution-pack, client-rfq-preparation-brief,
  pricing-hedging-scenario-calculator, model-roll-forward-auditor,
  research-publication-preparation-assistant, trade-idea-evidence-packet,
  financial-document-version-comparator).
- **Full-library sweep (2026-07-24):** `ruff check .` clean; `validate_skills.py` **220/220,
  0/0**; `check_handoffs.py` **0 dangling across 220**; `run_selftests.py` **955/955 pass**
  (every R2/R3 safety fixture fails closed). Catalog reconciles **220 entries ↔ 220 built
  dirs, 1:1** (all 47 provisional entries present and built). Cross-platform fix applied:
  removed non-cp1252 characters (Σ) from printed validator strings so output never crashes on
  the Windows console.
- **Guardrail design of the 47:** deterministic stdlib-only scripts over documented JSON
  schemas; each R3 skill carries a fail-closed `validate_output` screen (no
  decide/approve/execute/recommend language, citation coverage, review-only disposition,
  standing disclaimer) wired to a non-compliant "bad" fixture as a safety eval (`expect_exit
  1`); R2 skills add tie-out identities (TCA components→total, chain-ladder ultimate=latest+IBNR,
  premium buildup, P&L explained+residual=reported).

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
