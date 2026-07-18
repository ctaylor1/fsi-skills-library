---
name: call-quality-compliance-reviewer
description: >-
  Evaluate a contact-center interaction (call, chat, or email transcript) against a
  versioned quality/compliance rubric — required disclosures, identity authentication, fair
  treatment of vulnerable customers, prohibited language, complaint handling, agent
  commitments, and coaching opportunities — and produce cited findings with a suggested QA
  disposition band. Use when a QA analyst, compliance reviewer, or contact-center manager
  asks "review this call for compliance", "did the agent give the required disclosures",
  "score this interaction", "check this transcript for prohibited language or an
  authentication gap", or needs a review-ready, evidence-linked scorecard. This skill
  evidences findings and suggests a disposition for a human; it NEVER adjudicates agent
  misconduct, declares a regulatory breach, decides a pass/fail or disciplinary outcome,
  files a report, or takes any action — those are human/authorized-system decisions.
license: MIT
compatibility: Amazon Quick Desktop; requires contact-center transcript/CRM, case-management, complaint-system, approved-knowledge/product-terms, and approved-calculation MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Customer Service & Experience"
  aws-fsi-skill-type: "Analysis and evaluation skills"
  aws-fsi-risk-tier: "R2"
  aws-fsi-archetype: "Analyze & review"
  aws-fsi-agent-pattern: "Interactive decision-support copilot"
  aws-fsi-delivery-wave: "Wave 2 - analytical production"
  aws-fsi-action-mode: "Read-only analysis"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "external-delivery"
  aws-fsi-data-classification: "Highly Confidential (customer NPI/PII)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Customer Service & Experience"
  aws-fsi-primary-user: "Quality assurance / compliance / contact-center manager"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Call Quality & Compliance Reviewer

## Purpose and outcome
Given a de-identified contact-center interaction transcript and its context, run a set of
**explainable rubric checks**, explain in plain language which quality/compliance
expectations were met or missed, attach the specific transcript turns as evidence, and
produce a review-ready scorecard with a **suggested QA disposition band**. A successful
output lets a QA analyst or compliance reviewer decide what to do next — deliver coaching,
escalate for compliance review, or clear the interaction. The decision, the coaching, and
any downstream action remain human.

## Use when
- "Review this call/chat for compliance and quality."
- "Did the agent make the required disclosures (recording notice, mini-Miranda, APR, risk)?"
- "Check this transcript for prohibited language, an authentication gap, or a missed complaint."
- A QA lead needs a consistent, cited scorecard to attach to a coaching or calibration record.

## Do not use
- The user wants an **agent-misconduct determination**, a **regulatory-breach finding**, a
  **pass/fail that drives discipline**, an **HR/disciplinary action**, or a **regulatory
  report filed** → out of scope. Evidence the findings and route to the human QA lead /
  compliance officer / a licensed specialist.
- **Written/marketing or supervised-communications compliance** (not a contact-center
  interaction) → `communications-compliance-reviewer`.
- The interaction is actually a **substantive complaint to work** (classify, root-cause,
  remediate, respond) → `complaint-resolution-assistant`.
- A **service failure needs remediation/goodwill** designed → `service-recovery-assistant`.
- The user just wants a **plain summary** of the interaction (sentiment, actions, no rubric)
  → `customer-interaction-summarizer`.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill emits a scorecard with a
durable `review_id`; downstream complaint, service-recovery, vulnerability, and operational-
risk skills consume its findings. It must not duplicate their disposition or action steps,
and it never delivers the coaching itself.

## Inputs and prerequisites
- **Interaction identifier** and the **channel** (voice / chat / email).
- **Turns** — an ordered list of `{turn_id, speaker(agent|customer|system|ivr), text, ts?}`.
  Voice calls should be a diarized, de-identified transcript. Schema:
  [scripts/validate_input.py](scripts/validate_input.py).
- **Context** — `requires_authentication`, `product_context`
  (deposit / lending / collections / investment / general), `customer_stated_vulnerability`.
- **Versioned rubric/config** — required-disclosure markers, prohibited lexicon, and the
  authentication / vulnerability / complaint marker sets (see
  [references/domain-rules.md](references/domain-rules.md)). Read access to the transcript/
  CRM, case, complaint, and approved-knowledge sources.

## Source hierarchy
See [references/source-map.md](references/source-map.md). The interaction transcript is the
record of what was said; CRM/case adds context (auth performed in IVR, prior contact); the
approved-knowledge/product-terms library and the versioned rubric define what was required.
Cite every finding to a specific turn (or the scanned scope for an absence).

