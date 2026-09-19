# Build Status

Progress tracker for the 296-package FSI portfolio. The **live** built/pending list is
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

## To do

- [ ] **Insurance Phase 4 — architecture and measured automation.** Resume in a future
  session from the completed Phase 3 checkpoint. Cover insurance workflow, data and
  core modernization; shared solution architecture, automation assessment,
  data-product value and operations performance. Follow the
  [insurance roadmap](docs/insurance/IMPLEMENTATION-PLAN.md); validate source
  integration, benefits and failure paths. Queued at the user's request; not started.

## Insurance Phase 3 — 2026-09-18

**Phase 3 implementation and bounded verification are complete.** Twenty-one new
specialist workflows bring insurance to **61 packages**. Strategy/economics,
portfolio/actuarial analysis, claims/recovery/disputes, fraud/SIU, assumed
reinsurance, exposure/CAT, finance/capital/ORSA and market conduct have native
methods, evidence contracts, templates, portable helpers and active routes.

Final checks: **1,517/1,517 whole-library executable package checks**, including
**308 insurance checks**; **362 repository methods**, including **37 insurance
contract/integration methods**. All **296 packages** pass structure validation with
zero errors/warnings and zero dangling handoffs. All 61 insurance contract bundles
and 38 foundation bundles match. Scoped lint and whitespace pass. Insurance package
commands invoke 754 regression methods (342 in the new packages); those are not
additional independent evaluations. Global counts include concurrent Payments
Phase 4 changes, which are preserved.

Three independent streams evaluated all 21 new workflows with fresh synthetic
sources, numerical expectations and practitioner narratives. They found two
misleading dependent benefit outputs and four input-guide omissions. The repairs
passed unchanged-input benefit replay and separately disclosed interface mappings.
Final integrated replay matches all **46 reviewed JSON results across 138 checks**,
including the expected rejection of one malformed input. Original evidence and
wrong outputs remain retained. No source authentication, qualified professional
signoff, broader model benchmark or deployment acceptance is claimed.

See [implementation and inventory](docs/insurance/PHASE3-IMPLEMENTATION.md),
[validation evidence](docs/insurance/phase3-validation/README.md) and
[roadmap](docs/insurance/IMPLEMENTATION-PLAN.md). **Next: Phase 4 architecture and
measured automation.**

## Payments Phase 4 — 2026-09-18

**Phase 4 authoring and bounded agent evaluation are complete:** four new packages
bring Payments to **38**, with seven optional modules across six existing packages.
Regional Pix/UPI/Interac, cross-border design and funding, wallets/mobile money,
advanced platforms/commercial cards, concrete stablecoin assessment, company
business models and agent-commerce evidence are implemented. Existing core modes
retain their scope and behavior.

**311/311 Payments/PCI package commands**, **61 Payments integration methods**, and
**359 domain regression methods inside those package commands** pass. Structure and
handoffs pass across 39 Payments/PCI packages and all 296 repository packages.
The full package sweep passes **1,517/1,517**; the repository test sweep runs 362
methods with one remaining concurrent insurance-router catalog/metadata failure.
A clean whole-repository test pass is not claimed. Scoped E9/F, bundle and whitespace
checks pass. Prior wealth and Payments Phase 1–3 evidence matches the pre-turn hashes.

Independent fresh evaluations cover all eleven new native contexts and 41 router
requests. AP2 subdelegation and intermediary funding defects were fixed and the
original cases independently retested. See [scope](docs/payments/PHASE4-IMPLEMENTATION.md),
[validation and findings](docs/payments/phase4-validation/README.md), and
[roadmap](docs/payments/ROADMAP.md). All four agreed implementation phases are authored;
human specialist acceptance, institutional sources, workbook reconciliation and
deployment gates remain open. No financial execution or publication occurred.

## Historical insurance Phase 2 checkpoint — 2026-09-18

**Phase 2 implementation is complete.** Seventeen new native workflows bring insurance
to **40 packages**. Product/rate, policy/billing, distribution, claims, life/annuity and
ceded reinsurance foundations now have active routes, source-bound outputs, portable
helpers, explicit native schemas and meaningful arithmetic/evidence controls.

Final verification: **1,329/1,329 full-library executable package checks**, including
**197 insurance checks**; **344 repository test methods**, including **31 insurance
contract/integration methods**. All **271 packages** pass structure validation with
zero errors/warnings and zero dangling handoff references. All 40 insurance contract
bundles and 17 foundation bundles match; scoped lint and whitespace checks pass.
The insurance package commands invoke 412 test methods (258 in the new packages);
these counts are not additional independent evaluations.

Three independent agent streams authored **17 fresh baseline cases** plus three
bounded variants. They found and verified repairs for three domain-output defects
and schema/freshness usability gaps. Final integrated replay passed **60 native
checks across 20 unchanged inputs**, with outputs exactly matching the independently
reviewed results. This is synthetic bounded evidence, not a model benchmark, source
authentication, specialist signoff or institutional deployment acceptance.

