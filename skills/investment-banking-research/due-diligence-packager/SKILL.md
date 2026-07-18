---
name: due-diligence-packager
description: >-
  Convert data-room documents into an indexed, source-mapped due-diligence pack: extract and
  cite key data, build a source index, compile an issue log and open-questions list, run
  completeness checks, and prepare structured model handoffs for the deal team. Use when a
  deal-team analyst or diligence lead needs to turn a raw data room into a reviewable
  diligence package, index and cite source documents, log diligence issues and open
  questions, or hand extracted financials to modeling skills (three-statement-model-builder,
  dcf-modeler, comps-analysis-builder). Draft-only: this skill NEVER sends, submits, emails,
  or otherwise delivers the pack to a counterparty, NEVER files or writes a system of record,
  and NEVER makes a binding recommendation, valuation opinion, or personalized investment
  advice. Every material data point must cite an indexed source; external delivery requires
  recorded human approval; unsupported or unsourced assertions fail closed.
license: MIT
compatibility: Amazon Quick Desktop; requires data-room/VDR, document-intelligence, market/financial-data, filings, research-corpus, and CRM MCP integrations (all read-only); drafting to a controlled workspace only.
metadata:
  aws-fsi-category: "Investment Banking & Research"
  aws-fsi-skill-type: "Artifact-creation skills"
  aws-fsi-risk-tier: "R2"
  aws-fsi-archetype: "Draft & package"
  aws-fsi-agent-pattern: "Interactive production copilot"
  aws-fsi-delivery-wave: "Wave 2 - analytical production"
  aws-fsi-action-mode: "Draft-only; no system-of-record change"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "external-delivery"
  aws-fsi-data-classification: "Highly Confidential (MNPI / client-confidential)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Investment Banking / Research"
  aws-fsi-primary-user: "Deal-team analyst / diligence lead"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Due Diligence Packager

## Purpose and outcome
Turn a raw data room into a **reviewable, source-mapped diligence pack**. For a defined deal,
the skill indexes source documents, extracts and cites key data points, compiles an issue log
and open-questions list, checks workstream completeness, and assembles structured **model
handoffs** so downstream modeling can start from clean, cited inputs. The outcome is an
internal draft package — every material figure ties to an indexed source — that a diligence
lead reviews and approves before any external use. Substantive modeling, valuation, and
external delivery stay with the adjacent skills and human owners.

## Use when
- "Package this data room into a diligence pack / build the diligence index."
- "Extract and source-map the key financials, issues, and open questions from these VDR docs."
- "Compile the issue log and open items for the deal-team review."
- "Prepare the extracted financials to hand to the model."

## Do not use
- **Building the financial model / valuation** (3-statement, DCF, LBO, merger, comps) →
  `three-statement-model-builder`, `dcf-modeler`, `lbo-model-builder`, `merger-model-builder`,
  `comps-analysis-builder`. This skill *hands off* cited inputs; it does not model or value.
- **Company profile / strip page** → `company-profile-builder`.
- **Deal process, NDA, access, and deadline tracking** → `transaction-process-tracker`.
- **Buyer / investor / lender universe** → `buyer-investor-list-builder`.
- Any request to **send/submit the pack, deliver to a counterparty, file, make a
  buy/sell/valuation recommendation, or give investment advice** → refuse; route to the human
  approver or the relevant specialist.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill emits a durable `pack_id`, a
cited source index, and per-target model-handoff bundles. Modeling and valuation are separate
control activities with distinct inputs and reviewers; the packager must not perform them.

## Inputs and prerequisites
- A data-room extraction manifest: the deal header (`deal_id`, as-of date, masked target), the
  `sources[]` document index (doc id, title, type, date, version, owner, index_ref),
  `extractions[]` (each with a `source_doc` and page), `issues[]`, `open_questions[]`,
  requested `model_targets[]`, and the `approvals[]` ledger. Schema and checks:
  [scripts/validate_input.py](scripts/validate_input.py).
- Read access to the VDR/data room, document-intelligence, market/financial data, filings,
  research corpus, and CRM. Drafting is to a controlled workspace only — no external send.

