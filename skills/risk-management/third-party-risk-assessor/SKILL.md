---
name: third-party-risk-assessor
description: >-
  Assess a third party (vendor/supplier) across eight documented risk dimensions —
  criticality, control evidence, concentration, subcontractors (fourth parties), data,
  resilience, financial condition, and exit/contingency — scoring each into an evidenced band
  and a suggested composite risk tier for committee review. Use when a third-party-risk
  analyst, procurement lead, or business owner asks "assess this vendor's risk", "what is our
  exposure to this supplier", "review the control evidence / concentration / resilience /
  financials for onboarding or renewal", or needs a cited assessment pack. HARD BOUNDARY:
  produces evidence and recommendations only; it NEVER approves, rejects, onboards, renews,
  terminates, or risk-accepts a vendor, closes/files the assessment, gives investment advice,
  or writes a system of record — human/committee adjudication and sign-off are required.
license: MIT
compatibility: Amazon Quick Desktop; requires third-party-inventory, control-evidence, risk-register, finance/operational-data, and approved-config MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Risk Management"
  aws-fsi-skill-type: "Analysis and evaluation skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Analyze & review"
  aws-fsi-agent-pattern: "Interactive decision-support copilot"
  aws-fsi-delivery-wave: "Wave 3 - regulated casework"
  aws-fsi-action-mode: "Read-only analysis"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Confidential"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Enterprise Risk Management"
  aws-fsi-primary-user: "Third-party risk / procurement / business owner"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Third-Party Risk Assessor

## Purpose and outcome
Given a third party's inventory profile, control evidence, and finance/operational data,
score the **eight documented risk dimensions** (criticality, control evidence, concentration,
subcontractors/fourth parties, data, resilience, financial condition, exit/contingency),
explain in plain language why each band was assigned, attach cited evidence to each material
finding, and produce a review-ready pack with a **suggested composite risk tier** and
remediation recommendations. A successful output lets the accountable third-party-risk
committee, procurement lead, or business owner adjudicate onboarding, renewal, or continued
use — the decision, sign-off, and any action remain human.

## Use when
- "Assess this vendor's / supplier's risk before we onboard or renew."
- "What is our exposure to this third party across data, resilience, and financials?"
- "Review the control evidence / concentration / subcontractor / exit-plan gaps for V-XXXX."
- A reviewer needs a consistent, cited third-party assessment pack to attach to a case or the
  vendor register.

## Do not use
- The user wants a **vendor decision** ("approve/reject/onboard/renew/terminate this vendor"),
  a **risk acceptance**, or the assessment **closed/filed** → out of scope. Provide evidence
  and route to the human committee / authorized system.
- **Deep cyber/security control testing** of the vendor → `third-party-cyber-risk-reviewer`.
- **Enhanced due diligence** on ownership / financial-crime / sanctions exposure →
  `enhanced-due-diligence-packager` (and human specialists; this skill never adjudicates
  sanctions or misconduct).
- **Resilience/exit scenario testing** for a critical vendor →
  `operational-resilience-scenario-tester`.
- **Ongoing** concentration or KRI monitoring → `concentration-risk-monitor` /
  `key-risk-indicator-monitor` (this skill is a point-in-time interactive assessment).
- **Investment/credit advice** on the vendor's securities or debt → out of scope entirely.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill emits an assessment pack with
a durable `assessment_id`; downstream review, due-diligence, resilience, monitoring, and
enterprise-risk skills consume it. It must not duplicate their testing, adjudication, or
action steps.

## Inputs and prerequisites
- Vendor identifier and name, `as_of` date, `config_version`, and `framework_version`.
- One or more **risk-dimension blocks**: `criticality`, `controls`, `concentration`,
  `subcontractors`, `data`, `resilience`, `financials`, `exit_plan` — each row carrying a
  `source_ref` so evidence is traceable. Schema:
  [scripts/validate_input.py](scripts/validate_input.py).
- Read access to the third-party inventory, control-evidence repository, risk register, and
  finance/operational data; approved thresholds/config (see
  [references/domain-rules.md](references/domain-rules.md)).

## Source hierarchy
See [references/source-map.md](references/source-map.md). The third-party inventory is the
position of record; the control-evidence repository establishes control status; the risk
register supplies concentration, limits, and loss events; finance/operational data supplies
financials, SLA, RTO, and exit artifacts. Never substitute a vendor self-assertion for the
evidence record. Cite every material finding to a source row.

