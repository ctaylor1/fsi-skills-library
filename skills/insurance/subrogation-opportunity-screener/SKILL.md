---
name: subrogation-opportunity-screener
description: >-
  Scan open and closed claims for missed subrogation/recovery potential — identify responsible
  third parties, compute explainable recovery signals, assemble source-linked evidence, check the
  diaried limitation window, estimate the referral economics, and prepare a cited referral for a
  licensed recovery/subrogation specialist. Use when a claims or recovery specialist asks "does
  this claim have subrogation potential we missed", "who is the responsible party and is the
  limitation window still open", or "screen these claims for recovery and prepare a referral".
  HARD BOUNDARY: this skill screens and evidences recovery signals and suggests a triage band; it
  NEVER makes a subrogation, liability, or limitation (time-bar) determination, and NEVER issues a
  demand, files suit, places a lien, negotiates, waives, releases, or closes a recovery — those are
  human/licensed-specialist actions.
license: MIT
compatibility: Amazon Quick Desktop; requires claims, policy-administration, payments/recovery-ledger, limitation-rules, party/external-records, document-intelligence, and approved-calculation MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Insurance"
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
  aws-fsi-owner: "Insurance underwriting & claims"
  aws-fsi-primary-user: "Claims recovery / subrogation specialist"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Subrogation Opportunity Screener

## Purpose and outcome
Given a claim's financials, loss facts, party roster, evidence inventory, and diaried limitation
date, compute a set of **explainable recovery signals**, explain in plain language why each fired,
attach evidence to each, compute the **referral economics** (net expected recovery), and produce a
review-ready pack with a **suggested screening band** (Refer / Review / No-Action). A successful
output lets a claims or recovery specialist decide whether to pursue subrogation — the
determination, and any recovery action, remains human.

## Use when
- "Does this paid claim have subrogation/recovery potential we missed?"
- "Who is the responsible third party and is the limitation window still open?"
- "Screen this book of closed claims for recovery opportunities and prioritize them."
- A specialist needs a consistent, cited recovery write-up and referral economics to attach to a
  claim before referral.

## Do not use
- The user wants a **subrogation, liability, or time-bar determination**, a **demand issued**,
  **suit filed**, a **lien placed**, or a recovery **waived/closed** → out of scope. Provide the
  screening evidence and route to a licensed recovery specialist / counsel.
- **Fraud** indicators dominate (staged loss, misrepresentation) → `claims-fraud-referral-assistant`
  (draft-only; no fraud finding).
- **Reserve development** to reflect anticipated recovery → `reserving-analysis-assistant`.
- **Full claim-file review** (documentation, chronology, reserve support) → `claims-file-reviewer`.
- **Policy-form / endorsement comparison** (e.g., confirm a waiver-of-subrogation endorsement) →
  `policy-wording-comparator`.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill emits a referral pack with a
durable `screening_id`; downstream fraud, reserving, file-review, and reinsurance skills consume it.
The actual subrogation decision (pursue, demand, file, negotiate, waive) belongs to a **licensed
recovery specialist / counsel**, not to any skill. It must not duplicate their determination or
action steps.

## Inputs and prerequisites
- Claim identifier and the **claim financials** (paid to date, recoverable deductible, reserve) plus
  loss facts (loss date, state, cause).
- **Responsible-party roster** (each with role, liability share, insurer, and collectibility
  indicators) and an **evidence inventory** (police/expert reports, liability admissions, photos,
  estimates), each with a `source_ref`. Schema: [scripts/validate_input.py](scripts/validate_input.py).
- The **diaried limitation date** (jurisdiction/claim-type specific). If absent, `limitation_window_open`
  is **not evaluable** and must be resolved before reliance.
- Read access to claims, policy, recovery ledger, limitation rules, and party records; approved
  config floors/factors (see [references/domain-rules.md](references/domain-rules.md)).

## Source hierarchy
See [references/source-map.md](references/source-map.md). The claims system is the position of
record for financials and status; policy administration resolves waiver/anti-subrogation
conditions; the limitation-rules pack plus the diaried calendar govern the limitation posture; party
records resolve collectibility. Cite every signal's evidence to a source row.

## Workflow
1. **Scope & validate** — confirm the claim and load financials, parties, evidence, and the
   limitation date; validate with `validate_input`. Surface data gaps (especially a missing
   limitation date) as warnings.
