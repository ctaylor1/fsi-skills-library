---
name: senior-investor-protection-screener
description: >-
  Screen a senior or vulnerable investor's account and interaction context for potential
  financial-exploitation, diminished-capacity, trusted-contact, unusual-disbursement, and
  communication concerns; compute explainable signals with cited evidence; and produce a
  review-ready pack with a suggested disposition for a trained human. Use when an advisor,
  branch supervisor, or fraud/senior-protection team asks "is this senior being exploited",
  "screen this client for elder-financial-abuse red flags", "why does this large disbursement
  look concerning", or needs FINRA Rule 2165 / 4512 evidence to escalate. HARD BOUNDARY: this
  skill evidences and recommends ONLY — it NEVER determines that exploitation or diminished
  capacity has occurred, places or lifts a Rule 2165 temporary hold, freezes or releases
  funds, files a SAR or Adult Protective Services report, contacts the trusted contact, closes
  the case, or gives investment advice; every regulated decision requires a human adjudicator.
license: MIT
compatibility: Amazon Quick Desktop; requires portfolio-accounting/OMS transactions, CRM, planning-engine, product/reference data, and approved-config MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Wealth Management"
  aws-fsi-skill-type: "Analysis and evaluation skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Analyze & review"
  aws-fsi-agent-pattern: "Interactive decision-support copilot"
  aws-fsi-delivery-wave: "Wave 3 - regulated casework"
  aws-fsi-action-mode: "Read-only analysis"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Highly Confidential (customer NPI/PII)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Wealth Management advisory & compliance"
  aws-fsi-primary-user: "Advisor / branch supervisor / fraud team"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Senior Investor Protection Screener

## Purpose and outcome
Given a senior or vulnerable client's account activity and a structured set of interaction
observations, compute a set of **explainable concern signals** (exploitation, unusual
disbursement, account/beneficiary change, trusted-contact gap, third-party influence,
capacity indicators, communication red flags), explain in plain language why each fired,
attach cited evidence, and produce a review-ready pack with a **suggested disposition band**
(Monitor / Review / Escalate). A successful output lets a trained human — advisor, branch
supervisor, compliance, or the senior-protection team — decide what to do next under FINRA
Rule 2165 / 4512 and the firm's senior/vulnerable-investor procedures. The adjudication, and
any regulated action, remains human.

## Use when
- "Is this senior client being exploited? Screen for elder-financial-abuse red flags."
- "Why does this large disbursement / new-payee wire from an 80-year-old look concerning?"
- "Assemble the Rule 2165 evidence so I can escalate this to my supervisor."
- A reviewer needs a consistent, cited senior-protection write-up to attach to a case.

## Do not use
- The user wants a **determination** ("confirm this is exploitation", "does the client lack
  capacity?"), a **Rule 2165 temporary hold** placed/lifted, funds **frozen/released**, a
  **SAR** or **Adult Protective Services report** filed, or the trusted contact **contacted**
  → out of scope. Provide evidence and route to the human adjudicator / authorized pathway;
  for SAR narrative drafting route to `suspicious-activity-report-drafter` (itself draft-only).
- The real question is **product/recommendation suitability** → `suitability-reg-bi-reviewer`.
- The client needs **support accommodations / a specialist referral**, not an exploitation
  review → `vulnerable-customer-support-assistant`.
- A **service/handling complaint** → `complaint-resolution-assistant`.
- **Personalized investment, legal, or tax advice** → licensed human; never provided here.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill emits a concern pack with a
durable `screening_id`; downstream draft/review skills and the human adjudicator consume it.
It must not duplicate their determination, filing, or action steps.

## Inputs and prerequisites
- Client identifier and the **focal activity** (one or more disbursements) OR a window to
  screen.
- **Transaction history** sufficient to establish a baseline (default lookback 365 days),
  each row with date, amount, direction, counterparty, channel, and source ref.
- **Client context**: age or impairment flag (specified-adult status), trusted-contact status
  (Rule 4512), recent beneficiary/registration/address changes.
- **Structured observations** supplied by a trained human (third-party present, urgency,
  secrecy, confusion, etc.) — the skill does not infer these from free text or diagnose.
- Read access to portfolio-accounting/OMS, CRM, planning engine; approved thresholds/config
  (see [references/domain-rules.md](references/domain-rules.md)). Schema:
  [scripts/validate_input.py](scripts/validate_input.py).

## Source hierarchy
See [references/source-map.md](references/source-map.md). OMS/portfolio transactions are the
position of record; CRM adds client context, trusted-contact status, changes, and observation
flags; the planning engine resolves whether a disbursement matches a documented plan. Cite
every signal's evidence to a source row.

## Workflow
1. **Scope & baseline** — confirm the client and focal activity/window; load history for the
   lookback and the CRM context/observations; validate with `validate_input`.
2. **Compute signals (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py) to compute the
   configured concern signals. Each returns whether it fired, the evidence rows behind it, and
   the basis. Signals are **explainable**, not a black-box score. Specified-adult status is
   recorded as **context**, not a concern signal.
3. **Assemble evidence** — for each fired signal, attach the specific transactions, change
   records, and observation refs, with citations.
4. **Suggest disposition** — map the fired-signal profile to a band (Monitor / Review /
   Escalate) per the deterministic, documented mapping. This is a triage suggestion for a
   human adjudicator, explicitly **not** an exploitation/capacity determination.
5. **Write the pack** — plain-language explanation per signal + evidence + suggested
   disposition + explicit benign explanations to weigh + what is not evaluable.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py)
