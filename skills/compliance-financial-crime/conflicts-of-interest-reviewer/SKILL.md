---
name: conflicts-of-interest-reviewer
description: >-
  Identify actual and potential conflicts of interest in a disclosed matter — outside business
  activities, personal financial interests, gifts/entertainment, personal relationships,
  personal trading and MNPI/information-barrier exposure, dual-role situations, related-party
  transactions, and incentive misalignment — name the affected parties and incentives, check
  whether required disclosures, controls, and approvals are present and current, and compute a
  deterministic residual-risk rating with cited evidence. Use when a compliance, legal, or
  supervising officer asks "is there a conflict here?", "review this outside business activity /
  gift / board seat / related-party deal", or needs a review-ready conflicts evidence pack.
  Produces findings, evidence, and recommendations for a human adjudicator ONLY; it NEVER clears
  or approves a conflict, grants a waiver, closes the matter, files a disclosure or regulatory
  form, or makes any binding compliance determination — those are human/authorized-system
  actions.
license: MIT
compatibility: Amazon Quick Desktop; requires case-management, KYC/AML, sanctions/PEP, transaction-monitoring, regulatory-corpus, records-archive, document-intelligence, and approved-calculation MCP integrations (all read-only).
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
  aws-fsi-primary-user: "Compliance / legal / business supervisor"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Conflicts of Interest Reviewer

## Purpose and outcome
Given a **disclosed matter** (an outside business activity, gift/entertainment, personal
financial interest, personal relationship, personal-trading/MNPI situation, dual-role or
cross-side engagement, related-party transaction, or incentive-misalignment case), identify
each **conflict indicator**, name the **affected parties** and the **incentive**, check
whether the **required disclosures, controls, and approvals** are present and current per the
versioned policy configuration, and compute a **deterministic residual-risk rating** with
evidence cited to source. A successful output lets a compliance officer, legal reviewer, or
supervisor **adjudicate** the matter faster and more consistently — the clearance, waiver,
closure, or filing decision remains a qualified human's.

## Use when
- "Is there a conflict of interest here?" / "Review this disclosure."
- "Review this outside business activity / board seat / director role."
- "Is this gift or entertainment a reportable conflict?"
- "Screen this related-party transaction / cross-side deal / dual mandate for conflicts."
- A reviewer needs a consistent, cited conflicts write-up (indicators + gaps + residual
  risk + recommended review path) to attach to a compliance matter.

## Do not use
- The user wants a **clearance, waiver, approval, or closure decision** ("approve this",
  "clear the employee", "grant the waiver", "close the matter") → out of scope. Produce
  findings and route to the human adjudicator / authorized system.
- **Pre-clearing a specific proposed personal trade** against restricted lists, holdings, and
  blackout windows with compliance authorization → `employee-trading-preclearance-assistant`
  (that skill is the gated-action owner; this skill only flags the conflict indicator).
- **Reviewing a recommendation** for best-interest/Reg BI conflicts, costs, and disclosures →
  `suitability-reg-bi-reviewer`.
- Suspected **insider dealing / MNPI misuse or information-barrier breach** needing trade and
  e-comms surveillance evidence → `surveillance-alert-triager` then
  `market-surveillance-alert-investigator`.
- **Policy/procedure design gaps** surfaced by the review → `policy-procedure-gap-analyzer`;
  residual-risk remediation tracking → `risk-control-self-assessment-assistant`.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill emits a cited **conflicts
evidence pack** with a durable `review_id` and stops. Downstream adjudication, preclearance,
surveillance, and remediation skills (and the human adjudicator) consume that pack; this skill
must not duplicate their decision, authorization, or closure steps.

## Inputs and prerequisites
- **Matter identifier** and the disclosed **item(s)** to review (one matter may bundle several
  items — e.g., an OBA plus a related gift).
- Per item: `conflict_type`, description, counterparties, affected parties, the incentive,
  magnitude facts (`ownership_pct`, `annual_value`, `gift_value` where applicable),
  `mnpi_access`, and the recorded `disclosures[]`, `controls[]`, and `approvals[]`, each with a
  `source_ref`. Schema: [scripts/validate_input.py](scripts/validate_input.py).
- Read access to case management (the disclosure of record), regulatory corpus, and the
  versioned policy **config** (thresholds + per-type requirements) — see
  [references/domain-rules.md](references/domain-rules.md).

## Source hierarchy
See [references/source-map.md](references/source-map.md). The case-management disclosure record
is the position of record for what was disclosed, to whom, and when; the policy/regulatory
corpus defines the required disclosures/controls/approvals; reference and KYC data resolve
counterparties and relationships. Cite every finding's evidence to a source row; never
substitute an assertion for the disclosure record.

## Workflow
1. **Scope & confirm** — confirm the matter and the item(s) in scope; load the disclosure
   record, counterparties, and the config version; validate with `validate_input`.