## Workflow
1. **Scope & validate** — confirm the interaction, channel, and product context; load the
   turns; validate with `validate_input`. Note which checks are not evaluable given the data.
2. **Run checks (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py) to evaluate the
   configured rubric checks (recording-consent disclosure, identity authentication, product
   required disclosures, prohibited language, fair-treatment/vulnerability, complaint
   acknowledgement, commitment capture, empathy/courtesy). Each check returns fired/not,
   the reason, and the evidence turns behind it. Checks are **explainable**, not a black-box
   score.
3. **Assemble evidence** — for each fired finding, attach the specific turn(s) (or the
   scanned scope for an absence) with citations and the rubric item referenced.
4. **Suggest disposition** — map the fired-finding profile to a disposition band
   (Meets expectations / Coaching recommended / Compliance review required) per the
   configured, documented mapping. This is a triage suggestion for a human, explicitly
   **not** a misconduct or breach determination.
5. **Write the scorecard** — plain-language explanation per check + the evidence + the
   suggested disposition + explicit **considerations** (benign explanations to weigh before
   dispositioning).

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py)
after. The output check confirms: every fired finding has evidence + citation, no
misconduct/breach determination or disciplinary/action/advice language is present, the
disposition maps deterministically from the fired findings' severities, the standing
disclaimer is present, and considerations are included when any finding fired. Fail closed
on any miss.

## Human approval
`external-delivery`: human review required before the scorecard is delivered to the agent,
a team lead, a calibration record, or a system of record, and before any coaching or
routing. No approval is needed for the reviewer's own read. The skill never dispositions a
case, delivers coaching, or takes an action.

## Failure handling
- **Partial / truncated transcript** → state that absence-based checks are low-confidence;
  do not assert a disclosure was missed if the segment that would contain it is absent.
- **IVR-delivered disclosure/authentication** → recording notice or authentication may
  occur in an IVR segment not in the agent transcript; mark such checks "consider" rather
  than firing when the IVR segment is unavailable.
- **Ambiguous interaction/identity** → stop and confirm; never review the wrong interaction.
- **Missing speaker labels / no diarization** → agent-only checks are not evaluable; label
  them so.
- **Mislabeled product_context** → the wrong required-disclosure set applies; flag the
  product assumption in the output.
- **Tool timeout** → return the checks computed so far with a clear "incomplete" flag.

## Output contract
1. **Summary** — interaction (masked), channel, product, count of fired findings, suggested
   disposition band.
2. **Findings** — per check: name, severity (critical / coaching), plain-language reason,
   evidence turns (cited), and the rubric item referenced.
3. **Considerations** — explicit benign explanations (IVR/written disclosure, transcription
   error, partial transcript, product mislabel) the reviewer must weigh before dispositioning.
4. **Not-evaluable checks** — with the reason each could not be assessed.
5. **Machine-readable** — findings + evidence + `review_id` for downstream skills.
6. **Standing disclaimer** — "Quality-review evidence only; not a determination of
   misconduct, a regulatory breach, or a disciplinary decision. No action has been taken."
See [references/controls.md](references/controls.md).

## Privacy and records
Customer NPI/PII. Operate on **de-identified** transcripts; mask any account/card numbers to
last 4. Minimize customer data in the output to what evidences a finding. Retain the
scorecard + citations + rubric version per records policy; log the read and any external-
delivery approval. Never exfiltrate customer or agent data, and treat agent-performance data
as confidential.

## Gotchas
- **A finding is not a verdict.** A fired compliance-critical finding justifies *human
  compliance review*, never an autonomous misconduct/breach conclusion or a disciplinary
  action.
- **Absence is not proof.** A disclosure or authentication may have happened off-transcript
  (IVR, prior transfer, in writing) — that is why every absence-based finding carries a
  "consider" prompt and cites the scanned scope.
- **Transcription noise**: ASR errors can hide or fabricate a marker; a spoken-marker miss
  should be spot-checked against audio before dispositioning.
- **Prohibited-language matches are lexical**, not intent — quote the phrase factually and
  attribute any conclusion to the human reviewer.
- **Do not tune the rubric to an agent or a customer**: markers and thresholds come from the
  approved, versioned config, never from guessing what "should" count for this interaction.
- **Fair treatment, not profiling**: never use protected-class attributes or proxies as a
  quality signal; vulnerability cues drive *accommodation*, never an adverse conclusion.
