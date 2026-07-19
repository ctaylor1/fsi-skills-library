---
name: suitability-reg-bi-reviewer
description: >-
  Assemble and review the evidence behind a broker-dealer or advisory recommendation against
  Regulation Best Interest (Reg BI) and FINRA Rule 2111 suitability — customer investment
  profile, costs, reasonably-available alternatives, conflicts of interest, required
  disclosures (Form CRS, Reg BI disclosure), rollover/switch analysis, and supervisory
  routing — and surface gaps with cited evidence. Use when an advisor, supervisor, or
  compliance analyst asks to "review this recommendation for Reg BI", "check the suitability
  evidence", "is the Reg BI file complete", or needs a supervisor-ready evidence pack before a
  principal's determination. HARD BOUNDARY: this skill reports evidence and gaps only; it
  NEVER makes the best-interest / suitability determination, approves or rejects a
  recommendation, clears a trade, closes the review, or files with a regulator — a qualified
  human supervisor or principal must adjudicate.
license: MIT
compatibility: Amazon Quick Desktop; requires CRM, portfolio-accounting/OMS, planning-engine, product-data, disclosures, restrictions, and approved-calculation MCP integrations (all read-only).
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
  aws-fsi-primary-user: "Advisor / supervisor / compliance analyst"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Suitability / Reg BI Reviewer

## Purpose and outcome
Given a **recommendation packet** — a proposed recommendation to a retail customer (buy, sell,
hold, switch, exchange, rollover, reallocate) plus the supporting record — evaluate the
**evidence for each Reg BI component obligation** (Disclosure, Care, Conflict of Interest,
Compliance) and, for non-retail accounts, FINRA Rule 2111 suitability. The skill runs a
deterministic obligation-check set, attaches cited evidence to every satisfied check, flags
**gaps and not-evaluable** items, and assigns a **review-disposition band**. A successful
output is a supervisor-ready evidence pack that tells a principal exactly what is documented
and what is missing — the **best-interest determination and approval remain the human's**.

## Use when
- "Review this recommendation for Reg BI before it goes to the principal."
- "Is the suitability evidence file complete? What's missing?"
- "Check the Care obligation evidence for this variable-annuity switch / IRA rollover."
- "Are the conflicts disclosed and is Form CRS on file for this recommendation?"
- A supervisor needs a consistent, cited obligation-by-obligation write-up to attach to a case.

## Do not use
- The user wants the recommendation **approved / cleared / signed off** or a **best-interest
  or suitability determination** → out of scope. Assemble the evidence and route to the human
  **supervisor / principal**; this skill never adjudicates.
- **Personalized investment advice** ("which fund should I buy?") → prohibited; this skill
  reviews recommendation *evidence*, it does not make recommendations.
- **Senior / vulnerable-investor** protection concerns (diminished capacity, suspected
  exploitation) → `senior-investor-protection-screener`.
- Comparing two product/portfolio **proposals** on cost and allocation →
  `portfolio-proposal-comparator`.
- Modeling **retirement income** from a rollover under scenarios →
  `retirement-income-scenario-modeler`.
- Building the **investment policy statement** → `investment-policy-statement-builder`.
- A deep, standalone **conflicts inventory / mitigation** review →
  `conflicts-of-interest-reviewer`.
- Non-US suitability regimes (e.g., MiFID II appropriateness) unless a jurisdiction pack is
  configured → stop and route to a licensed specialist.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill emits an evidence pack with a
durable `review_id`; the supervisor/principal and downstream skills consume it. It must not
duplicate their determination, approval, or action steps.

## Inputs and prerequisites
- The **recommendation** (action + security) and **customer_type** (`retail` |
  `institutional`).
- The **customer investment profile** (risk tolerance, time horizon, liquidity needs,
  objectives, financial situation, experience).
- The supporting record: **disclosures** (Form CRS, Reg BI disclosure, product disclosure),
  **costs** + cost comparison, **alternatives considered**, **conflicts** inventory,
  **product due diligence**, **rollover/switch analysis** where applicable, and **supervision**
  routing. Schema: [scripts/validate_input.py](scripts/validate_input.py).
- Read access to CRM, portfolio-accounting/OMS, planning engine, product data, and the
  disclosures/restrictions libraries; the approved, **versioned** rule/threshold config (see
  [references/domain-rules.md](references/domain-rules.md)).

## Source hierarchy
See [references/source-map.md](references/source-map.md). Portfolio-accounting/OMS is the
position of record for the recommendation and holdings; the disclosures library is
authoritative for delivery/version; CRM is authoritative for the customer profile; product
data resolves costs and product attributes. Cite every satisfied check to a source record.