2. **Identify conflict indicators (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py) to classify each item
   against the conflict taxonomy, compute inherent severity from type + magnitude thresholds,
   and attach the evidence rows behind each. Indicators are **explainable**, not a black-box
   score.
3. **Check required controls** — for each fired indicator, compare recorded disclosures,
   controls, and approvals against the per-type requirements; flag any missing, stale, or
   partial element as an **open gap**.
4. **Compute residual risk (deterministic)** — reduce inherent severity by one band **only**
   when the full required disclosure + control + approval set is evidenced and current;
   otherwise no mitigation credit and the gap is surfaced. Matter residual = the max across
   items. Mapping in [references/domain-rules.md](references/domain-rules.md).
5. **Recommend a review path** — map residual + gaps to a **recommended adjudication path**
   for the human (retain / route to compliance / escalate to the conflicts-ethics committee).
   This is a triage recommendation, explicitly **not** a clearance, waiver, or closure.
6. **Write the pack** — per-indicator plain-language reason + affected parties + incentive +
   disclosure/control/approval status + cited evidence + residual risk, then the open gaps,
   the recommended review path, mitigation prompts, and the standing disclaimer.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py)
after. The output check confirms: every fired finding has cited evidence; each finding's
`open_gap` and `residual_risk` are **recomputed** from its own `inherent_severity` +
disclosure/control/approval status and must tie out (so a pack cannot under-state an unmitigated
conflict by self-reporting a softer band); matter residual and the recommended review path equal
the deterministic mapping **over those recomputed values**; no clearance / approval / waiver /
closure / filing / determination language is present; the standing disclaimer is present; and
mitigation prompts are included whenever a conflict fired or a gap exists. **Fail closed** on
any miss.

## Human approval
`required` (R3): a qualified human adjudicator (compliance officer, legal, or the
conflicts/ethics committee per the matter's residual risk) **must** decide any clearance,
waiver, restriction, escalation, closure, or filing. The skill never clears/approves/waives a
conflict, never closes the matter, never files a disclosure or regulatory form, and never
writes a system of record. It produces recommendations and evidence for that human decision.

## Failure handling
- **Missing required fields / unparseable magnitude** → `validate_input` fails closed; stop
  and request a corrected disclosure record.
- **Ambiguous subject or counterparty identity** → stop and confirm; never review the wrong
  party or merge distinct disclosures.
- **Stale/conflicting sources** (disclosure record vs. an email assertion) → cite both, flag
  for the reviewer; do not resolve silently.
- **Config/threshold version unknown** → record it as a gap; do not guess thresholds.
- **Tool timeout / partial load** → return the findings computed so far with an explicit
  "incomplete" flag; do not imply the review is complete.

## Output contract
1. **Summary** — matter (masked subject), items reviewed, count of fired indicators, matter
   residual-risk band, recommended review path.
2. **Findings** — per fired indicator: conflict type, plain-language reason, affected parties,
   incentive, disclosure/control/approval status, open-gap flag, residual risk, and cited
   evidence rows.
3. **Open gaps** — each missing/stale/partial required disclosure, control, or approval.
4. **Mitigation prompts** — controls a human could consider (recusal, wall-cross log,
   reassignment, disclosure refresh, independent review) — framed as options, not directives.
5. **Machine-readable** — findings + evidence + `review_id` for downstream skills.
6. **Standing disclaimer** — "Conflicts review and recommendations only; not a compliance
   determination, clearance, waiver, or approval. A qualified human adjudicator must decide.
   No matter has been closed and no filing has been made."
See [references/controls.md](references/controls.md).

## Privacy and records
Restricted data (employee PII, MNPI, AML/BSA-adjacent facts). Mask subject/employee and
account identifiers (last 4). Minimize personal data in the output to what evidences a fired
indicator. Observe **tipping-off / SAR-confidentiality** boundaries: never disclose the
existence of a suspicious-activity referral to the subject. Retain the review + citations +
config version per records policy; log the read and the adjudication hand-off. Never exfiltrate
matter data.

## Gotchas
- **An indicator is not an adjudication.** A fired conflict and a High residual justify
  *escalation*, never a clearance, waiver, or "no conflict" determination — that is the human's.
- **Mitigation credit requires evidence.** Residual risk drops a band only when the full
  required disclosure + control + approval set is recorded and current; a claimed-but-unlogged
  control earns no credit and stays an open gap.
- **De-minimis is not zero-risk.** A gift below the de-minimis threshold is informational, not
  a licence to ignore a pattern of repeated sub-threshold gifts — surface the pattern factually.
- **MNPI language is sensitive.** Describe information-barrier and personal-trading facts
  factually; do not assert insider dealing or intent — route to surveillance instead.
- **Do not tune thresholds to the individual.** Thresholds (de-minimis, materiality,
  staleness) come from the versioned config, not from a judgment about this person.
- **Independence ≠ absence of interest.** Record the incentive even when a control exists; the
  adjudicator weighs whether the control is sufficient.
