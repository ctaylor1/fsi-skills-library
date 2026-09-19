---
name: reinsurance-contract-reviewer
description: "Interpret a reinsurance treaty in plain language — attachment, per-occurrence and aggregate limits, exclusions, reinstatements, and reporting/notice conditions, and how a ceded recovery is illustrated under the layer terms — with every statement and figure tied to the exact treaty article, slip line, or endorsement clause. Use when a reinsurance analyst or ceded-claims specialist asks \"what does this treaty cover\", \"where does the layer attach and what is the limit\", \"how do reinstatements work\", or attaches a treaty wording, slip, or loss bordereau and wants a clause-level walkthrough or an illustrative ceded-recovery calculation. Informational only: it never makes a binding coverage or recoverability determination on a specific claim, decides what to bill, collect, reserve, or book, opines on a dispute or commutation, or gives legal, actuarial, or accounting advice — route those to a licensed specialist or the appropriate reserving, claims, or wording-comparison skill."
license: MIT
compatibility: Python 3.10+; offline structured inputs and supplied source evidence. Expected source systems are not bundled production connectors.
metadata:
  aws-fsi-category: "Insurance"
  aws-fsi-skill-type: "Guidance or domain-expertise skills"
  aws-fsi-risk-tier: "R2"
  aws-fsi-archetype: "Explain & summarize"
  aws-fsi-agent-pattern: "Interactive decision-support copilot"
  aws-fsi-delivery-wave: "Insurance Phase 1"
  aws-fsi-action-mode: "Read-only analysis"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "existing-updated"
  aws-fsi-human-approval: "external-delivery"
  aws-fsi-data-classification: "Highly Confidential (customer NPI/PII)"
  aws-fsi-jurisdictions: "Reviewed target-specific jurisdiction/product profiles required; fixture coverage is not global applicability"
  aws-fsi-owner: "Reinsurance contract and claims specialists"
  aws-fsi-primary-user: "Reinsurance analyst / ceded claims specialist"
  aws-fsi-version: "0.2.0"
  aws-fsi-recertification-date: "2027-09-18"
---

# Reinsurance Treaty Interpreter

## Implemented scope and evidence contract

Clause explanation supports supplied contract wording. Numeric illustration supports only one excess-of-loss layer on an explicitly reviewed losses-occurring basis, with sourced eligibility for every loss, ascending dates within the period and explicit aggregate terms. Reinstatement math supports only `pro_rata_amount_on_erosion`; unsupported contract types, attachment bases or premium methods retain explanation with no recovery illustration. Never infer eligibility from a peril keyword or apply XoL math to quota share/facultative labels.

All output artifacts include the portable insurance evidence contract and source snapshot. Missing actor, versioned source, date or upstream context remains explicitly partial. Content hashes detect changes; they do not authenticate sources or grant approval. After authoring narrative, rebuild `artifact` with `build_artifact` from `scripts/insurance_contract.py` before running output validation. A common envelope does not replace the receiver's native input validator.

## Purpose and outcome
Turn one reinsurance treaty into a faithful, plain-language interpretation so a reinsurance
analyst or ceded-claims specialist understands exactly what the treaty **says** and how its
mechanics work. A successful output restates the attachment, per-occurrence and aggregate
limits, exclusions, reinstatement mechanics, and reporting/notice conditions in ordinary
language — each statement tied to the exact treaty article, slip line, or endorsement clause
— and, where loss figures are supplied, produces an **illustrative** ceded-recovery
calculation under the layer terms. It does this **without** making a binding coverage or
recoverability determination on any specific claim and **without** any legal, actuarial, or
accounting advice.

## Use when
- "What does this treaty cover", "walk me through this slip / wording / cover note".
- "Where does the layer attach and what is the per-occurrence / aggregate limit" ("10 xs 5").
- "How do the reinstatements work", "how many reinstatements and at what premium".
- "What are the reporting / notice / loss-bordereau requirements under this treaty".
- "Illustrate the ceded recovery for these occurrence losses under the layer terms."
- A reinsurance analyst or ceded-claims specialist attaches a treaty wording, slip, or loss
  bordereau and wants a clause-level walkthrough (external delivery requires human review —
  see Human approval).

## Do not use
- The user asks whether a **specific loss/claim is (or would be) recoverable, covered, or
  excluded** → that is a coverage/recoverability determination; do not answer it. State that
  it is a ceded-claims decision and route to the ceded reinsurance claims function and, where
  wording is disputed, to reinsurance counsel.
- The user wants a **form/version/wording comparison** against a prior treaty, filed form, or
  the placed slip → route to `policy-wording-comparator` (R3).
- The user needs **ceded reserve development, severity/frequency, or IBNR** work → route to
  `pc-reserving-analysis-assistant`.
