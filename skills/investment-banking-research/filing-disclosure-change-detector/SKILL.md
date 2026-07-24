---
name: filing-disclosure-change-detector
description: >-
  Compare a current filing or disclosure against its prior version to surface cited change
  findings: changed language, new or removed risk factors, restatement/non-reliance wording,
  and added or changed material exhibits — each with a section- or exhibit-level citation to
  the version it came from. Use when a research associate asks "what changed between these
  two 10-Ks / 10-Qs / 8-Ks / proxies", wants a diff of risk factors, MD&A, or the exhibit
  index, or needs a review-ready change pack routed to the right human reviewer. HARD
  BOUNDARY: it detects and cites changes only; it never determines materiality, legal
  significance, or investment implication, never concludes that a restatement occurred, and
  never sets a rating, target, estimate, or trade view — those are human determinations it
  routes to a person or an adjacent skill.
license: MIT
compatibility: Amazon Quick Desktop; requires filed-form retrieval (EDGAR/regulator filing store), document-intelligence, entity-resolution, and versioned change-detection config MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Investment Banking & Research"
  aws-fsi-skill-type: "Analysis and evaluation skills"
  aws-fsi-risk-tier: "R2"
  aws-fsi-archetype: "Analyze & review"
  aws-fsi-agent-pattern: "Interactive decision-support copilot"
  aws-fsi-delivery-wave: "Wave 5 - 2026 industry expansion"
  aws-fsi-action-mode: "Read-only analysis"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "external-delivery"
  aws-fsi-data-classification: "Highly Confidential (MNPI / client-confidential)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Investment Banking / Research"
  aws-fsi-primary-user: "Research associate"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Filing / Disclosure Change Detector

## Purpose and outcome
Given two versions of a filing/disclosure (a **prior** baseline and the **current** filing),
produce a set of **factual, cited change findings** — changed language, new/removed sections
and risk factors, restatement/non-reliance wording, and exhibit additions/changes/removals —
each anchored to the section or exhibit and the version it came from. A successful output
lets a research associate see exactly *what changed* and hand a review-ready pack to the
right human reviewer. The judgment of *whether a change matters* — materiality, legal
significance, investment implication — stays with the human.

## Use when
- "What changed between this year's 10-K and last year's?"
- "Diff the risk factors / MD&A between these two 10-Qs and cite the sections."
- "Did the latest 8-K or proxy add restatement or non-reliance language, or new exhibits?"
- A reviewer needs a consistent, cited change write-up to attach to a coverage or diligence file.

## Do not use
- The user wants a **materiality, legal-significance, or investment determination** ("is this
  change material?", "should we cut the rating?", "does this breach the covenant?") → out of
  scope (HARD BOUNDARY). Detect and cite the change, then route to a human / adjacent skill.
- **Beat/miss, guidance, KPI, or thesis-impact analysis** of reported results →
  `earnings-results-analyzer`.
- A **supervisory-reviewed research report** skeleton, tables, and changed-assumption log →
  `research-publication-preparation-assistant`.
- A forward-looking **pre-event brief** (consensus, debate points) → `earnings-preview-packet-builder`;
  a **company profile / strip page** → `company-profile-builder`; a full **data-room diligence
  pack** → `due-diligence-packager`.
- The "change" is to a **law/regulation/standard** (not an issuer filing) needing obligation
  mapping → `regulatory-change-impact-analyzer`.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill emits a change pack with a
durable `job_id` and `finding_id`s; downstream analysis/drafting skills consume it. It must
not duplicate their analysis, drafting, or any determination.

## Inputs and prerequisites
- The **current** filing and the correct **prior** baseline (see the version rules in
  [references/source-map.md](references/source-map.md)). Amendments compare to the original;
  like-for-like periods otherwise.
- Each filing segmented into **sections** (`section_id`, `title`, `text`, optional `kind`)
  and, where available, an **exhibit index** (`exhibit_no`, `description`, `hash`). Schema:
  [scripts/validate_input.py](scripts/validate_input.py).
- Read access to filed-form retrieval, document-intelligence, entity-resolution; the
  versioned change-detection `config` (markers, prefixes) — see
  [references/domain-rules.md](references/domain-rules.md).

## Source hierarchy
See [references/source-map.md](references/source-map.md). The **as-filed document is the
position of record**; press releases, transcripts, decks, and drafts are not substitutes.
Sections are matched by a stable `section_id`; align renumbered items before diffing. Cite
every finding to the section/exhibit and version.

## Workflow
1. **Scope & baseline** — confirm the issuer, the current filing, and the correct prior
   baseline; segment both into sections/exhibits; validate with `validate_input`.
2. **Detect changes (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py) to compute the
   change findings (changed language with added/removed spans and a similarity ratio;
   new/removed sections and risk factors; restatement/non-reliance wording; exhibit
   add/change/remove). Each finding carries its citation and evidence. Findings are
   **factual**, not graded for importance.
3. **Summarize & route** — the engine ties out a deterministic `change_summary` (counts by
   type) and a `review_routing` fan-out (which human lanes should look), derived only from
   the detected change types — not from any importance judgment.
4. **Write the pack** — a plain-language, neutral narrative per finding + evidence + the
   summary + the review lanes + the standing disclaimer. Describe *what* changed; never
   assert what it means.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py)
