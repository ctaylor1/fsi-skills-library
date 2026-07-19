---
name: regulatory-change-impact-analyzer
description: >-
  Analyze a regulatory change (law, regulation, supervisory guidance, or standard): capture
  authority, jurisdiction, and effective dates; extract obligations; test applicability to
  the firm's business lines; map applicable obligations to policies, controls, systems, data,
  training, and owners; flag mapping gaps, lead-time pressure, and authority conflicts; and
  recommend a disposition with cited evidence. Use when a regulatory-change analyst or
  compliance advisor asks "what does this rule change require of us", "which obligations apply
  and where are the gaps", "map this regulation to our policies and controls", or needs an
  impact-assessment pack for adjudication. This skill produces findings, cited evidence, and a
  recommended disposition ONLY; it NEVER decides applicability to close scope, determines the
  firm is/ isn't compliant, resolves a conflict, closes a change, files with a regulator, or
  attests — those are human/authorized-system actions.
license: MIT
compatibility: Amazon Quick Desktop; requires approved-source-retrieval (regulatory corpus), governance/entity-resolution (firm profile), controlled-register (policy/control/system/data/training inventory), and approved-calculation MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Compliance & Financial Crime"
  aws-fsi-skill-type: "Analysis and evaluation skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Analyze & review"
  aws-fsi-agent-pattern: "Interactive decision-support copilot"
  aws-fsi-delivery-wave: "Wave 3 - regulated casework"
  aws-fsi-action-mode: "Read-only analysis"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Restricted (AML/BSA — SAR confidentiality; tipping-off controls)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Compliance & Financial Crime (FIU)"
  aws-fsi-primary-user: "Regulatory-change analyst / compliance advisory"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Regulatory Change Impact Analyzer

## Purpose and outcome
Given a regulatory change and the firm's profile and control inventory, extract the
**obligations**, test each obligation's **applicability** to the firm, **map** applicable
obligations to owning policies/controls/systems/data/training/owners, and surface
**findings** — mapping gaps, short lead time, overdue/retroactive effective dates, and
authority conflicts — each with cited evidence. The skill recommends a **disposition band**
and the open questions a human must resolve. A successful output lets a regulatory-change
analyst or compliance advisor adjudicate scope, gaps, and priority with an evidenced,
reproducible pack — the applicability decision, conflict resolution, disposition, filing, and
closure remain human.

## Use when
- "What does this rule change require of us, and which obligations apply?"
- "Map this regulation to our policies, controls, systems, and owners — where are the gaps?"
- "How much lead time do we have, and is anything already effective or retroactive?"
- An analyst needs a consistent, cited impact-assessment pack to route for adjudication.

## Do not use
- The user wants a **compliance determination** ("are we compliant?"), an **applicability
  decision that closes scope**, a **change closed/dispositioned**, a **regulatory filing or
  attestation**, or a **conflict resolved** → out of scope. Provide evidence and route to the
  human adjudicator / authorized system.
- **Deep policy/procedure gap analysis and drafting** for a flagged gap →
  `policy-procedure-gap-analyzer`.
- **Obligations from a contract** (not a law/regulation/guidance) → `contract-obligation-extractor`.
- **Impact of a model/algorithm change** (not a regulatory instrument) → `model-change-impact-analyzer`.
- **Firm-wide risk assessment** rather than a single change → `enterprise-risk-assessment-builder`.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill emits an impact assessment
with a durable `assessment_id`; downstream gap-analysis, control-assessment, reporting,
privacy, and exam-response skills consume it. It must not duplicate their remediation,
decision, or filing steps.

## Inputs and prerequisites
- The **regulatory instrument**: authority, citation, authority level, jurisdiction,
  publication and effective dates, and a source reference to the primary text.
- The **obligations** extracted from the instrument (id, text, type, business-line scope,
  any declared conflicts, source ref).
- The **firm profile** (business lines and jurisdictions) and the **inventory** mapping
  obligations to policies/controls/systems/data/training/owners.
- Approved thresholds/config (lead-time window, mapping-completeness rules — see
  [references/domain-rules.md](references/domain-rules.md)). Schema:
  [scripts/validate_input.py](scripts/validate_input.py).

