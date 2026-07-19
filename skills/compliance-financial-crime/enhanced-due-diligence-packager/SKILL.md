---
name: enhanced-due-diligence-packager
description: >-
  Assemble a higher-risk customer's enhanced due diligence (EDD) evidence — source of funds,
  source of wealth, beneficial ownership and control, geographic exposure, adverse media,
  PEP/sanctions screening, expected activity, and monitoring controls — into a controlled,
  source-mapped draft EDD package with a documented residual-risk indicator and a
  recommendation for adjudication. Use when an EDD investigator or compliance officer must
  compile an EDD dossier for a high-risk onboarding, periodic review, or trigger-based EDD
  (PEP, high-risk geography, adverse media, opaque ownership), map every assertion to an
  approved source, flag evidence gaps, and route for committee/senior sign-off. HARD
  BOUNDARY: drafts and packages only — it never makes or communicates an
  onboarding, retention, or exit decision, never changes a risk rating of record, closes a
  case, files a SAR or regulatory report, writes a system of record, or sends/submits the
  package; every regulated decision and filing stays with the human adjudicator.
license: MIT
compatibility: Amazon Quick Desktop; requires KYC/AML, sanctions/PEP-screening, transaction-monitoring, case-management, regulatory-corpus, and records-archive MCP integrations (all read-only), plus document-intelligence and approved-source retrieval for citations.
metadata:
  aws-fsi-category: "Compliance & Financial Crime"
  aws-fsi-skill-type: "Artifact-creation skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Draft & package"
  aws-fsi-agent-pattern: "Interactive production copilot"
  aws-fsi-delivery-wave: "Wave 3 - regulated casework"
  aws-fsi-action-mode: "Draft-only; no system-of-record change"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Restricted (AML/BSA — SAR confidentiality; tipping-off controls)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Compliance & Financial Crime (FIU)"
  aws-fsi-primary-user: "EDD investigator / compliance officer"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Enhanced Due Diligence Packager

## Purpose and outcome
Take a higher-risk customer's due-diligence evidence and marshal it into a controlled,
source-mapped **draft EDD package** that a compliance adjudicator can decide on. For each
required section — source of funds (SoF), source of wealth (SoW), ownership and control,
geography, adverse media, PEP/sanctions screening, expected activity, and monitoring — the
package records the evidence, maps it to an approved source, and flags what is missing. It
computes a **documented residual-risk indicator** and attaches a **recommendation for
adjudication**. The outcome is an audit-ready package queued for human sign-off — the
onboarding/retention/exit decision, any risk-rating change of record, and any filing remain
with the adjudicator. This skill matches [assets/output-template.md](assets/output-template.md).

## Use when
- "Assemble the EDD package for this high-risk PEP onboarding."
- "Compile the enhanced due diligence dossier for this periodic high-risk review."
- "Package the SoF/SoW, ownership, geography, and adverse-media evidence for sign-off."
- "Which EDD evidence is still missing before this goes to committee?"

## Do not use
- To **decide** onboarding/retention/exit, or to communicate any such decision → that is the
  human adjudicator's call (committee / MLRO / senior management).
- To **change a customer risk rating of record** → `customer-risk-rating-reviewer` proposes;
  the write is a separate authorized action.
- To **verify beneficial ownership** as the primary task → `beneficial-ownership-verifier`.
- To **investigate/disposition adverse media** → `adverse-media-investigator`.
- To **adjudicate a sanctions match** → `sanctions-match-adjudicator`.
- To **draft or file a SAR** → `suspicious-activity-report-drafter` (draft-only, human-filed).
- Any request to **close a case, file, send/submit, or write a system of record** → refuse;
  package and route to a human.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill sits **downstream** of
first-line screening/triage and **upstream** of the human adjudication that decides the
relationship. It emits a durable `case_id` + draft package and pulls corroboration from
specialist skills; it must not perform their work or the adjudicator's.

## Inputs and prerequisites
- An EDD case-intake object: `config_version`, `case_id`, `customer` (id, type,
  `risk_rating_of_record`, `edd_trigger[]`), `required_approvals[]`, `recorded_approvals[]`,
  `risk_factors{}`, and the nine `evidence{}` sections with items and citations. Schema and
  field list: [scripts/validate_input.py](scripts/validate_input.py).
- Read access to KYC/AML, sanctions/PEP screening, transaction monitoring, case management,
  the regulatory corpus (e.g., FATF high-risk lists), and the records archive — all read-only.
- The **approved output template** and the **residual-risk weighting** are versioned config.

