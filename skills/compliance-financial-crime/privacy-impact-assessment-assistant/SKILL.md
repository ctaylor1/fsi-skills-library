---
name: privacy-impact-assessment-assistant
description: >-
  Draft a privacy / data-protection impact assessment (PIA/DPIA) for a processing activity:
  marshal purpose, personal-data inventory, legal basis and necessity/proportionality, data
  sharing and international transfers, retention, security, data-subject rights, and risk
  mitigations into a controlled, source-mapped draft with a documented privacy-risk indicator
  and a sign-off recommendation. Use when a privacy officer, product risk owner, or legal
  reviewer must compile a DPIA for a new or changed processing activity (large-scale profiling,
  AI, special-category data, systematic monitoring, high-risk transfer), map every assertion to
  an approved source, flag gaps, and route for DPO/senior sign-off. HARD BOUNDARY: drafts and
  packages only — it never approves or clears the processing, sets a lawful basis of record,
  closes a case, files a DPIA or initiates prior consultation, writes a system of record, or
  sends/submits the assessment; every privacy decision stays with the human adjudicator.
license: MIT
compatibility: Amazon Quick Desktop; requires privacy/DPIA-register (case-management), records-of-processing/data-inventory, data-lineage, privacy-program-artifacts, regulatory-corpus, information-security/TPRM, and records-archive MCP integrations (all read-only), plus document-intelligence and approved-source retrieval for citations.
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
  aws-fsi-primary-user: "Privacy officer / product risk / legal"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Privacy Impact Assessment Assistant

## Purpose and outcome
Take a processing activity's privacy evidence and marshal it into a controlled, source-mapped
**draft PIA/DPIA** that a privacy adjudicator can sign off. For each required section —
processing purpose, personal-data inventory, legal basis and necessity/proportionality, data
sharing and international transfers, retention, security, data-subject rights, and mitigations —
the assessment records the evidence, maps it to an approved source, and flags what is missing.
It computes a **documented privacy-risk indicator** (risk to the rights and freedoms of data
subjects) and attaches a **recommendation for sign-off**. The outcome is an audit-ready
assessment queued for human decision — the approval of the processing, any lawful basis of
record, and any filing or prior consultation remain with the adjudicator. This skill matches
[assets/output-template.md](assets/output-template.md).

## Use when
- "Draft the DPIA for this AI-assisted, large-scale profiling model."
- "Compile the privacy impact assessment for this new processing activity for DPO sign-off."
- "Map the purpose, data, legal basis, sharing, retention, security, rights, and mitigations to sources."
- "Which privacy evidence is still missing before this DPIA can go to the DPO?"

## Do not use
- To **approve / authorize / clear the processing to go live**, or communicate any such
  decision → that is the human adjudicator's call (DPO / privacy officer / legal / senior mgmt).
- To **set or change a lawful basis of record** in the RoPA/system → separate authorized action.
- To **map data lineage** as the primary task → `data-lineage-documenter`.
- To **assess processor / third-party risk** → `third-party-risk-assessor`.
- To **build the AI risk assessment** for an automated-decision/AI use case → `ai-risk-assessment-builder`.
- To **decide a data-subject request** (access/erasure/objection) → not this skill.
- Any request to **close a case, file, initiate prior consultation, send/submit, or write a
  system of record** → refuse; package and route to a human.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill sits **downstream** of the
intake that flags a processing activity for a DPIA and **upstream** of the human sign-off that
authorizes the processing. It emits a durable `assessment_id` + draft assessment and pulls
corroboration from specialist skills; it must not perform their work or the adjudicator's.

## Inputs and prerequisites
- A PIA/DPIA intake object: `config_version`, `assessment_id`, `processing` (id, name,
  `business_owner_role`, `dpia_trigger[]`, masked `processing_ref`), `required_approvals[]`,
  `recorded_approvals[]`, `risk_factors{}`, and the eight `evidence{}` sections with items and
  citations. Schema and field list: [scripts/validate_input.py](scripts/validate_input.py).
- Read access to the privacy/DPIA register, records of processing / data inventory, data
  lineage, privacy-program artifacts (LIA/TIA/notices), the regulatory corpus, information
  security / TPRM assurance, and the records archive — all read-only.
- The **approved output template** and the **privacy-risk weighting** are versioned config.

## Source hierarchy
See [references/source-map.md](references/source-map.md). The DPIA register is the system of
record for assessment state and the `assessment_id`; RoPA/data inventory for the processing and
data categories; the regulatory corpus for lawful-basis conditions and transfer mechanisms.
**Cite every evidence item.** An uncited assertion is treated as unsupported and downgraded to
a gap.

## Workflow
1. **Validate intake** — run [scripts/validate_input.py](scripts/validate_input.py); fail
   closed on structural problems, warn on evidence gaps (they force `needs-information`).