See [implementation and inventory](docs/insurance/PHASE2-IMPLEMENTATION.md),
[validation evidence](docs/insurance/phase2-validation/README.md) and
[roadmap](docs/insurance/IMPLEMENTATION-PLAN.md). At that checkpoint Phase 3 analytical
and specialist depth remained next; the Phase 3 record above supersedes that
implementation status. Historical counts include concurrent Payments Phase 3 work.

## Historical insurance Phase 1 checkpoint — 2026-09-18

**Insurance Phase 1 implementation is complete.** Its 24 original packages became
**23 packages** through two workflow mergers and a new router. Renamed packages,
catalog overrides, native evidence contracts and handoffs are synchronized. Existing
methods now preserve missing information and distinguish reserve, quote, treaty,
claims, reconciliation and CAT-monitoring meanings more carefully.

Final integrated verification: **1,179/1,179 executable package checks**, including
**118 insurance checks**; **319 repository test methods**, including **15 insurance
contract/integration methods**; **248 packages with zero structure errors/warnings**;
zero dangling handoffs; all 23 insurance helper/reference bundles match. Scoped
E9/F lint and whitespace checks pass. The insurance checks include 154 package test
methods; do not add them to the executable-command count as independent evaluations.
This final sweep supersedes the transient insurance failure observed during the
concurrent payments sweep below.

Four independent initial agent-evaluation streams exercised routing, product,
claims and CAT/data requests. Their observed defects were repaired and the original
inputs replayed. Some initial evaluators then authored fixes: those later replays
are author verification, not additional independent acceptance. Human professional
review, wider model benchmarking, current institutional sources and deployment
acceptance remain outstanding. Other domain work was preserved; the repository-wide
total includes concurrent payments additions.

See [implementation and package inventory](docs/insurance/PHASE1-IMPLEMENTATION.md),
[validation evidence](docs/insurance/validation/README.md), and
[roadmap](docs/insurance/IMPLEMENTATION-PLAN.md). At that checkpoint Phase 2 operating foundations remained next; the current Phase 2
record above supersedes that implementation status. Historical test counts remain unchanged.

## Historical payments Phase 3 checkpoint — 2026-09-18

**Phase 3 implementation is complete:** six new packages bring Payments to **34**.
Fraud and incident packages are expanded and renamed with legacy interfaces retained.
Acceptance analytics, credentials, platform/commercial flows, liquidity and operating
improvement are implemented; bank collection and architecture/readiness modules are
added. Routing, native handoffs, catalog regeneration and shared bundles are aligned.

**234/234 payments/PCI package commands** and **49 payments integration methods** pass.
The Phase 3 domain suites contain 281 regression methods, included inside package
commands rather than additive independent evaluations. The recorded whole-library
sweep passes **1,329/1,329 package commands**, **336 repository test methods**, and
structure/handoff checks across **271 packages**. Those totals include concurrent
insurance work. Scoped E9/F lint and whitespace pass.

Independent fresh forward reviews cover the eleven native workflows and 37 routing
cases. Conflicting payer-response identity and fraud route-mode defects were fixed
and independently retested; final scope review also corrected active handoffs and
superseded FedNow references. Prior wealth and payments validation records match
the pre-turn baseline. No live actions or deployment occurred.

See [implementation](docs/payments/PHASE3-IMPLEMENTATION.md),
[validation and findings](docs/payments/phase3-validation/README.md), and
[roadmap](docs/payments/ROADMAP.md). At that checkpoint Phase 4 regional depth
and specialized models remained next; the current entry above supersedes that status. Professional acceptance, trusted institution sources,
workbook reconciliation and deployment gates remain open.

## Historical payments Phase 2 checkpoint — 2026-09-18

**Core authoring is complete:** ten new workflows bring Payments to **28 packages**.
Native US/EA/UK rail and message profiles, consumer-error/scheme preparation,
participant-aware routing and standalone evidence-bound helpers are delivered.
Initiation, ordinary servicing and exception repair retain distinct authority.

**163/163 payments/PCI package evaluations**, **40 payments integration methods**
and **319 repository test methods** pass. All **248 packages** pass structure checks,
with zero dangling handoffs. Payment bundles, scoped E9/F lint and whitespace checks
pass. The final full-library sweep passes **1,179/1,179 package commands**.
Independent fresh forward scenarios and an 18-request routing pass identified
six findings that were corrected and retested. These are bounded agent evaluations,
not professional or deployment acceptance. Earlier transient failures in concurrent
insurance work and their successful recheck remain in the validation record.

See [implementation](docs/payments/PHASE2-IMPLEMENTATION.md),
[validation and retained evidence](docs/payments/phase2-validation/README.md),
[source governance](docs/payments/SOURCE-GOVERNANCE.md) and [remaining phases](docs/payments/ROADMAP.md).
The external workbook, licensed institution rules, trusted-source integration,
human specialist acceptance and deployment gates remain outstanding.