## Source hierarchy
See [references/source-map.md](references/source-map.md). The **data room / VDR is the system
of record** for diligence documents; every extraction, issue, and open question must cite an
indexed source document with page and version. Market/financial data and filings corroborate
but never replace a data-room citation. Conflicts are surfaced, not silently resolved.

## Workflow
1. **Validate & index** — run `validate_input`; confirm every source doc has an id, type, and
   `index_ref`; flag extractions/issues whose `source_doc` is not in the index (these become
   *unsupported claims* and cannot enter the pack).
2. **Extract & cite** — for each data point, bind `source_doc` + page + version into a
   citation; carry a confidence label. No figure without a resolvable citation.
3. **Compile issue log & open questions** — normalize severity/priority; keep each item's
   source citation and status; never mark an issue resolved on the target's behalf.
4. **Completeness check** — compare covered workstreams against the required diligence set;
   list missing workstreams explicitly rather than implying coverage.
5. **Assemble the pack (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py): produces the
   `pack_id`, source index, cited extracted-data table, issue summary, completeness, and
   validated **model-handoff bundles** (targets checked against known modeling skills).
6. **Draft the deliverable** — populate [assets/output-template.md](assets/output-template.md);
   record approvals as *pending* until a human signs off. Draft only — never send or submit.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py)
after. The output check enforces: all required template sections present; **no unsupported
claims** (every extracted-data and issue item cites a doc in the source index); model-handoff
targets are known modeling skills; **required approvals recorded** (diligence lead + quality
reviewer); no send/submit/external-delivery language; no investment recommendation, valuation
opinion, or advice language; standing note present. Fail closed on any miss.

## Human approval
`external-delivery`. The pack is an **internal draft**. A diligence lead and an independent
quality reviewer must be recorded in the approvals ledger, and both must be `approved` before
the pack is marked ready for external delivery — and the actual send is performed by a human,
never by this skill. Internal analytical use may be reviewer-sampled.

## Failure handling
- **Unsupported / unsourced data point** → exclude from the pack, list under `needs-source`;
  never fabricate or infer a citation.
- **Conflicting sources** → cite both and log an issue; do not pick a winner.
- **Missing workstream** → report the gap in completeness; do not imply coverage.
- **Unknown model-handoff target** → flag as an invalid handoff; do not invent a skill.
- **Stale document (version/date past freshness window)** → flag; require a refreshed source.
- **Tool timeout** → return the partial pack with an explicit `incomplete` flag; no retry
  assumption, no silent completion.

## Output contract
1. **Diligence pack draft** — the sections in [assets/output-template.md](assets/output-template.md):
   cover, executive summary, source index, extracted data (cited), issue log, open questions,
   completeness, model handoffs, approvals, standing note.
2. **Machine-readable pack** — the structured JSON from `calculate_or_transform` keyed by
   `pack_id` (source index, extracted data, issue summary, completeness, model handoffs).
3. **Needs-source / gaps list** — any excluded data points and missing workstreams.
4. **Standing note** — "Draft diligence pack for internal review only; not approved for
   external delivery; no valuation or investment recommendation is made."
See [references/controls.md](references/controls.md).

## Privacy and records
**Highly Confidential — MNPI / client-confidential.** Treat data-room contents as material
non-public information: mask target/counterparty identifiers to what the pack requires, apply
information-barrier and need-to-know controls, and never route content outside the deal team.
Retain the pack, source index, citations, and approval ledger with document versions per the
engagement's records policy; log every read, draft, and approval with the analyst identity.

## Gotchas
- **A citation is not a conclusion.** Extracting and sourcing a figure is packaging; judging
  whether it supports a valuation is the modeler's and deal team's job.
- **No figure without a resolvable source.** An extraction whose `source_doc` is missing from
  the index is an unsupported claim and must be excluded, not "cited to the data room."
- **Draft never ships.** The skill cannot send, email, submit, or deliver — external delivery
  is a human action gated on recorded approvals.
- **Completeness is stated, not assumed.** Always list missing workstreams; silence is not
  coverage.
- **Handoffs must be real.** Only route model bundles to known modeling skills; never invent a
  downstream skill name.
- **MNPI discipline.** The pack is highly confidential; masking and information barriers are
  not optional.