## Source hierarchy
See [references/source-map.md](references/source-map.md). Case management is the system of
record for case state and the `case_id`; KYC/AML for customer, SoF/SoW, and ownership;
screening for PEP/sanctions/adverse-media; the regulatory corpus for geography lists. **Cite
every evidence item.** An uncited assertion is treated as unsupported and downgraded to a gap.

## Workflow
1. **Validate intake** — run [scripts/validate_input.py](scripts/validate_input.py); fail
   closed on structural problems, warn on evidence gaps (they force `needs-evidence`).
2. **Marshal evidence (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py): builds each of the
   nine sections with status `present`/`gap` and citations; a section without cited items is
   a **gap**, not an assertion.
3. **Score residual risk (documented)** — the same script computes a residual-risk indicator
   from explainable factors (PEP status, high-risk-geography nexus, adverse-media severity,
   ownership opacity, cash-intensity, channel, SoF/SoW consistency) → band Low/Medium/High.
   A **sanctions true-match** is a hard boundary → `blocked` + specialist route.
4. **Set packaging status** — `blocked` (hard boundary) → `needs-evidence` (any gap) →
   `ready-for-adjudication` (complete, no hard boundary). Never a decision state.
5. **Attach recommendation + routes + approval ledger** — an advisory review path, specialist
   corroboration routes, and the required-approval ledger (all pending in a fresh draft).
6. **Validate output** — run [scripts/validate_output.py](scripts/validate_output.py); fail
   closed on any control breach. Present the package for human adjudication; do not send it.

## Validation loop
Run `validate_input` before and `validate_output` after. The output check enforces: allowed
draft status only (no decision/closure state); all required template sections present; no
unsupported claims (present sections carry citations); required approvals recorded; residual
risk is a bounded indicator; hard-boundary consistency; and screens for decision/closure,
filing, and send/submit language. Fail closed on any miss. See
[references/controls.md](references/controls.md) and [references/domain-rules.md](references/domain-rules.md).

## Human approval
`required`. This skill packages and recommends; a human adjudicator decides. Every onboarding/
retention/exit decision, every risk-rating change of record, every case closure, and every
filing require the authorized human role (EDD investigator, MLRO/BSA Officer, senior
management as configured). Obtaining the recorded approvals is the human step — the draft
merely lists them as pending.

## Failure handling
- **Missing/uncited evidence** → mark the section a **gap**, set `needs-evidence`, list what is
  missing; never fill a gap by assumption.
- **Sanctions true-match** → hard boundary: `blocked`, route to `sanctions-match-adjudicator`;
  make no disposition.
- **Ambiguous ownership / adverse-media** → package the evidence and route to the specialist
  for corroboration; do not conclude.
- **Stale/conflicting sources** → cite both with dates/versions and flag the conflict; do not
  silently pick one.
- **Tool timeout / partial data** → return a partial draft with an explicit incompleteness
  flag and `needs-evidence`; assume no automatic retry.

## Output contract
1. **Draft EDD package** — the fifteen template sections (nine evidence + trigger/scope,
   residual-risk, recommendation, approvals, sources, standing note), each cited, keyed to
   [assets/output-template.md](assets/output-template.md).
2. **Packaging status** — `ready-for-adjudication` | `needs-evidence` | `blocked` (never a
   decision).
3. **Residual-risk indicator** — band + score + documented factors (to inform, not decide).
4. **Recommendation + routes** — advisory review path and specialist corroboration handoffs.
5. **Approval ledger** — every required role with status (pending until a human signs).
6. **Machine-readable** — the package JSON keyed by `case_id`.
7. **Standing note** — draft-only; no decision, rating change, filing, system write, or send.

## Privacy and records
**Restricted — AML/BSA.** SAR-confidentiality and tipping-off controls apply: never produce
customer-facing text that reveals monitoring or SAR activity. Mask customer/account
identifiers to what the evidence requires (`customer_ref` is masked). Retain the package,
citations, and config/template versions per BSA recordkeeping; log every read and every
package assembly with the investigator identity. Do not compile personal data beyond the EDD
scope.

## Gotchas
- **Packaging ≠ deciding.** `ready-for-adjudication` means "complete and queued," not
  "approved." The relationship decision is always a human's.
- **A gap is not a pass.** An uncited or missing section is a gap that forces `needs-evidence`;
  it is never quietly asserted as satisfied.
- **Hard boundary fails closed.** A sanctions true-match blocks the package and routes to the
  specialist — this skill never adjudicates the match.
- **Residual risk is an indicator, not the rating of record.** It informs adjudication; it does
  not change the customer's rating in any system.
- **Draft-only.** The package is never sent, submitted, or filed by this skill; delivery and
  filing are separate authorized human actions.
- **Tipping-off is a legal risk.** Keep all output internal to the EDD/adjudication workflow.
