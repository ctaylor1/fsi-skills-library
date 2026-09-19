---
name: policy-renewal-reviewer
description: "Compare an expiring P&C policy term with the proposed renewal term — premium, limits, deductibles, exposures, forms/endorsements, and loss history — surface material changes with cited evidence, draft renewal questions and plain-language customer explanations, and suggest a review disposition. Use when an underwriter, agent, or account manager asks \"what changed at renewal\", \"compare the expiring and proposed terms\", \"is this renewal priced/structured differently\", or needs a review-ready renewal comparison. This skill compares, evidences, and drafts questions only; it NEVER makes a renew/non-renew or decline decision, sets premium or rate, binds coverage, issues a non-renewal notice, makes a coverage or claim determination, or gives personalized insurance advice — those are human/licensed-professional actions."
license: MIT
compatibility: Python 3.10+; offline structured inputs and supplied source evidence. Expected source systems are not bundled production connectors.
metadata:
  aws-fsi-category: "Insurance"
  aws-fsi-skill-type: "Analysis and evaluation skills"
  aws-fsi-risk-tier: "R2"
  aws-fsi-archetype: "Analyze & review"
  aws-fsi-agent-pattern: "Interactive decision-support copilot"
  aws-fsi-delivery-wave: "Insurance Phase 1"
  aws-fsi-action-mode: "Read-only analysis"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "existing-updated"
  aws-fsi-human-approval: "external-delivery"
  aws-fsi-data-classification: "Highly Confidential (customer NPI/PII)"
  aws-fsi-jurisdictions: "Reviewed target-specific jurisdiction/product profiles required; fixture coverage is not global applicability"
  aws-fsi-owner: "Insurance underwriting and account management"
  aws-fsi-primary-user: "Underwriter / agent / account manager"
  aws-fsi-version: "0.2.0"
  aws-fsi-recertification-date: "2027-09-18"
---

# Policy Renewal Reviewer

## Implemented scope and evidence contract

Loss statistics require `claims_complete: true` and sourced `earned_premium{amount,period_start,period_end,currency,source_ref}` matching the exact inclusive `[as_of - review_window_days, as_of]` window and top-level currency. Filter out old/future claims; never substitute expiring premium times years. Missing schedules/forms are not removals. Empty source lists require an explicit corresponding completeness flag. No fired findings plus unevaluable checks is `Incomplete`, never `Routine`. A confirmed empty claims list is distinct from unavailable history.

All output artifacts include the portable insurance evidence contract and source snapshot. Missing actor, versioned source, date or upstream context remains explicitly partial. Content hashes detect changes; they do not authenticate sources or grant approval. After authoring narrative, rebuild `artifact` with `build_artifact` from `scripts/insurance_contract.py` before running output validation. A common envelope does not replace the receiver's native input validator.

## Purpose and outcome
Given an expiring policy term and a proposed renewal term (plus loss history), compute a set
of **explainable material-change findings**, explain in plain language why each fired, attach
cited evidence to each, draft the **renewal questions** a human should raise, and produce a
review-ready comparison with a **suggested review disposition**. A successful output lets an
underwriter, agent, or account manager see exactly what changed and why it matters, and drives
a human conversation with the insured — the renewal decision, the pricing, and any customer
commitment remain human/licensed-professional actions.

## Use when
- "What changed between the expiring policy and the proposed renewal?"
- "Compare the expiring and proposed terms — premium, limits, deductibles, forms, exposures."
- "Is this renewal priced or structured differently, and what should I ask about?"
- "Draft renewal questions and a plain-language explanation of the changes for the insured."
- An underwriter/agent needs a consistent, cited renewal write-up to attach to the account file.

## Do not use
- The user wants a **renewal decision** ("should we renew / non-renew / decline?"), a **price
  or rate**, to **bind** the renewal, or to **issue a non-renewal notice** → out of scope.
  Provide the comparison and route to the licensed underwriter; underwriting decision support
  is `insurance-underwriting-risk-reviewer` (which itself drafts rationale for human underwriting).
- **Coverage-need / exposure-adequacy analysis** ("do I have enough coverage / any gaps?") →
  `coverage-gap-analyzer`.
- **Clause-level wording comparison** of specific forms/endorsements → `policy-wording-comparator`.
- **Comparing competing market quotes** (not expiring-vs-proposed on one policy) →
  `premium-quote-comparator`.
- **Plain explanation of a single policy document** with no renewal comparison →
  `policy-document-explainer`.
- **Deep review of a specific claim** in the loss history → `claim-file-quality-reviewer`; catastrophe
  accumulation/modeled-loss monitoring → `catastrophe-exposure-monitor`.
- **Personalized insurance advice** ("which option should I buy?") → decline; route to a
  licensed agent/broker.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill emits a renewal comparison pack
with a durable `review_id`; downstream underwriting, wording, coverage-gap, and claims skills
consume it. It must not duplicate their decision, pricing, or determination steps.

## Inputs and prerequisites
- **Policy identifier** and both terms to compare: the **expiring** term and the **proposed**
  renewal term, each with effective/expiration dates, annual premium, coverages
  (`limit`, `deductible`), exposures (`basis`, `value`), and forms/endorsements
  (`form_id`, `edition`).
