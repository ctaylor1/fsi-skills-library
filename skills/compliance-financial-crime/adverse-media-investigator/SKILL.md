---
name: adverse-media-investigator
description: >-
  Investigate adverse-media / negative-news hits on a customer or counterparty for
  financial-crime and reputational-risk review: resolve each hit to the subject or a namesake
  from identity signals, tier source quality, separate allegations from findings and resolved
  matters, score materiality, and assemble a durable case with a cited evidence bundle
  (chronology, parties, amounts) and a disposition RECOMMENDATION. Use when a financial-crime
  investigator, KYC/CDD analyst, or reputational-risk reviewer must work adverse-media hits,
  disambiguate common names, judge whether negative news is credible and relevant, or package
  evidence for enhanced due diligence. HARD BOUNDARY: decision support only — it never clears
  or closes a case, makes a sanctions/PEP or fraud/AML determination, recalculates a risk
  rating, drafts or files a SAR, attributes adverse media on a name alone, or produces
  customer-facing (tipping-off) content; every disposition is a recommendation a human
  adjudicates and routes.
license: MIT
compatibility: Amazon Quick Desktop; requires case-management, KYC/CDD, sanctions/PEP-data, regulatory/court-corpus, adverse-media-retrieval, transaction-monitoring, and records-archive MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Compliance & Financial Crime"
  aws-fsi-skill-type: "Analysis and evaluation skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Investigate & casework"
  aws-fsi-agent-pattern: "Case agent + evidence bundle"
  aws-fsi-delivery-wave: "Wave 3 - regulated casework"
  aws-fsi-action-mode: "Read-only analysis"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Restricted (AML/BSA — SAR confidentiality; tipping-off controls)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Compliance & Financial Crime (FIU)"
  aws-fsi-primary-user: "Financial-crime investigator / reputational risk"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Adverse Media Investigator

## Purpose and outcome
Take a batch of adverse-media / negative-news hits on one or more subjects (customers,
counterparties, beneficial owners) and produce, per subject, a **durable case** with a
**cited evidence bundle** and a **disposition recommendation**. The work is entity resolution
(is this hit our subject or a namesake?), source-quality tiering, separating allegations from
findings from resolved matters, and a documented materiality assessment. The outcome is an
audit-ready case a human adjudicator can act on — escalate to enhanced due diligence, route a
sanctions/PEP proximity to the specialist, monitor, or confirm no material adverse media —
without this skill ever making the regulated decision itself.

## Use when
- "Investigate the adverse-media hits on this customer — which are real matches?"
- "Are these negative-news articles about our subject or a namesake?"
- "Distinguish allegations from findings and assess source quality/relevance."
- "Package the adverse-media evidence for EDD / periodic review."

## Do not use
- **Sanctions/PEP match adjudication** (deciding a true match) → `sanctions-match-adjudicator`.
- **Customer risk-rating** recalculation → `customer-risk-rating-reviewer`.
- **EDD sign-off / assembly** as an approved package → `enhanced-due-diligence-packager`
  (this skill recommends and supplies evidence; it does not sign off).
- **SAR narrative drafting** → `suspicious-activity-report-drafter` (post-investigation, human-filed).
- Any request to **clear, close, or make a determination**, or to produce customer-facing
  notice of screening/SAR activity → refuse; recommend and route.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). Investigation (this skill) is separated
from the decisions it feeds — sanctions adjudication, rating change, EDD sign-off, SAR filing
— which carry different entitlements. This skill emits a durable `case_id` + evidence bundle;
it must not perform the downstream regulated decision.

## Inputs and prerequisites
- A screening batch: `config_version`, `as_of_date`, and `subjects[]`, each with identity
  fields (`name`, `type`, `dob`, `nationality`, `known_identifiers`) and candidate `hits[]`
  (source, tier, published date, category, assertion type, `entity_match`, named parties,
  amounts). Schema: [scripts/validate_input.py](scripts/validate_input.py).
- Read access to case management, KYC/CDD, sanctions/PEP flags, the regulatory/court corpus,
  adverse-media retrieval, and the versioned scoring config.

## Source hierarchy
See [references/source-map.md](references/source-map.md). Case management is the system of
record for the `case_id`; KYC supplies the identifiers that drive entity resolution; Tier-1
official/court sources outrank established media (Tier 2), which outrank low-reliability
aggregators (Tier 3). Cite every evidence item. Scoring tiers/weights are a **versioned
contract**.

