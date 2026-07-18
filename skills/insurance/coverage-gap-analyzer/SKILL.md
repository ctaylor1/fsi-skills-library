---
name: coverage-gap-analyzer
description: >-
  Compare a policyholder's stated needs and exposures against their policy's coverages,
  limits, sublimits, deductibles, exclusions, and endorsements; surface explainable coverage
  gaps with dual (needs + policy) citations, and suggest a review priority for a licensed
  professional. Use when a policyholder, agent, or broker asks "where am I underinsured",
  "does my policy cover this exposure", "check my coverage against my needs", "analyze my
  homeowners/commercial policy for gaps", or wants a review-ready gap list before a renewal
  or client meeting. This skill evidences gaps and suggests a review priority only; it NEVER
  determines whether a claim is or would be covered, decides eligibility, gives insurance or
  legal advice, or recommends buying/dropping/switching a specific policy — those are
  licensed-professional decisions.
license: MIT
compatibility: Amazon Quick Desktop; requires policy-administration, document-intelligence, producer/needs-analysis, actuarial/catastrophe reference-data, and approved-config MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Insurance"
  aws-fsi-skill-type: "Analysis and evaluation skills"
  aws-fsi-risk-tier: "R2"
  aws-fsi-archetype: "Analyze & review"
  aws-fsi-agent-pattern: "Interactive decision-support copilot"
  aws-fsi-delivery-wave: "Wave 1 - stabilize existing"
  aws-fsi-action-mode: "Read-only analysis"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "existing-updated"
  aws-fsi-human-approval: "external-delivery"
  aws-fsi-data-classification: "Highly Confidential (customer NPI/PII)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Insurance underwriting & claims"
  aws-fsi-primary-user: "Policyholder / agent or broker"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Coverage Gap Analyzer

## Purpose and outcome
Given a policyholder's **stated needs and exposures** and their **policy of record**,
compute a set of **explainable coverage gaps** (missing coverage, excluded peril, limit and
sublimit shortfalls, coinsurance shortfall, deductible burden, missing endorsement), attach
evidence with **dual citations** (the needs item + the policy term), and produce a
review-ready analysis with a **suggested review priority**. A successful output lets a
licensed agent, broker, or underwriter see exactly where the policy may fall short of the
stated needs and decide what to discuss with the client — the coverage decision and any
advice remain with the licensed professional.

## Use when
- "Where am I underinsured / where are the gaps in my policy?"
- "Does my homeowners/commercial policy cover this exposure?"
- "Compare my coverage against my needs and list the gaps with citations."
- An agent or broker wants a consistent, cited gap list to attach to a client review or renewal prep.

## Do not use
- The user wants a **coverage/eligibility/claim determination** ("is this covered?", "will
  this claim be paid?") → out of scope; surface the gap and route to a licensed professional.
- The user wants **personalized advice or a purchase recommendation** ("what should I buy?",
  "should I drop this?") → out of scope; this skill does not advise or recommend transactions.
- Plain-language **policy walkthrough** with no needs comparison → `policy-document-explainer`.
- **Form/endorsement wording** vs. an approved/filed form (clause-level, R3) → `policy-wording-comparator`.
- Comparing **priced quotes/options** across carriers → `premium-quote-comparator`.
- **Renewal** term-change comparison and customer questions → `policy-renewal-reviewer`.
- An **actual loss/claim** (readiness or a denial appeal) → `claim-readiness-checker` or
  `claim-denial-appeal-helper`.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill emits a gap analysis with a
durable `analysis_id`; downstream explain/compare/renewal/claim skills consume it. It must
not duplicate their determination, advice, or drafting steps.

## Inputs and prerequisites
- A **profile** with stated exposures — each with a category, a value, and where possible a
  `peril`, a `required_coverage`, a `sublimit_category`, and/or a `recommended_endorsement`.
- The **policy of record**: coverages (type, limit, deductible, optional sublimits and
  coinsurance), exclusions (peril), and endorsements. Schema:
  [scripts/validate_input.py](scripts/validate_input.py).
- Read access to policy administration, document intelligence, and producer/needs systems;
  approved thresholds/config (see [references/domain-rules.md](references/domain-rules.md)).

## Source hierarchy
See [references/source-map.md](references/source-map.md). The **policy of record** governs
what is in force; document intelligence supplies clause/page citations; stated exposures are
**client-provided and unverified** inputs, never coverage facts. Cite every gap to both the
needs item and the policy term.

## Workflow
1. **Scope & load** — confirm the profile and the policy; load stated exposures and the full
   coverage schedule (coverages, limits, sublimits, deductibles, exclusions, endorsements);
   validate with `validate_input`.
2. **Compute gaps (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py) to compute the
   configured gaps. Each fired gap returns its evidence rows and **dual citations**. Gaps are
   **explainable and rule-based**, not a black-box score; gap types with no data to evaluate
   are reported under `not_evaluable`.
3. **Assemble evidence** — for each fired gap, attach the specific exposure and the policy
   term it deviates from, with both citations and the measured shortfall.
4. **Suggest priority** — map the fired-gap profile to a review-priority band (Informational
   / Review / Elevated) per the configured, documented mapping. This is a triage suggestion
   for a licensed professional, explicitly **not** a coverage determination.
5. **Write the analysis** — plain-language explanation per gap + the evidence + the suggested
   priority + explicit review prompts (context to weigh, e.g., other policies, replacement-
   cost basis, intentional deductible) and the standing disclaimer.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py)