## Historical payments Phase 1 checkpoint — 2026-09-17

**Phase 1 implementation is complete.** The checkpoint catalog contained **239 packages** with
**18 payment packages**. A payments router and shared contracts were added; payout
explanation was merged into settlement reconciliation; issuer and merchant dispute
roles were separated; and PCI evidence moved to cybersecurity. Renames, metadata,
active handoffs and catalog regeneration overrides are synchronized.

Operational corrections preserve payment lifecycle distinctions, unknown monetary
values, source identity, scoped policy evidence and exact repair proposals. The
router exposes later-phase jobs as capability gaps. Existing narrower skills retain
their actual scope rather than claim broader strategic or runtime capabilities.

Validation: **1,101/1,101 package evaluations**, including **100 payments/PCI**;
**277 repository test methods**, including **13 payments integration methods**;
**239 packages with 0 structure errors/warnings**; no dangling handoffs; consistent
shared bundles in 19 packages. Scoped E9/F lint and whitespace checks pass.
Two independent agents evaluated nine bounded synthetic requests plus variants,
found three defects, and independently verified their fixes. These checks do not
establish human specialist acceptance or production readiness. The broader routing
model benchmark, workbook reconciliation, trusted-source integration and deployment
acceptance remain outstanding.

See [implementation](docs/payments/PHASE1-IMPLEMENTATION.md),
[validation and retained evidence](docs/payments/validation/README.md), and
[source governance](docs/payments/SOURCE-GOVERNANCE.md). Phase 2–4 capabilities were
not implemented at that checkpoint. Wealth-management package content and validation records were preserved.

## Wealth-management P4 quality validation, 2026-09-17

The catalog remains **239 packages**, including **27 wealth-management packages**. All agreed
P0–P3 authoring priorities remain complete: 27 practitioner destinations plus the router,
with manager due diligence in Asset Management. P4 adds quality validation and focused
instruction corrections without adding or removing practitioner coverage.

**P4 validation work is complete; behavioral acceptance is not achieved.** Thirty real-model
runs are retained: 24 initial paired outputs across 12 synthetic advisor cases, plus six cold
follow-ups after corrections. Initial with-skill responses passed **105/111 rubric items**
and **6/12 whole cases**; baselines passed **81/111 items** and **2/12 cases**. All expected
runs completed and all 278 initial/follow-up item decisions are reviewed with evidence.
Three independent-from-generation agents graded the outputs; this is not human-SME acceptance.
The requested model was GPT-5.5/high; exact server-resolved identity was not returned.

Source-to-input fidelity remains a blocker despite validator-passing artifacts. Three skills
now have explicit unknown/source-check guidance (0.2.1) and four supporting regressions.
Two targeted with-skill reruns passed fully; household planning still invented provenance.
Additional internal-audience packaging defects remain documented outside narrow rubric scores.
See the [P4 validation record](docs/wealth-management/P4-VALIDATION.md),
[implementation](docs/wealth-management/P4-IMPLEMENTATION.md) and
[retained evidence](docs/wealth-management/p4/results/README.md).

**1,082/1,082 package evaluations, 264 repository test methods, 20 new handoff tests across
five chains, and 42/42 lending replay checks pass.** Handoff tests are included in the
repository total. Package validation reports **0 errors / 0 warnings** across 239 packages;
there are no dangling handoffs. Catalog correspondence, shared helpers and scoped lint pass.
Deterministic checks do not establish source truth or model reliability. No live connectors,
external financial actions, professional approvals or deployment certification are supplied.

[P0 validation](docs/wealth-management/P0-VALIDATION.md),
[P1 validation](docs/wealth-management/P1-VALIDATION.md),
[P2 validation](docs/wealth-management/P2-VALIDATION.md) and
[P3 validation](docs/wealth-management/P3-VALIDATION.md) preserve earlier milestone results.

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

## Historical coverage snapshot — pre-P0 220-package milestone

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

The prior milestone recorded **220 packages** (173 original + 47 industry-expansion) and the following deterministic checks. These historical results do not establish current deployment readiness:
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

- [ ] Insurance Phase 4: architecture and measured automation, following [the agreed plan](docs/insurance/IMPLEMENTATION-PLAN.md). Deferred for a later session; not implemented yet.
- [ ] Payments Phase 4 follow-up: implementation is complete; finish human specialist review, institution/source acceptance, workbook reconciliation and deployment acceptance as applicable. See [remaining gates](docs/payments/phase4-validation/README.md#evidence-and-remaining-gates).
- Licensing set to MIT to match the repo; the build template's default was "Proprietary."
  Confirm MIT is the intended license for published skills.
- The 12 scheduled-agent monitors assume the Quick scheduled-agent runtime is enabled with
  read-only entitlements.
- Real MCP integrations must be wired at deployment (see each skill's `compatibility:` and
  `references/source-map.md`).