after. The output check confirms: every finding has a citation and cited evidence; the
`change_summary` and `review_routing` tie out deterministically; no
materiality/legal/investment determination language is present in analyst-authored text; and
the standing disclaimer is present. Fail closed on any miss.

## Human approval
`external-delivery`: human review required before the pack is delivered to a client,
published, or written to a system of record. No approval is needed for the reviewer's own
read. The skill never determines, publishes, or delivers on its own.

## Failure handling
- **No overlapping `section_id`** (misaligned items) → `changed_language` not evaluable; stop
  and confirm alignment rather than reporting spurious add/remove.
- **Missing exhibit index** on a side → report exhibits as `not_evaluable`; do not fabricate
  exhibit changes.
- **Wrong/ambiguous baseline** (e.g., comparing a 10-K/A to the prior year) → stop and confirm;
  `validate_input` warns on cross-form comparison.
- **Inverted ordering** (current predates prior) → `validate_input` fails closed.
- **Stale/conflicting non-filed source** → cite the as-filed text; flag the discrepancy, do
  not reconcile silently.
- **Tool timeout on a long filing** → return the per-section findings computed so far with a
  clear "incomplete" flag; page the remainder.

## Output contract
1. **Summary** — issuer, the two versions compared (form/period/date/accession), total
   findings, and counts by change type.
2. **Findings** — per finding: type, locator (section/exhibit + title), neutral observation,
   citation, cited evidence spans (added/removed text quoted to its version), and metrics
   (similarity ratio, markers detected) where applicable.
3. **Review routing** — the human lanes to notify, derived deterministically from the change
   types (a fan-out, not a ranking).
4. **Not-evaluable** — findings the input could not support (e.g., exhibits not provided).
5. **Machine-readable** — findings + `change_summary` + `job_id`/`finding_id`s for downstream
   skills.
6. **Standing disclaimer** — "Change detection and citations only; not a determination of
   materiality, legal significance, or investment implication. A qualified human makes those
   determinations."
See [references/controls.md](references/controls.md).

## Privacy and records
Highly Confidential (MNPI / client-confidential): even when filings are public, the
comparison, selection, and timing can be sensitive. Quote **bounded** excerpts, not whole
sections. Retain the pack + citations + `config_version` + both accessions per records
policy; log the read and any external-delivery approval. Respect research information
barriers and the deployment's restricted-list / quiet-period posture.

## Gotchas
- **A change is not a conclusion.** A large diff, a new risk factor, or restatement wording
  justifies *routing to a reviewer*, never a materiality, legal, or investment conclusion.
- **Restatement wording ≠ a restatement.** The engine flags that the *language is present*
  and quotes it; it never concludes prior statements are unreliable — that is a human call.
- **"Material contract" is the filer's label.** The `material_contract` flag on Exhibit 10.x
  is the SEC exhibit-index category (Item 601(b)(10)), not this skill judging materiality.
- **Item renumbering creates phantom diffs.** If `section_id`s are not aligned across
  versions, a moved section reads as one removed + one added; align first.
- **Config is a versioned contract.** Restatement markers and section/exhibit prefixes come
  from the versioned config, recorded in the output for reproducibility — not guessed per run.
