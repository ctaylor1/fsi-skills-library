---
name: contract-obligation-extractor
description: >-
  Extract a contract's obligations, key dates, service levels, rights, restrictions, renewal
  and termination terms, data terms, and dependencies into ONE source-linked draft obligation
  register, with a clause-level citation on every item. Use when a legal-operations,
  procurement, or business owner asks to pull the obligations/deadlines/SLAs out of a contract,
  build or update an obligation register or deadline calendar, map contract terms to a required
  taxonomy, or flag ambiguous or conflicting terms for review. HARD BOUNDARY: draft-only and
  citation-bound — this skill never gives legal advice or interprets enforceability, breach, or
  liability; never asserts an obligation without a clause citation; never claims the register is
  complete/exhaustive or that the contract is silent (absence is a coverage gap to confirm);
  never fabricates terms; and never sends, submits, signs, executes, or delivers the register or
  contract. It extracts, cites, and flags; humans review, advise, and decide.
license: MIT
compatibility: Amazon Quick Desktop; requires contract/CLM, document-intelligence, contract-taxonomy, and procurement/vendor-master MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Enterprise Functions & Technology"
  aws-fsi-skill-type: "Artifact-creation skills"
  aws-fsi-risk-tier: "R2"
  aws-fsi-archetype: "Draft & package"
  aws-fsi-agent-pattern: "Interactive production copilot"
  aws-fsi-delivery-wave: "Wave 2 - analytical production"
  aws-fsi-action-mode: "Draft-only; no system-of-record change"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "external-delivery"
  aws-fsi-data-classification: "Confidential"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Enterprise Functions & Technology"
  aws-fsi-primary-user: "Legal operations / procurement / business owner"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Contract Obligation Extractor

## Purpose and outcome
Turn an executed contract into ONE **source-linked, clause-cited draft obligation register**.
For each required taxonomy category the skill maps the extracted terms to their governing
clause, assigns an extraction status (`extracted`, `ambiguous`, `conflict`, `unsourced`, or
`coverage-gap`), and compiles an explicit open-items list — every asserted obligation carries a
clause citation. The outcome is a register a human can review and route: a rendered register
from [assets/output-template.md](assets/output-template.md) plus a machine-readable manifest.
The skill **extracts and cites**; it does not interpret enforceability, monitor obligations, or
decide anything.

## Use when
- "Pull the obligations, deadlines, and SLAs out of this contract with citations."
- "Build / update the obligation register (or deadline calendar) for this agreement."
- "Map this contract's terms to our obligation taxonomy and list what's missing."
- "Flag the ambiguous or conflicting terms in this contract for legal to review."
- "Summarize the renewal, termination, and data-protection terms with clause references."

## Do not use
- **Legal advice / interpretation** (enforceability, validity, breach, liability, negotiation,
  redlining, "can we terminate?") → licensed legal counsel; never performed here.
- **Ongoing covenant / threshold monitoring** after extraction → `covenant-compliance-monitor`.
- **Counterparty / vendor risk assessment** driven by the terms → `third-party-risk-assessor`.
- **Turning obligations into tracked tasks / deadlines** in a tracker → `meeting-action-tracker`.
- Any request to **decide, certify completeness, sign, execute, or deliver** → refuse; route to
  a human via the approval broker.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). Extraction is deliberately separated from
legal interpretation, obligation monitoring, and external delivery (distinct controls,
entitlements, and accountability). This skill emits a durable `register_id` + clause-cited
manifest and hands off downstream; it must not perform counsel's, the monitor's, or the
deliverer's work.

## Inputs and prerequisites
- The intake bundle: `config_version`, `register_id`, `as_of_date`, the `contract` metadata,
  the required `taxonomy` (categories to cover), the source `clauses` (each with `clause_id`,
  heading, text, and `source_ref`), the candidate `extractions` (each with a category, a
  `clause_ref`, a summary, and where relevant a responsible party / due date / terms),
  `required_reviews`, and recorded `reviews`. Schema and required fields:
  [scripts/validate_input.py](scripts/validate_input.py).
- Read access to contract/CLM, document-intelligence, taxonomy, and vendor-master sources (all
  read-only). No term is fabricated: what is not in a clause becomes an open item.

## Source hierarchy
See [references/source-map.md](references/source-map.md). The CLM system is the system of record
for the executed contract, metadata, and recorded reviews; document intelligence provides the
clause text and citations; the taxonomy defines which categories are required. Cite every item
as `{system}:{ref}@{date/version}`. The `taxonomy`, template, and review requirements are
**versioned contracts**.