- The user asks about **catastrophe accumulation, event footprint, or modeled loss ranges** →
  route to `catastrophe-exposure-monitor`.
- The user wants a **specific ceded-claim file** reviewed for coverage evidence, chronology,
  or reserve support → route to `claim-file-quality-reviewer`.
- The user wants to interpret the **underlying direct policy** wording → `policy-document-explainer`.
- The user wants advice on **billing, collecting, commuting, disputing, or booking** a
  recoverable, or legal/actuarial/accounting advice → out of scope; do not answer it here.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). In short: this skill produces a
plain-language treaty interpretation plus a normalized interpretation object (including any
illustrative recovery) tagged with a durable `interpretation_id`, then stops. It hands off to
`policy-wording-comparator` (wording/version comparison), `pc-reserving-analysis-assistant`
(ceded reserving), `catastrophe-exposure-monitor` (accumulation/modeled loss),
`claim-file-quality-reviewer` (a specific ceded-claim file), and `policy-document-explainer` (the
underlying direct policy). It never determines recoverability, bills, reserves, or advises.

## Inputs and prerequisites
- One treaty at a time: `treaty_id`, `cedent`, `treaty_type` (e.g. `excess_of_loss`),
  underwriting year, currency, inception/expiry dates, the treaty broken into `clauses` with
  `clause_type`, heading, text, and a source citation, and — for excess-of-loss — a `layer`
  (attachment, limit, reinstatements, aggregate limit, layer premium). Optional `losses`
  (occurrence id, date, gross loss) drive the illustration. See the schema in
  [scripts/validate_input.py](scripts/validate_input.py).
- The **inception/expiry dates** and underwriting year, so the reader knows which treaty
  period is being interpreted. Reject a treaty whose expiry precedes its inception.
- Read permission to the reinsurance-contract/treaty register and/or document-intelligence
  extraction of the attached wording; approved-source retrieval for any referenced filed form
  or standard clause; claims/policy-administration for occurrence loss figures.

## Source hierarchy
Rank sources and cite every statement and figure. See [references/source-map.md](references/source-map.md).
1. Reinsurance-contract **system of record / treaty register** (highest): placed treaty,
   endorsements, layer terms, effective dates.
2. The **executed treaty wording / slip / cover note** for the stated period (via
   document-intelligence) with article/clause/line citations.
3. **Claims and policy-administration** (loss bordereaux, cessions) for occurrence and loss
   figures used in the illustration.
4. **Actuarial / catastrophe data** for exposure context only (background, not a treaty term).
Never substitute a user assertion for the treaty of record; if they conflict, surface the
conflict and cite both. Interpret the **wording as written** — do not resolve ambiguity by
guessing intent.

## Workflow
1. **Scope one treaty** — confirm a single `treaty_id`, treaty period, and underwriting year.
   If multiple treaties, layers, or periods are present, ask which one (do not merge).
2. **Validate input** — run [scripts/validate_input.py](scripts/validate_input.py): required
   fields, valid dates (expiry not before inception), a citable source on every clause, and a
   well-formed `layer` for excess-of-loss. Fail closed on errors; carry warnings (missing
   aggregate limit, below-attachment losses, unrecognized clause types) into the output as gaps.
3. **Normalize and interpret** — map each clause to the clause schema; classify it (attachment,
   limit, exclusion, reinstatement, reporting, definition, condition, recoverability, other);
   restate it in plain language, preserving attachment, limits, reinstatement counts, and
   premium percentages exactly as written; attach the clause citation to each element.
4. **Illustrate recovery (deterministic)** — when occurrence losses are supplied, run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py) to compute, per
   occurrence, the layer loss, ceded recovery, limit erosion, reinstated amount, reinstatement
   premium, and remaining aggregate under the layer terms. See
   [references/domain-rules.md](references/domain-rules.md). Label every figure **illustrative**;
   a tie-out miss is re-checked or surfaced, never smoothed over.
5. **Surface gaps** — unreadable clauses, unresolved cross-references, missing endorsements,
   below-attachment or excluded losses, and ambiguous wording are listed explicitly, not guessed.
6. **Validate and disclaim** — run the validation loop and attach the standing disclaimer.

## Validation loop
Run `validate_input` before interpreting, `calculate_or_transform` to produce and tie out any
recovery illustration, and `validate_output` after drafting. If a clause lacks a citation, the
interpreted-clause count does not tie to the clauses listed, an illustrated recovery figure
does not tie to the layer arithmetic, the output contains a binding coverage/recoverability
determination or legal/actuarial/accounting advice, or the standing disclaimer is missing,
**fix or fail closed** — do not deliver a determination-tainted, untied, or uncited
interpretation. See [references/controls.md](references/controls.md).