## Source hierarchy
See [references/source-map.md](references/source-map.md). The **primary regulatory text is the
position of record** for authority, citation, and effective date; the firm profile drives
applicability; the controlled inventory drives mapping. Cite every finding to an obligation or
instrument evidence row with its effective date; never substitute a secondary tracker for the
primary text, and surface (never silently resolve) conflicting requirements.

## Workflow
1. **Scope & validate** — confirm the instrument, obligations, firm profile, and inventory;
   validate with `validate_input`. Record the config version.
2. **Test applicability (deterministic)** — for each obligation, evaluate jurisdiction and
   business-line scope; keep the cited basis. Applicability is a recommendation, not a
   decision.
3. **Map & find gaps (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py) to map applicable
   obligations to the inventory and raise findings (mapping gap, owner gap, overdue/retroactive,
   short lead time, authority conflict), each with evidence and citation.
4. **Recommend disposition** — map the raised-finding profile to a disposition band
   (Informational / Assess / Priority) per the documented, deterministic mapping. This is a
   triage recommendation for a human adjudicator, explicitly **not** a compliance
   determination or a closure.
5. **Write the pack** — plain-language impact summary per obligation + the findings + the
   recommended disposition + the open questions the human must resolve + explicit
   uncertainties.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py)
after. The output check confirms: every raised finding has evidence + citation, no
determination/closure/filing/attestation language is present, the disposition maps
deterministically from the findings, the disclaimer and `mandatory_adjudication` are present,
and adjudication prompts are included. Fail closed on any miss.

## Human approval
`required`: a human must **adjudicate applicability, disposition, and closure** before any
regulated decision, filing, commitment, posting, or system-of-record change. No approval is
needed for the analyst's own read of the pack. The skill never decides, files, attests, or
writes a system of record.

## Failure handling
- **Missing/undated instrument** (no effective date, no primary source ref) → stop; the
  effective date and authority are load-bearing.
- **Ambiguous applicability** (no firm jurisdictions, or unclear business-line scope) → mark
  the obligation not-confidently-evaluable and require human confirmation; do not guess scope.
- **Missing inventory mapping** → raise `mapping_gap`/`owner_gap` as findings; do not invent a
  mapping.
- **Conflicting requirements** across instruments/jurisdictions → cite both and route to
  legal/compliance; never pick a winner.
- **Stale/secondary source disagreeing with the primary text** → cite both; do not resolve
  silently.
- **Tool timeout** → return the findings computed so far with a clear "incomplete" flag.

## Output contract
1. **Summary** — change id, instrument (authority, citation, level, jurisdiction, effective
   date, lead days), applicable-obligation count, recommended disposition band.
2. **Findings** — per raised finding: name, plain-language reason, evidence rows (cited), and
   the basis (threshold/scope) it derives from.
3. **Applicability** — per obligation: applicable (yes/no) with the cited basis.
4. **Open questions** — the applicability, conflict, gap, and ownership questions a human must
   resolve before disposition/closure.
5. **Machine-readable** — findings + evidence + `assessment_id` + config version for downstream
   skills.
6. **Standing disclaimer** — "Impact assessment and evidence only; not a compliance
   determination. Applicability, disposition, and closure require human adjudication. No
   regulatory decision, filing, or system-of-record change has been made."
See [references/controls.md](references/controls.md).

## Privacy and records
Restricted. The instrument text is public; the firm profile, inventory, owners, and
implementation notes are internal — minimize them to what evidences a finding. Retain the
assessment + citations + config version per records policy; log the read and the human
adjudication decision. Never exfiltrate the inventory or owner data.

## Gotchas
- **A finding is not a decision.** Gaps and conflicts justify *disposition priority* and
  adjudication, never a "compliant / non-compliant" conclusion or a change closure.
- **Effective date is load-bearing.** An already-effective or retroactive instrument is a
  `Priority` escalator; capture publication and effective dates exactly from the primary text.
- **Applicability is recommended, not decided.** Firm-wide (`all`) scope and jurisdiction
  overlap are cited *bases*; a human confirms scope and exemptions before anything closes.
- **Conflicts are surfaced, not resolved.** A state/federal or cross-jurisdiction conflict is
  a legal reading, not a position the skill takes.
- **Do not tune thresholds to force a band.** Lead-time and mapping rules come from the
  versioned config, not from what "should" be urgent for this change.