## Workflow
1. **Validate & normalize** — run `validate_input`; confirm the intake structure and surface
   data gaps (extractions with no resolvable clause, taxonomy categories with no extraction,
   missing required reviews) as warnings.
2. **Assemble the register (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py): resolve each
   extraction's clause citation, assign its status, route it to the right register section,
   capture recorded reviews plus outstanding required reviews, and build the citation source
   index. Rules: [references/domain-rules.md](references/domain-rules.md).
3. **Render the register** — populate [assets/output-template.md](assets/output-template.md)
   from the manifest; every extracted/ambiguous/conflict item carries its clause citation.
4. **Compile open items** — everything not cleanly `extracted` (ambiguous parties, conflicting
   terms, unsourced extractions, coverage gaps, outstanding reviews) becomes an explicit open
   item. Do not silently drop, resolve, or assume silence.
5. **Mark draft & hand off** — set `assembly_status: draft-extracted`, record that human
   approval is required before delivery, and route downstream as needed. Never advise, certify,
   sign, or send.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py) after.
The output check enforces: all required template sections present; every asserted
(extracted/ambiguous/conflict) item carries a clause citation (no unsupported assertions);
reviews are recorded with role, date, and citation and delivery approval is flagged as required;
no legal-advice/interpretation, completeness/exhaustiveness, or send/submit/execute/deliver
language; `assembly_status` is `draft-extracted`; standing note present. Fail closed on any miss.

## Human approval
`external-delivery`. This skill produces a **draft** register for internal review. A human must
review and approve before the register is delivered, relied on for a decision, or treated as a
system-of-record change. Legal interpretation and any negotiation, execution, or delivery are
separate, human-owned steps — this skill neither performs nor pre-empts them.

## Failure handling
- **Unsourced extraction** (no resolvable clause) → status `unsourced`; listed as a
  `needs-source` open item, never asserted as an obligation.
- **Ambiguous responsibility** (no resolvable party where required) → status `ambiguous`; cited
  and flagged for a human to assign the party; never guessed.
- **Conflicting terms across clauses** → status `conflict`; both cited and flagged for
  reconciliation; never resolved by picking one clause.
- **Coverage gap** (taxonomy category with no clause) → open item to **confirm**; never asserted
  as the contract being silent.
- **Unresolvable data / tool timeout** → return the partial register with an explicit incomplete
  flag and the open-items list; no retry assumption, no guessing.

## Output contract
See [references/controls.md](references/controls.md) and
[assets/output-template.md](assets/output-template.md).
1. **Rendered register** — the template sections (register summary, contract profile,
   obligations, key dates, service levels, rights & restrictions, renewal & termination, data
   terms, dependencies, reviews, open items, source index) populated with cited content.
2. **Machine-readable manifest** — `register_id`, per-entry status + clause citation, reviews
   (recorded/outstanding), open items, source index, `assembly_status` (`draft-extracted`), and
   `human_approval_required_before_delivery: true`.
3. **Open-items list** — every ambiguous/conflict/unsourced/coverage-gap/outstanding-review item
   with a required human action.
4. **Standing note** — "Draft obligation register for human review only. This register is an
   extraction aid, not legal advice or a completeness certification, and it has not been
   delivered, executed, or acted on. Every obligation must be verified against the source
   contract."

## Privacy and records
**Confidential.** Contracts routinely carry commercial terms, pricing, and counterparty and
personnel identifiers. Mask person/user identifiers in output to what the register requires; do
not expose pricing or personal data beyond the extracted term. Retain the register manifest,
clause citations, and config/template versions per the organization's contract recordkeeping
policy. Log every read and every extraction with the analyst identity. Data stays within the
deployment's residency boundary.

## Gotchas
- **Extraction ≠ advice.** Characterizing and citing a clause is not an opinion on
  enforceability, breach, or what to do. Those are counsel's; this skill never advises.
- **No citation, no obligation.** An extraction with no resolvable clause is an open item, not an
  assumed obligation. Every asserted item must be citable.
- **Absence is not silence.** A taxonomy category with no clause is a `coverage-gap` to confirm,
  never a statement that the contract "has no" such term.
- **Conflicts are reconciled by humans.** Two clauses with different notice periods are both
  surfaced as a `conflict`; the skill never picks one.
- **No completeness claim.** The register is an extraction aid, never "complete" or "exhaustive".
- **Versioned contracts.** Record the `taxonomy`, template, and config versions on the manifest
  so the extraction is reproducible and reviewable.