## Workflow
1. **Scope & confirm** — confirm the vendor, `as_of`, and which dimension blocks are present;
   validate with `validate_input`. Missing blocks become `not_evaluable`, not silent Low.
2. **Score dimensions (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py) to score each
   dimension into a band (Low/Moderate/High/Critical) per the configured rules. Each material
   finding (severity ≥ High) returns its band, reason, and the evidence rows behind it. Bands
   are **explainable**, not a black-box score.
3. **Assemble evidence** — for each material finding, attach the specific control/data/
   financial/exit rows and cite them.
4. **Suggest composite tier** — map the dimension bands to a composite tier
   (Low/Moderate/High/Critical) per the deterministic, documented mapping. This is a
   prioritization suggestion for the committee, explicitly **not** an approval or a decision.
5. **Write the pack** — plain-language explanation per dimension + cited evidence + suggested
   tier + remediation recommendations (each a route for a human to initiate) + explicit
   evidence gaps and considerations to weigh.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py)
after. The output check confirms: every material finding has cited evidence; the composite
tier maps deterministically from the dimension severities; no vendor-decision / closure /
filing / risk-acceptance / sign-off language is present; the standing disclaimer is included;
recommended actions carry a human-adjudication note and evidence gaps are listed. **Fail
closed on any miss** — do not deliver a pack that fails the screen.

## Human approval
`required` (R3): human/committee adjudication and sign-off are mandatory before any vendor
decision (onboarding, renewal, termination, risk acceptance), any filing, any commitment, or
any write to the vendor register / GRC system. This skill performs none of these; it produces
evidence and recommendations for the accountable human to act on.

## Failure handling
- **Missing dimension block** → mark the dimension `not_evaluable`; exclude it from the
  composite; list it in evidence gaps. Never default a missing dimension to Low.
- **Ambiguous vendor identity** → stop and confirm; never assess the wrong third party.
- **Stale evidence** (control `last_tested` beyond tolerance, stale financials) → treat as a
  gap and flag it; do not credit stale evidence as passing.
- **Vendor self-assertion vs. evidence conflict** → cite both; do not resolve silently.
- **Tool timeout / large control or subcontractor sets** → return the dimensions scored so far
  with a clear "incomplete" flag; page the remainder as resumable stages.

## Output contract
1. **Summary** — vendor (id + name), `as_of`, `config_version` / `framework_version`, count of
   material findings, suggested composite tier.
2. **Dimensions** — per dimension: band, plain-language reason, evidence rows (cited), and the
   inputs behind the band. Material findings (High/Critical) always carry evidence.
3. **Recommended actions** — remediation and follow-up routes (each initiated by a human),
   plus the explicit human-adjudication note.
4. **Evidence gaps / not-evaluable dimensions.**
5. **Machine-readable** — dimensions + evidence + `assessment_id` for downstream skills.
6. **Standing disclaimer** — "Assessment evidence and recommendations only; not an approval,
   rejection, or risk-acceptance decision. Human adjudication and sign-off are required before
   any onboarding, renewal, termination, or system-of-record change."
See [references/controls.md](references/controls.md).

## Privacy and records
Confidential vendor commercial, control, and financial data (may reference customer-data
exposure). Minimize to what evidences a finding; do not copy raw customer data into the pack.
Retain the assessment + citations + config/framework versions per records policy; log the
read. The committee's adjudication is recorded by the authorized system of record, not by this
skill. Never exfiltrate vendor or customer data.

## Gotchas
- **A band is not a decision.** A Critical tier justifies *review priority and remediation*,
  never an autonomous approve/reject/terminate or a risk acceptance.
- **Missing ≠ safe.** A missing control, exit plan, or financial block is a gap or
  not-evaluable — never scored as Low by omission.
- **Stale evidence is a gap.** Control evidence past its test tolerance and stale financials
  do not count as passing; they raise, not lower, the finding.
- **Financial condition ≠ investment advice.** Solvency/creditworthiness indicators are a
  factual risk read; never recommend buying/holding/selling the vendor's securities or debt.
- **Jurisdiction lists flag, they don't judge.** `elevated_risk_jurisdictions` is a configured
  ERM/compliance list that triggers enhanced review, not a decision, and never a proxy for
  protected-class attributes.
- **Do not tune thresholds to a vendor.** Thresholds come from the approved, versioned config,
  not from guessing what "should" be acceptable for this vendor.
