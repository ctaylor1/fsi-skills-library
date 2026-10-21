---
name: issuer-engagement-reviewer
description: >-
  Assemble a cited Engagement History Brief for a single issuer: prior stewardship
  engagements (meetings, calls, letters), issuer commitments and the progress the issuer has
  disclosed against them, firm-side and issuer-side attendees by role, the underlying source
  documents, and unresolved follow-ups — as a draft a stewardship analyst reviews. Use when a
  stewardship or active-ownership analyst asks to compile an issuer's engagement history,
  prepare background before a meeting or vote, track outstanding commitments and open
  follow-ups, or reconstruct who-said-what-when with citations. HARD BOUNDARY: this skill is
  draft-only and R3 — it NEVER chooses an engagement objective, represents or states a firm
  position/view, casts or proposes a vote, or writes a system of record; those are human
  stewardship decisions. It routes vote-decision evidence to proxy-voting-reviewer
  and human-proposed-vote policy checks to proxy-voting-reviewer.
license: MIT
compatibility: Python 3.10+ offline JSON helpers; live source connectors and authenticated delivery require separate deployment integration.
metadata:
  aws-fsi-category: "Asset Management"
  aws-fsi-skill-type: "Artifact-creation skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Draft & package"
  aws-fsi-agent-pattern: "Interactive production copilot"
  aws-fsi-delivery-wave: "Wave 5 - 2026 industry expansion"
  aws-fsi-action-mode: "Draft-only; no system-of-record change"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "existing-updated"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Highly Confidential (MNPI / client-confidential)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Asset Management investment & product"
  aws-fsi-primary-user: "Stewardship analyst"
  aws-fsi-version: "0.2.0"
  aws-fsi-recertification-date: "2027-09-20"
---

Read [references/domain-rules.md](references/domain-rules.md) for the supplied-input validation boundary and current deterministic limits before using the scripts.


# Engagement History Brief

## Purpose and outcome
Assemble, for a single issuer, a **draft Engagement History Brief**: a reverse-chronological
timeline of prior stewardship engagements, each issuer commitment matched to the progress the
issuer has *disclosed* against it, a role-level attendee roll-up, the underlying source
documents, and the still-open follow-ups — every item cited to its source. The outcome is a
review-ready background pack a **stewardship analyst** uses to prepare for a meeting, a vote,
or an internal discussion. It is **evidence assembled, not a decision made**: the brief never
chooses what the next engagement should achieve and never states a firm view on the issuer.

## Use when
- "Pull together our engagement history with `<issuer>`."
- "What has this issuer committed to, and what progress have they disclosed?"
- "Prepare background before our meeting / before the AGM vote."
- "What follow-ups are still open with this issuer, and who owns them?"
- "Reconstruct who attended which engagement and when, with citations."

## Do not use
- **Casting, proposing, or recommending a vote**, or assembling a *meeting/vote decision*
  evidence packet → `proxy-voting-reviewer`.
- **Checking a human-proposed vote against policy** and precedent →
  `proxy-voting-reviewer`.
- **Drafting external, firm-attributed narrative** (fund/stewardship commentary that
  represents the firm to clients/public) → `investment-commentary-builder` (approval-gated).
- **Choosing the engagement objective** or **setting / representing the firm's position** on
  an issuer → refuse; this is a human stewardship decision (analyst → stewardship lead /
  stewardship committee). See [references/handoffs.md](references/handoffs.md).
- Any request to **write the engagement log / system of record**, close a follow-up, or mark
  a commitment "met" as a judgment → refuse; draft-only.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill produces a *history* brief
keyed to a durable `brief_id`; the vote-decision packet, the policy consistency check, and
external commentary are **separate skills with separate entitlements**. This skill emits the
cited history bundle and routes onward; it must not perform their work or duplicate it.

## Inputs and prerequisites
- The issuer engagement log: engagements (id, date, type, channel, topics), attendees
  (firm-side and issuer-side, by role), issuer commitments (id, text, due), disclosed
  progress (linked to a commitment, with source), follow-ups (id, text, status, owner), and
  source documents (id, title, type, date, source ref). Plus `as_of_date`, `brief_version`,
  and `source_hierarchy_version`. Schema and validator:
  [scripts/validate_input.py](scripts/validate_input.py).
- Read access to the engagement log / stewardship CRM, document intelligence (notes,
  disclosures, filings), entity resolution (issuer identity), and approved-source retrieval
  (research-provider inputs). All **read-only**.

## Source hierarchy
See [references/source-map.md](references/source-map.md). The engagement log is the system of
record for *what was said and committed*; issuer disclosures and filings are authoritative for
*disclosed progress*; research-provider inputs are supporting context, never a substitute for
the primary record. **Cite every item**; where sources conflict, present both with dates and
do not resolve the conflict on the firm's behalf. `brief_version` and
`source_hierarchy_version` are **versioned contracts** recorded on every brief.

## Workflow
1. **Validate & normalize** — run `validate_input`; confirm the log is structurally usable
   and record data-quality warnings (missing owners, uncited progress, overdue commitments,
   future-dated entries). Do not invent missing fields.