after. The output check confirms: every fired gap has evidence with **both** citations, no
coverage/eligibility/claim-determination or advice language is present, the priority maps
deterministically from the fired gaps, the standing disclaimer is present, and review prompts
are included when any gap fired. Fail closed on any miss.

## Human approval
`external-delivery`: a licensed professional must review before the analysis is sent to a
customer or written to a case/system of record. No approval is needed for the reviewer's own
read. The skill never binds, quotes, decides coverage, or advises a transaction.

## Failure handling
- **Sparse exposures / policy** (missing required fields) → `validate_input` fails closed;
  state what is missing rather than guessing coverage.
- **Ambiguous profile/policy identity** → stop and confirm; never analyze the wrong policy.
- **Missing peril / required_coverage / sublimit / coinsurance data** → compute only the gaps
  the data supports; report the rest under `not_evaluable`.
- **Dec page vs. endorsement conflict** → cite both; do not resolve silently.
- **Stated value obviously unverified or stale** → note it; do not treat client-stated values
  as coverage facts.
- **Tool timeout** → return the gaps computed so far with a clear "incomplete" flag.

## Output contract
1. **Summary** — profile (masked), policy (masked), `as_of`, count of fired gaps, suggested priority band.
2. **Gaps** — per fired gap: type, plain-language reason, evidence rows with **dual
   citations**, and the measured shortfall/basis.
3. **Not evaluable** — gap types with insufficient data and why.
4. **Review prompts** — context a licensed professional must weigh (other policies,
   replacement-cost basis, intentional deductible, statutory/lender minimums).
5. **Machine-readable** — gaps + evidence + `analysis_id` for downstream skills.
6. **Standing disclaimer** — "Coverage-gap analysis only; not a coverage, eligibility, or
   claim determination and not insurance or legal advice. Consult a licensed insurance
   professional before acting."
See [references/controls.md](references/controls.md).

## Privacy and records
Customer NPI/PII. Mask policy/account numbers (last 4). Minimize customer data in output to
what evidences a fired gap. Retain the analysis + citations + config version per records
policy; log the read and any external-delivery approval. Never exfiltrate customer data.

## Gotchas
- **A gap is not a coverage decision.** A fired gap justifies a *review/discussion*, never a
  statement that a claim is or would be covered, paid, or denied.
- **Stated values are unverified.** Exposure values are client-provided; a "shortfall"
  reflects the stated value, not an appraised or agreed value — the review prompts exist for this.
- **Endorsements buy coverage back.** An excluded peril with a matching buy-back endorsement
  is **not** a gap; check endorsements before flagging `exclusion_match`.
- **Sublimits hide inside adequate aggregate limits.** A generous personal-property limit can
  still leave a jewelry sublimit far below the stated value — always check the sublimit.
- **Don't tune thresholds to a person.** Thresholds come from the approved, versioned config,
  not from guessing what "should" be adequate for this customer.
- **No adequacy verdict and no purchase steer.** Report the measured gap factually; do not
  conclude the policy is sufficient/insufficient or recommend buying, dropping, or switching.