2. **Compute signals (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py) to compute the configured
   recovery signals (third-party liability indicated, recovery above floor, limitation window open,
   supporting evidence present, recovery not waived, collectible responsible party, positive expected
   recovery). Each signal returns a contribution and the evidence rows behind it. Signals are
   **explainable**, not a black-box score.
3. **Compute referral economics** — recovery base × liability share × collectibility factor, less
   estimated pursuit cost = net expected recovery. This is triage economics, not a promise.
4. **Assemble evidence** — for each fired signal, attach the specific party/financial/evidence rows
   and the basis, with citations.
5. **Suggest band** — map the fired-signal set (plus the time-critical flag) to a screening band
   (Refer / Review / No-Action) per the deterministic, documented mapping. This is a triage
   suggestion for a human, explicitly **not** a subrogation determination.
6. **Write the pack** — plain-language explanation per signal + evidence + economics + suggested
   band + explicit counter-considerations (comparative negligence, collectibility, anti-subrogation
   / made-whole, limitation nuances) for the specialist to weigh.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py) after. The
output check confirms: every fired signal has evidence + citation, no determination/action language
is present, the band maps deterministically from the fired signals (+ time-critical flag), the
standing disclaimer is present, and counter-consideration prompts are included whenever the band is
not No-Action. Fail closed on any miss.

## Human approval
`external-delivery`: human review required before the referral is sent to a recovery specialist /
counsel or written to the claim system of record. No approval is needed for the specialist's own
read. The skill never takes a recovery action.

## Failure handling
- **Missing limitation date** → `limitation_window_open` is not evaluable; state that the controlling
  date must be resolved; never conclude the claim is or is not time-barred.
- **Ambiguous claim/identity** → stop and confirm; never screen the wrong claim.
- **No responsible party / thin evidence** → compute only the signals the data supports; label the
  rest "not evaluable"; do not overstate recovery potential.
- **Waiver of subrogation or prior/open recovery** → `recovery_not_waived` does not fire; band is
  No-Action; do not refer an unavailable or duplicate recovery.
- **Stale/conflicting sources** (rules pack vs diaried date) → cite both; do not resolve silently.
- **Tool timeout** → return partial signals computed so far with a clear "incomplete" flag.

## Output contract
1. **Summary** — claim (masked), line of business, count of fired signals, net expected recovery,
   suggested band, and the limitation posture (days remaining / time-critical).
2. **Signals** — per fired signal: name, plain-language reason, contribution, evidence rows (cited),
   and the basis.
3. **Referral economics** — recovery base, liability share, collectibility factor, gross and net
   expected recovery.
4. **Consider (counter-considerations)** — comparative negligence, collectibility, anti-subrogation /
   made-whole, jurisdiction-specific limitation — so the specialist weighs both sides.
5. **Data gaps / not-evaluable signals.**
6. **Machine-readable** — signals + evidence + economics + `screening_id` for downstream skills.
7. **Standing disclaimer** — "Screening evidence only; not a subrogation, liability, or limitation
   determination. No demand, filing, waiver, or recovery action has been taken."
See [references/controls.md](references/controls.md).

## Privacy and records
Customer NPI/PII and third-party PII. Mask claimant/party identifiers where not needed to evidence a
signal; minimize third-party data to what supports the referral. Retain the screening + citations +
config version per records policy; log the read and any external-delivery approval. Never exfiltrate
claim or third-party data.

## Gotchas
- **A signal is not a decision.** A full set of fired signals justifies a *referral*, never a
  subrogation, liability, or time-bar conclusion, and never a demand or filing.
- **Limitation is the highest-stakes field.** A live window can lapse and destroy a recovery right —
  the screen flags `time_critical` and forces at least Review, but the *controlling* limitation
  period (which varies by jurisdiction and claim type) must be confirmed with counsel. Never state a
  claim is time-barred.
- **Recovery base ≠ incurred.** The recoverable base is paid to date plus the insured's reimbursed
  deductible; do not seek amounts not actually paid.
- **Collectibility matters more than liability.** A 100%-at-fault but judgment-proof, uninsured party
  yields little — the collectibility factor and the counter-considerations exist for this.
- **Anti-subrogation / made-whole / waiver endorsements** can bar an otherwise strong recovery; the
  `recovery_not_waived` signal and the policy-condition prompt guard against referring a barred claim.
- **Do not tune floors to a claim**: floors and factors come from the approved config, not from
  guessing what "should" be worth pursuing here.