## Workflow
1. **Scope & validate** — confirm the account, customer_type, and recommendation; load the
   packet; run `validate_input`. Structural problems fail closed; data-quality warnings become
   downstream gaps / not-evaluable findings (never a silent pass).
2. **Run obligation checks (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py) to evaluate the
   documented obligation-check set across the four Reg BI obligations (plus FINRA 2111 for
   non-retail). Each check returns a status (`satisfied` / `gap` / `not_evaluable` /
   `not_applicable`), a reason, and cited evidence for satisfied checks.
3. **Assemble findings + evidence** — for each satisfied check, attach the specific record and
   citation; for each gap/not-evaluable, state precisely what is missing.
4. **Assign disposition** — map the check set to a band (Insufficient-evidence /
   Gaps-identified / Evidence-complete) per the deterministic, documented mapping. This is a
   **review-readiness triage**, explicitly not a best-interest determination or approval.
5. **Write the pack** — obligation-by-obligation findings + cited evidence + gaps + open items
   + the standing disclaimer, framed for a supervisor/principal to adjudicate.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py)
after. The output check is the R3 fail-closed gate: it confirms every satisfied check has
cited evidence, the disposition ties out deterministically from the checks, **no
approval / best-interest-determination / trade-clearance / closure / filing language** is
present, the standing disclaimer is included, and remediation prompts accompany any non-complete
disposition. Fail closed on any miss.

## Human approval
`required`: a qualified **supervisor / principal** must make the best-interest / suitability
determination and any approval before the recommendation is acted on. Even at
**Evidence-complete**, the skill's output is *evidence readiness*, not an approval — it never
clears, approves, rejects, closes, or files. No approval is needed for the reviewer's own read.

## Failure handling
- **Missing whole evidence categories** (no disclosures list, no profile) → the affected
  obligation is `not_evaluable`; blocking categories drive **Insufficient-evidence** (fail
  closed). Do not infer completeness.
- **Ambiguous account/customer identity** → stop and confirm; never review the wrong file.
- **Institutional customer** → Reg BI retail disclosures are `not_applicable`; evaluate the
  FINRA 2111 suitability path instead.
- **Non-US regime with no configured pack** → stop; route to a licensed specialist.
- **Stale/conflicting sources** (e.g., profile date after the recommendation) → cite both and
  flag; do not resolve silently.
- **Tool timeout** → return the checks computed so far with a clear "incomplete" flag; never
  guess the remainder.

## Output contract
1. **Summary** — account (masked), customer_type, recommendation summary, disposition band,
   count of satisfied / gap / not-evaluable checks.
2. **Findings by obligation** — Disclosure, Care, Conflict of Interest, Compliance: per check,
   status, plain-language reason, and cited evidence (for satisfied checks).
3. **Open items** — the specific gaps / not-evaluable inputs to remediate before adjudication.
4. **Machine-readable** — the checks + evidence + `review_id` for the supervisor and downstream
   skills.
5. **Standing disclaimer** — "Reg BI and suitability evidence review only; not a best-interest
   determination, a suitability approval, or supervisory sign-off. No recommendation has been
   approved and no order has been placed. A qualified supervisor or principal must adjudicate."
See [references/controls.md](references/controls.md).

## Privacy and records
Customer NPI/PII. Mask account numbers (last 4). Minimize customer data in the output to what
evidences a check. Retain the review + citations + **config version** per records policy; log
the read and the routing to the supervisor. Never exfiltrate customer data.

## Gotchas
- **A complete file is not an approval.** Evidence-complete means the record is ready for the
  principal's determination — it is never a best-interest conclusion or a trade clearance.
- **Cost is a factor, not the decision.** Reg BI Care requires cost to be *considered* among
  reasonably-available alternatives; a low- or high-cost product is not automatically in or out
  of the customer's interest — the human weighs it.
- **Alternatives are the most-missed element.** "No alternatives documented" is a genuine Care
  gap, not a formality — surface it every time.
- **Rollovers are high-scrutiny.** For a plan-to-IRA rollover, require the documented plan-vs-IRA
  comparison (fees, services, investment options); its absence is a Care gap.
- **Proprietary / third-party comp must be disclosed and mitigated**, not just listed —
  an undisclosed or unmitigated conflict is a gap.
- **Do not tune the standard to the customer.** Obligation checks come from the versioned config
  and the rule; never relax a required disclosure or the profile completeness bar case-by-case.
- **"Routed for review" ≠ "approved".** The Compliance check confirms the packet reached the
  supervisor's queue; it must never be read as the supervisor's sign-off.
