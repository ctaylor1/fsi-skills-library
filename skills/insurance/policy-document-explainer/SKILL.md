---
name: policy-document-explainer
description: >-
  Explain an insurance policy document in plain language — what each coverage, limit,
  deductible, exclusion, condition, definition, endorsement, and premium line actually
  says — with every statement linked to the exact declarations line, section, or clause it
  comes from. Use when a policyholder or service agent asks "what does my policy cover",
  "explain this section/exclusion", "what's my deductible or limit", "walk me through my
  declarations page", or attaches a policy PDF, declarations page, or endorsement and wants
  a readable walkthrough. Informational only: it never decides whether a specific claim or
  loss is covered, makes an eligibility or coverage determination, predicts a claim
  outcome, tells the reader to buy/drop/switch/keep a policy, or gives insurance, legal, or
  tax advice — route those to the appropriate coverage, claims, or advice-boundary skill.
license: MIT
compatibility: Amazon Quick Desktop; requires policy-administration, claims, and document-intelligence MCP integrations plus an approved-source retrieval service for filed forms/endorsements (all read-only).
metadata:
  aws-fsi-category: "Insurance"
  aws-fsi-skill-type: "Guidance or domain-expertise skills"
  aws-fsi-risk-tier: "R1"
  aws-fsi-archetype: "Explain & summarize"
  aws-fsi-agent-pattern: "Interactive decision-support copilot"
  aws-fsi-delivery-wave: "Wave 1 - stabilize existing"
  aws-fsi-action-mode: "Read-only analysis"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "existing-no-changes"
  aws-fsi-human-approval: "external-delivery"
  aws-fsi-data-classification: "Highly Confidential (customer NPI/PII)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Insurance underwriting & claims"
  aws-fsi-primary-user: "Consumer (policyholder)"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Policy Document Explainer

## Purpose and outcome
Produce a faithful, plain-language walkthrough of what an insurance policy **says** so the
reader understands their coverages, limits, deductibles, exclusions, conditions, key
definitions, endorsements, and premium — each statement traceable to the exact document
source. A successful output lets a policyholder read their own policy in ordinary language,
**without** any determination of whether a particular claim would be paid and **without**
any advice about what policy to hold.

## Use when
- "What does my policy cover", "explain my declarations page", "walk me through this policy".
- "What does this exclusion / condition / definition mean", "explain Section I".
- "What's my deductible / my dwelling limit / my out-of-pocket for this coverage".
- The user attaches a policy PDF, declarations page, endorsement, or certificate and wants a
  readable explanation of what the document states.
- A service agent needs a clean plain-language explanation to attach to a customer response
  (external delivery requires human review — see Human approval).

## Do not use
- The user asks whether a **specific loss/claim is (or would be) covered or paid** → this is
  a coverage determination; do not answer it. State that it is a claims decision and route to
  the insurer/adjuster; for organized evidence use `claim-readiness-checker`.
- The user wants to know if they have **enough coverage or gaps vs. their needs/exposures** →
  route to `coverage-gap-analyzer` (analytical, still non-advice).
- A **claim was denied** and they want to understand and appeal it → `claim-denial-appeal-helper`.
- The user wants to **compare policies, quotes, or premiums** → `premium-quote-comparator`.
- The user (a professional) needs a **form/version/wording comparison against filed forms** →
  `policy-wording-comparator` (R3).
- The user wants advice on whether to buy, drop, switch, or keep coverage, or legal/tax
  advice → out of scope; do not answer it here.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). In short: this skill is the **upstream
plain-language map** of a single policy. It hands off a normalized policy-element map plus a
durable `explanation_id`; it never performs the downstream coverage analysis, claim
evaluation, comparison, or appeal itself.

## Inputs and prerequisites
- One policy document at a time: policy identifier (masked), form edition (e.g. `HO-3
  (07/2021)`), effective and expiration dates, and the document broken into sections with
  `section_type`, heading, text, and a source citation. See the input schema in
  [scripts/validate_input.py](scripts/validate_input.py).
- The **effective/expiration dates** and form edition, so the reader knows which version is
  being explained. Reject a document whose expiration precedes its effective date.
- Read permission to the policy-administration record and/or document-intelligence extraction
  of the attached document; approved-source retrieval for any referenced endorsement/form.

## Source hierarchy
Rank sources and cite every statement. See [references/source-map.md](references/source-map.md).
1. Policy-administration **system of record** for this policy (highest): in-force form,
   endorsements, declarations, effective dates.
2. The **executed policy document / declarations page** for the stated period (via
   document-intelligence) with page/section/clause citations.