2. **Marshal evidence (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py): builds each of the
   eight sections with status `present`/`gap` and citations; a section without cited items is a
   **gap**, not an assertion.
3. **Score privacy risk (documented)** — the same script computes a privacy-risk indicator from
   explainable factors (special-category/criminal data, children/vulnerable subjects, scale,
   systematic monitoring, automated decisions, novel technology, high-risk transfers, matching,
   over-retention) → band Low/Medium/High. An **unlawful-processing indicator** (no lawful
   basis, special-category data with no Art 9 condition, transfer with no mechanism) is a hard
   boundary → `blocked` + privacy-counsel route.
4. **Set packaging status** — `blocked` (hard boundary) → `needs-information` (any gap) →
   `ready-for-adjudication` (complete, no hard boundary). Never a decision state.
5. **Attach recommendation + routes + approval ledger** — an advisory review path (with a
   prior-consultation flag when residual risk is High), specialist corroboration routes, and the
   required-approval ledger (all pending in a fresh draft).
6. **Validate output** — run [scripts/validate_output.py](scripts/validate_output.py); fail
   closed on any control breach. Present the assessment for human sign-off; do not send it.

## Validation loop
Run `validate_input` before and `validate_output` after. The output check enforces: allowed
draft status only (no decision/sign-off state); all required template sections present; no
unsupported claims (present sections carry citations); required approvals recorded; privacy risk
is a bounded indicator; hard-boundary consistency; and screens for decision/sign-off, filing,
and send/submit language. Fail closed on any miss. See [references/controls.md](references/controls.md)
and [references/domain-rules.md](references/domain-rules.md).

## Human approval
`required`. This skill packages and recommends; a human adjudicator decides. Every approval of
the processing, every lawful basis of record, every case closure, every filing, and any prior
consultation with a supervisory authority require the authorized human role (privacy officer,
DPO, legal / senior management as configured). Obtaining the recorded approvals is the human
step — the draft merely lists them as pending.

## Failure handling
- **Missing/uncited evidence** → mark the section a **gap**, set `needs-information`, list what
  is missing; never fill a gap by assumption.
- **Unlawful-processing indicator** → hard boundary: `blocked`, route to privacy counsel / the
  DPO; make no disposition.
- **Ambiguous transfer / ADM / processor question** → package the evidence and route to the
  specialist for corroboration; do not conclude.
- **Stale/conflicting sources** → cite both with dates/versions and flag the conflict; do not
  silently pick one.
- **Tool timeout / partial data** → return a partial draft with an explicit incompleteness flag
  and `needs-information`; assume no automatic retry.

## Output contract
1. **Draft PIA/DPIA** — the fourteen template sections (eight evidence + scope/trigger,
   privacy-risk, recommendation, approvals, sources, standing note), each cited, keyed to
   [assets/output-template.md](assets/output-template.md).
2. **Packaging status** — `ready-for-adjudication` | `needs-information` | `blocked` (never a
   decision).
3. **Privacy-risk indicator** — band + score + documented factors (to inform, not decide),
   with an advisory prior-consultation flag when High.
4. **Recommendation + routes** — advisory review path and specialist corroboration handoffs.
5. **Approval ledger** — every required role with status (pending until a human signs).
6. **Machine-readable** — the assessment JSON keyed by `assessment_id`.
7. **Standing note** — draft-only; no decision, lawful-basis of record, filing, prior
   consultation, system write, or send.

## Privacy and records
**Restricted.** The assessment describes personal data but must **not embed actual personal
data** — cite sources and use category-level descriptions and the masked `processing_ref` (data
minimization applies to the assessment itself). Where the processing touches AML/BSA casework,
SAR-confidentiality and tipping-off controls still apply: never produce customer-facing content
revealing monitoring or SAR activity. Retain the assessment, citations, and config/template
versions per records-retention policy; log the author identity on every read and every assembly.

## Gotchas
- **Packaging ≠ deciding.** `ready-for-adjudication` means "complete and queued," not
  "approved." The processing decision is always a human's.
- **A gap is not a pass.** An uncited or missing section is a gap that forces
  `needs-information`; it is never quietly asserted as satisfied.
- **Hard boundary fails closed.** An unlawful-processing indicator blocks the assessment and
  routes to privacy counsel — this skill never rules the processing lawful.
- **The risk band is an indicator, not a decision.** It informs sign-off and whether prior
  consultation may apply; it does not authorize anything or set a lawful basis of record.
- **Draft-only.** The assessment is never sent, submitted, filed, or used to initiate prior
  consultation by this skill; those are separate authorized human actions.
- **Minimize inside the DPIA.** Do not paste raw personal data into the assessment; describe
  categories and cite the source system.