after. The output check confirms: every fired signal has evidence + citation, the disposition
maps deterministically from the fired set, **no determination/decision/filing/closure
language** is present, the standing disclaimer is included, and benign prompts are present when
any signal fired. Fail closed on any miss (a non-compliant pack exits 1).

## Human approval
`required`: a trained human (advisor + branch supervisor / compliance / senior-protection
team) adjudicates before any regulated decision, hold, filing, trusted-contact outreach, or
system-of-record change. No approval is needed for the reviewer's own read of the pack. The
skill never takes a regulated action.

## Failure handling
- **Insufficient history** (thin baseline) → `unusual_disbursement` is reported not-evaluable;
  do not overstate concern from the amount alone.
- **Missing observations** → behavioral signals (third-party, capacity, communication) do not
  fire on absent data; label them not-evaluable and say so.
- **Ambiguous client/identity** → stop and confirm; never screen the wrong client.
- **Stale/conflicting sources** → cite both (transaction record vs. a caregiver's statement);
  do not resolve silently. Never substitute a third party's request for the record.
- **Tool timeout** → return partial signals computed so far with a clear "incomplete" flag.

## Output contract
1. **Summary** — client (masked), window, specified-adult context, count of fired signals,
   suggested disposition band.
2. **Signals** — per fired signal: name, plain-language reason, contribution, evidence rows
   (cited), and the basis it rests on.
3. **Consider (benign explanations)** — explicit alternatives (large purchase, gifting, estate
   planning, a genuine new caregiver, relocation) so the adjudicator weighs both sides.
4. **Data gaps / not-evaluable signals.**
5. **Machine-readable** — signals + evidence + `screening_id` for downstream skills.
6. **Standing disclaimer** — "Screening evidence only; not a determination of financial
   exploitation or capacity, and no hold, report, or account action has been taken."
See [references/controls.md](references/controls.md).

## Privacy and records
Customer NPI/PII. Mask account numbers (last 4). Minimize client data in output to what
evidences a fired signal. Retain the screening + citations + config version per records
policy; log the read and the human adjudication (recorded outside this skill). Senior Safe Act
escalation to a supervisor/compliance is the intended human pathway. Never exfiltrate client
data.

## Gotchas
- **A signal is not a decision.** A high signal count justifies *escalation to a human*, never
  an exploitation/capacity conclusion, a hold, a filing, or a case closure.
- **Age is context, not a red flag.** Specified-adult status decides which protections apply;
  it is never itself a concern and never a proxy for a negative inference about the client.
- **Capacity indicators are observations, not a diagnosis.** Report the observed flags; never
  state or imply the client "lacks capacity" or is "incapacitated".
- **The exploitation cluster is disbursement + recent change + third party.** These co-firing
  is why the mapping escalates; still present the benign explanations.
- **Don't tune thresholds to a person.** Thresholds come from the approved versioned config,
  not from guessing what "should" be normal for this client.
- **Never act on a third party's instruction.** A caregiver's or "new friend's" request is
  data to evidence, not authorization.