3. **Filed/approved form and endorsement library** for the wording of standard forms the
   document references.
Never substitute a user assertion for the policy of record; if they conflict, surface the
conflict and cite both. Explain the **document as written** — do not resolve ambiguity by
guessing intent.

## Workflow
1. **Identify scope** — confirm the single policy, form edition, and effective/expiration
   window. If multiple policies, terms, or editions are present, ask which one (do not merge).
2. **Normalize** — map each element to the policy-element schema; classify each section
   (coverage, exclusion, condition, definition, endorsement, declaration, premium); attach the
   source citation (system + page/section/clause) to every element.
3. **Resolve references** — for each cross-reference (an endorsement or defined term the text
   points to), attach the referenced source; if a referenced endorsement/form is not present,
   record it as a **data gap** rather than guessing its content.
4. **Explain (plain language)** — restate each element in ordinary language, preserving limits,
   deductibles, sub-limits, and named perils exactly as written. Describe the document
   neutrally (third person: "the form / this coverage / Section I…"), never as a determination
   about the reader's situation.
5. **Surface gaps** — unreadable pages, unresolved cross-references, missing endorsements, or
   ambiguous wording are listed explicitly rather than filled in.
6. **Validate and disclaim** — run the validation loop and attach the standing disclaimer.

## Validation loop
Run `validate_input` before explaining and `validate_output` after. If an element lacks a
citation, the explained-element count does not tie to the elements listed, the output
contains coverage-determination / eligibility / claim-decision / advice language, or the
standing disclaimer is missing, **fix or fail closed** — do not deliver a
determination-tainted or uncited explanation. See [references/controls.md](references/controls.md).

## Human approval
None required for the user's own informational read. **Human review is required before the
explanation is delivered externally** (e.g., a service agent sending it to a customer) or
written to a system of record — `aws-fsi-human-approval: external-delivery`.

## Failure handling
- **Unreadable / partial document** → explain the sections that are legible, list the rest as
  "not readable — not explained"; never invent wording.
- **Missing form edition or effective dates** → state that the version is unconfirmed and
  explain conservatively; do not assume a standard form's contents.
- **Unresolved cross-reference / missing endorsement** → name it as a data gap; do not
  describe an endorsement that was not provided.
- **Multiple policies / editions in one file** → stop and ask; do not merge.
- **Source conflict** (user statement vs. policy of record) → present both with citations; do
  not pick a winner.
- **A coverage / claim-outcome question** → do not answer it; explain the relevant clause
  neutrally and route to the insurer/adjuster.
- **Tool timeout / permission denial** → report partial results and the exact gap; no retry
  assumption.

## Output contract
1. **Header** — policy label (masked), form edition, effective/expiration dates.
2. **Coverage walkthrough** — each coverage in plain language with its limit and deductible,
   cited.
3. **Exclusions & conditions** — what the form does not insure and the duties it imposes,
   neutrally described, cited.
4. **Definitions & endorsements** — key defined terms and any endorsements that modify the
   base form, cited.
5. **Data gaps** — unreadable, missing, or unresolved items listed explicitly.
6. **Machine-readable** — the normalized policy-element map with per-element citations, tagged
   with a durable `explanation_id` for downstream skills.
7. **Standing disclaimer** — "Informational explanation only; not a coverage determination,
   claim decision, or insurance/legal advice."
Every statement carries a source citation. See [references/controls.md](references/controls.md).

## Privacy and records
Customer NPI/PII. Mask policy and account numbers (show last 4) and the insured's identifying
details. Do not transmit the policy or explanation outside the approved environment. Retain the
explanation and its citations per records policy; log the read and any external-delivery
approval. See [references/controls.md](references/controls.md).

## Gotchas
- **"Explain" is not "determine"**: restating that Section I excludes flood is in scope;
  saying "your flood damage isn't covered" is a coverage determination and is out of scope.
- **Endorsements override the base form**: a base-form clause may be amended or deleted by an
  endorsement — explain the endorsement's effect, and flag when a referenced endorsement is
  missing rather than explaining the unamended base wording as final.
- **Limits vs. sub-limits**: a coverage limit and a category sub-limit (jewelry, electronics)
  are different numbers; preserve both exactly and don't conflate them.
- **Declarations vs. form**: the declarations page carries the actual dollar amounts; the form
  carries the wording. Cite the declarations for numbers and the form for terms.
- **Effective dates matter**: explain the version in force for the stated period; a policy can
  be reissued or amended mid-term.
- **Ambiguity is a finding, not a gap to fill**: if wording is genuinely ambiguous, say so and
  point to the insurer — do not resolve it in the reader's favor or against them.