## Workflow
1. **Validate & scope** — run `validate_input`; confirm each subject's identifiers and each
   hit's required fields; flag data gaps that will force `needs-data`.
2. **Resolve entities (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py): score each hit's
   `entity_match`; a DOB or identifier mismatch, or no name match, **discards** the hit as a
   namesake (recorded, not dropped). Only strong/weak matches proceed.
3. **Tier & classify** — tier the source (1/2/3) and label each matched hit `finding`,
   `allegation`, or `resolved-dismissed` (resolved = mitigating, scores 0).
4. **Score materiality (documented)** — category + assertion + source tier + recency give a
   per-hit relevance; the case score is the max; bands are Material / Watch / Not material.
5. **Recommend (never decide)** — route sanctions/PEP proximity to the specialist; flag an
   unresolvable subject `needs-data`; otherwise recommend escalate-EDD / monitor / no-material.
6. **Assemble the case** — durable `case_id`, chronology, parties, amounts, matched hits,
   discarded namesakes, and citations for every item.
7. **Never determine** — no closure, clearance, determination, or filing.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py)
after. The output screen enforces: durable `case_id`; recommendation-only dispositions (no
closure/clearance/determination/filing); band ties out to score and to the disposition;
routing carries a sanctions/PEP hit + specialist; `needs-data` lists the gap; every evidence
item is cited; no determination or tipping-off language; standing note present. Fail closed on
any miss.

## Human approval
`required`. Every escalation, EDD, sanctions/PEP determination, rating change, closure, and
filing needs a human owner (investigator / MLRO / BSA officer / licensed specialist). This
skill proposes and evidences; humans decide.

## Failure handling
- **Unresolvable subject** → `needs-data` with exactly what identifier is missing; never
  attribute adverse media on a name alone.
- **Ambiguous / partial match** → classify as strong/weak transparently, or discard as a
  namesake with the disambiguator recorded; do not auto-confirm.
- **Sanctions/PEP proximity** → route to the specialist; do not adjudicate identity or status.
- **Tier-3-only signal** → cannot reach Material without Tier-1/2 corroboration; monitor or
  needs-data.
- **Stale/conflicting sources** → cite each with its date; prefer the higher-tier source and
  surface the conflict; do not silently pick a side.
- **Tool timeout** → return the partial case with an explicit incomplete flag; no retry
  assumption.

## Output contract
1. **Case view** — per subject: `case_id`, materiality band, disposition (escalate-EDD |
   monitor | no-material-adverse-media | route-sanctions-pep | needs-data), one-line cited
   reason.
2. **Evidence bundle** — durable `case_id`, masked subject, chronology (dated matched events),
   parties, amounts, matched hits with entity-match basis + source tier + assertion type +
   relevance basis, discarded namesakes with disambiguators, and citations for every item.
3. **Data gaps / needs-data list** — the exact identifiers required to resolve a subject.
4. **Machine-readable** — the cases keyed by `case_id` (engine output).
5. **Standing note** — "Adverse-media investigation is decision support only; no case has been
   closed, no customer cleared or determined, and no filing has been made."
See [references/controls.md](references/controls.md) and
[references/domain-rules.md](references/domain-rules.md).

## Privacy and records
**Restricted — AML/BSA.** SAR-confidentiality and tipping-off controls apply: never produce
customer-facing content revealing screening, monitoring, or SAR activity. Mask government
identifiers and reduce DOB to year in output; keep named parties only as evidenced by cited
sources. Retain the case, evidence bundle, discarded-namesake rationale, citations, and
scoring `config_version` per BSA recordkeeping; log analyst identity on every read and
disposition.

## Gotchas
- **A name is not a match.** Common-name hits without a DOB/identifier are `needs-data`, not
  adverse media on the subject — the most consequential error in this domain is misattribution.
- **Allegation ≠ finding.** An unadjudicated allegation is weighted below a finding, and a
  dismissed/acquitted matter is *mitigating*, not adverse — but all three stay in the record.
- **Source tier is load-bearing.** A single low-reliability aggregator cannot make a case
  material; it needs corroboration from an official or established source.
- **Routing, not deciding.** Sanctions/PEP proximity goes to `sanctions-match-adjudicator`;
  this skill never confirms a true match or a designation.
- **Recommendations only.** Escalate/monitor/no-material are *recommendations*; the case is
  not closed, the customer is not cleared, and no SAR is drafted or filed here.