2. **Assemble (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py): builds the
   reverse-chronological timeline, matches each commitment to its disclosed progress, derives
   a **factual, date-based** commitment status, rolls up attendees by role, deduplicates
   source documents, and collects still-open follow-ups. Assembly is normalization + matching
   only — see [references/domain-rules.md](references/domain-rules.md).
3. **Render to template** — populate [assets/output-template.md](assets/output-template.md).
   The *Engagement objective* and *Firm position* sections are left explicitly **unset** with
   the reason recorded; the brief carries them as `null` / `false`.
4. **Validate output** — run [scripts/validate_output.py](scripts/validate_output.py); it
   fails closed on any uncited item, any chosen objective / represented position, prohibited
   decision or vote language, a non-draft status, or missing approvals.
5. **Route, do not decide** — surface the open follow-ups and any conflicts as *candidate
   discussion points for the human*, and route vote/position questions to the adjacent skills.
   Never fill the objective or state a view.

## Validation loop
Run `validate_input` before assembly and `validate_output` after rendering. The output screen
enforces: draft-only status; all required template sections present; every engagement,
commitment, disclosed-progress, follow-up, and source-document item cited; `engagement_objective`
null and `firm_position` not represented; no prohibited-decision / firm-representation / vote
language; required approver roles recorded; standing note present. Correct and re-run until it
passes, or **fail closed** and surface the gap. See [references/controls.md](references/controls.md).

## Human approval
`required`. This skill **drafts and packages only**. A **stewardship analyst** must review the
brief, and a **stewardship lead** (or the stewardship committee, per firm policy) must
adjudicate before it informs any objective, position, or vote. Choosing an engagement
objective, representing a firm position, and casting a vote are **human decisions** the brief
never makes. Approver roles are recorded on the brief; approval itself is captured outside this
skill.

## Failure handling
- **Structurally unusable log** (missing required fields) → `validate_input` errors; stop and
  report exactly what is missing. Do not assemble a partial brief silently.
- **Uncited progress / missing owners / future-dated entries** → keep them, flag them in the
  brief as data-quality warnings; never fabricate a citation or an owner.
- **Overdue commitment with no disclosed progress** → status `overdue-no-disclosure` (a
  factual date observation, not a judgment that the issuer failed).
- **Conflicting sources** → present both with dates; do not resolve on the firm's behalf.
- **A request to choose an objective, state a view, or vote** → refuse and route (handoffs).
- **Tool timeout / partial data** → return the partial brief with an explicit incomplete flag;
  assume no retry and no step-up authorization.

## Output contract
1. **Engagement History Brief** (draft) rendered from
   [assets/output-template.md](assets/output-template.md) with: issuer profile;
   reverse-chronological engagement chronology; commitments matched to disclosed progress with
   factual status; attendee roll-up by role; deduplicated source documents; unresolved
   follow-ups; **Engagement objective = unset** and **Firm position = not represented** (with
   reasons); handoffs; human-review block; standing note.
2. **Machine-readable brief** — the `sections` object keyed by `brief_id`, with a `summary`
   (engagement / commitment / follow-up counts) and `provenance` (`brief_version`,
   `source_hierarchy_version`, `as_of_date`).
3. **Data-quality notes** — the `validate_input` warnings (uncited, missing-owner, overdue,
   future-dated) surfaced for the analyst.
4. **Standing note** — "Draft engagement history only; this brief does not choose an
   engagement objective or represent a firm position, and casts or proposes no vote."
See [references/controls.md](references/controls.md).

## Privacy and records
**Highly Confidential (MNPI / client-confidential).** Engagement content may contain material
non-public information and client-attributable holdings. Minimize to what the brief needs;
carry issuer-side attendees at **role level** with de-identified ids; do not export MNPI to
unauthorized destinations. Retain the brief, its citations, and the `brief_version` /
`source_hierarchy_version` per the firm's stewardship recordkeeping and (where applicable) the
Stewardship Code disclosure regime. Log the analyst identity on every assembly.

## Gotchas
- **Assembly is not assessment.** "Progress disclosed" means the issuer *said* something and
  cited it — it does **not** mean the commitment was met. Judging substance is the analyst's
  call, not the brief's.
- **The objective stays empty on purpose.** A blank *Engagement objective* is the control
  working, not a missing field. Filling it is out of scope and fails validation.
- **Never speak for the firm.** No "we support / oppose", no "the firm's view is", no vote
  recommendation — even as a convenience summary. That is `proxy-voting-reviewer` /
  `proxy-voting-reviewer` territory and, ultimately, a human decision.
- **Citations are load-bearing.** An uncited claim is not "low confidence"; it fails closed.
  Every row must trace to a source ref.
- **Versioned contracts.** Record `brief_version` and `source_hierarchy_version` so the brief
  is reproducible and reviewable.

## Phase 1 support boundary

Supplied engagement chronology and commitment progress; full stewardship outcomes planned

This package performs only its documented local supplied-input operations. Live source access, authenticated permissions, production engines and professional acceptance are separate deployment requirements. Generated resources are pinned in `references/package-manifest.json`; maintain the canonical shared source. Legacy identifiers resolve through the repository migration registry.