## Human approval
None required for the analyst's own informational read. **Human review is required before the
interpretation is delivered externally** (e.g., to the cedent, broker, or reinsurer) or written
to a system of record — `aws-fsi-human-approval: external-delivery`. A binding recoverability
decision always requires the authorized ceded-claims function, not this skill.

## Failure handling
- **Unreadable / partial wording** → interpret the clauses that are legible, list the rest as
  "not readable — not interpreted"; never invent wording.
- **Missing layer terms or dates** → state that the term is unconfirmed and interpret
  conservatively; do not assume a standard treaty's contents or a default reinstatement count.
- **Unresolved cross-reference / missing endorsement** → name it as a data gap; do not describe
  an endorsement that was not provided.
- **Loss below attachment** → illustrate zero only on the supplied reviewed basis. Unknown eligibility, unsupported attachment basis or missing dates prevents the aggregate illustration. A sourced `eligible_for_illustration: false` may represent a reviewer-supplied exclusion; never decide it from wording here.
- **Multiple treaties / layers / periods in one file** → stop and ask; do not merge.
- **Source conflict** (user statement vs. treaty of record, or slip vs. register) → present both
  with citations; do not pick a winner.
- **A recoverability / claim-outcome question** → do not answer it; interpret the relevant clause
  neutrally and route to the ceded-claims function / reinsurance counsel.
- **Tool timeout / permission denial** → report partial results and the exact gap; no retry
  assumption.

## Output contract
1. **Header** — treaty label (masked), cedent, treaty type, underwriting year, currency,
   inception/expiry dates.
2. **Layer summary** — attachment, per-occurrence limit, reinstatements, aggregate limit
   ("limit xs attachment"), each cited.
3. **Clause walkthrough** — each clause in plain language (attachment, limits, exclusions,
   reinstatements, reporting/notice, definitions, conditions), cited.
4. **Recovery illustration** (when losses supplied) — per-occurrence layer loss, ceded recovery,
   cumulative ceded, remaining aggregate, reinstated amount and reinstatement premium, with the
   tie-out shown and labeled **illustrative**.
5. **Data gaps** — unreadable, missing, unresolved, below-attachment, or excluded items listed
   explicitly.
6. **Machine-readable** — the normalized interpretation object with per-clause and per-figure
   citations, tagged with a durable `interpretation_id` for downstream skills.
7. **Standing disclaimer** — "Informational interpretation only; not a coverage or
   recoverability determination, reserving or accounting decision, or legal advice."
Every statement and figure carries a source citation. See [references/controls.md](references/controls.md).

## Privacy and records
Customer NPI/PII. Mask treaty, account, and policy numbers (show last 4) and any claimant or
insured identifying details in loss data. Do not transmit the treaty or interpretation outside
the approved environment. Retain the interpretation and its citations per records policy; log
the read and any external-delivery approval. See [references/controls.md](references/controls.md).

## Gotchas
- **"Interpret" is not "determine"**: restating that the layer attaches at USD 5,000,000 is in
  scope; saying "this hurricane loss is recoverable" or "the reinsurer will pay USD 7,000,000"
  is a recoverability determination and is out of scope.
- **Reinstatements restore the limit, at a price**: after a loss erodes the per-occurrence limit,
  a reinstatement restores it for further occurrences and triggers a **reinstatement premium**
  (often "pro rata as to amount, 100% as to time"); the aggregate limit is
  `limit × (1 + reinstatements)`. Reproduce the count and premium percentage exactly.
- **Occurrence vs. aggregate limit**: the per-occurrence limit caps a single event; the annual
  aggregate caps the treaty year. A single occurrence never recovers more than the per-occurrence
  limit, and the year never recovers more than the aggregate — keep them distinct.
- **Attachment / retention is net of the layer**: only the part of each occurrence above the
  attachment enters the layer, and only up to the limit ("10 xs 5" yields 7 on an eligible 12 loss before aggregate effects).
- **Exclusions erode nothing**: a loss caused by an excluded peril does not attach or erode the
  limit — show it as excluded, do not net it into recoveries.
- **Hours clause / occurrence definition**: whether events aggregate into one occurrence is
  defined by the treaty (e.g. a 72-hour clause); interpret the definition as written, do not
  decide how a real event aggregates.
- **Ambiguity is a finding, not a gap to fill**: if wording is genuinely ambiguous, say so and
  route to reinsurance counsel — do not resolve it for or against the cedent.

## Evidence and handoff contract

Read [the insurance evidence contract](references/insurance-contract.md) for source
versioning, explicit unknowns, financial/date bases and receiver validation. A
content hash is not source authentication, professional approval or execution authority.