- **Loss history** for the review window (default 1,095 days / 3 years): claims with
  `date_of_loss`, `incurred`, `paid`, `status`, `cause`, and a `source_ref`.
- Approved thresholds/config (see [references/domain-rules.md](references/domain-rules.md)) and a
  `config_version`. Schema: [scripts/validate_input.py](scripts/validate_input.py).
- Read access to policy administration, claims, and underwriting-rules/config.

## Source hierarchy
See [references/source-map.md](references/source-map.md). The policy administration system is the
position of record for terms; claims is the position of record for loss history; the filed/approved
forms library resolves form editions; versioned underwriting config supplies thresholds and the
disposition mapping. Cite every finding's evidence to a source row.

## Workflow
1. **Scope & load** — confirm the policy and the two terms to compare; load loss history for the
   review window; validate with `validate_input`. Fail closed on structural problems.
2. **Compute findings (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py) to compute the configured
   findings (premium change, exposure change, limit reduction, deductible increase, coverage
   removed/added, form/endorsement change, loss-ratio flag, large/open claim, rate-vs-exposure
   divergence). Each finding returns a factual reason and the evidence rows behind it. Findings are
   **explainable**, not a black-box score.
3. **Assemble evidence** — for each fired finding, attach the specific expiring/proposed values (or
   claim rows) and their citations.
4. **Suggest disposition** — map the fired-finding profile to a review band (Routine / Review /
   Escalated) per the configured, documented mapping. This is a **triage suggestion for a human**,
   explicitly **not** a renewal, pricing, or coverage determination.
5. **Draft questions & explanation** — turn each fired finding into a renewal question for the human
   to raise and a plain-language explanation of the change for the insured; include the context
   prompts (benign explanations to weigh) and the standing disclaimer.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py) after. The
output check confirms: every fired finding has evidence + citation, no determination / pricing /
action / personalized-advice language is present, the disposition maps deterministically from the
fired findings, the standing disclaimer is present, and context prompts are included. Fail closed on
any miss.

## Human approval
`external-delivery`: human review is required before the comparison or any customer explanation is
sent to the insured/producer or written to a system of record. No approval is needed for the
reviewer's own read. The skill never renews, prices, binds, issues a notice, or takes any policy
action.

## Failure handling
- **Missing a term** (only expiring or only proposed present) → stop; a renewal comparison needs both.
- **Ambiguous policy/identity** → stop and confirm; never compare the wrong policy or term.
- **Missing coverages/exposures/forms/claims** → compute only the findings the data supports; label
  the rest `not_evaluable`; do not infer a change from absent data.
- **Stale/conflicting sources** (policy-admin vs. a quote document) → cite both; do not resolve
  silently.
- **Tool timeout** → return the findings computed so far with a clear "incomplete" flag; page long
  loss histories as resumable stages.

## Output contract
1. **Summary** — policy (masked), line of business, terms compared, count of fired findings,
   suggested disposition band.
2. **Findings** — per fired finding: name, plain-language reason, contribution, evidence rows
   (cited), and the basis/threshold it compared against.
3. **Renewal questions** — the human-facing questions to raise, one per fired finding (non-directive).
4. **Consider (context prompts)** — benign explanations (exposure growth, inflation guard, scheduled
   filings, bureau/state form changes, insured requests) so the reviewer weighs both sides.
5. **Data gaps / not-evaluable findings.**
6. **Machine-readable** — findings + evidence + `review_id` for downstream skills.
7. **Standing disclaimer** — "Comparison and review evidence only; not a renewal, pricing, or
   coverage determination. No renewal decision or notice has been issued."
See [references/controls.md](references/controls.md).

## Privacy and records
Customer NPI/PII. Mask policy/account numbers (last 4). Minimize insured data in output to what
evidences a fired finding. Retain the comparison + citations + `config_version` per records policy;
log the read and any external-delivery approval. Never exfiltrate customer data.

## Gotchas
- **A finding is not a decision.** Many fired findings justify an *Escalated review*, never a
  renew/non-renew conclusion, a price, or a coverage determination.
- **Premium change ≠ rate action.** A premium can move because exposure moved. Report the factual
  premium delta and the rate-vs-exposure divergence; let the underwriter attribute cause.
- **Silent limit erosion.** The highest-value catches are often a quietly reduced limit, an increased
  deductible, or a dropped coverage — compare coverage-by-coverage, not just total premium.
- **Form editions matter.** An edition change on the same `form_id` can materially change coverage;
  flag it and route the wording question to `policy-wording-comparator`. Do not judge the wording here.
- **Loss ratio is context, not verdict.** Read it with development, large-loss treatment, and
  credibility; it never by itself decides the renewal.
- **Thresholds come from versioned config**, never tuned to an individual insured to force or avoid a flag.

## Evidence and handoff contract

Read [the insurance evidence contract](references/insurance-contract.md) for source
versioning, explicit unknowns, financial/date bases and receiver validation. A
content hash is not source authentication, professional approval or execution authority.
