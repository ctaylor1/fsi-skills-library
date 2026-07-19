---
name: identity-access-reviewer
description: >-
  Review identities, accounts, roles, entitlements, segregation-of-duties conflicts,
  privileged and dormant access, inactivity, and certification evidence for an org unit, and
  stage revocation candidates for human approval. Produces explainable, rule-based findings
  with cited evidence (SoD toxic pairs, dormant/unapproved privileged access, orphaned
  accounts, stale certifications, privileged-without-MFA) and a suggested review priority.
  Use when an IAM analyst or control owner asks to run an access review or recertification
  prep, screen entitlements for exceptions, check segregation of duties, or find
  privileged/dormant/orphaned access with review-ready evidence. HARD BOUNDARY: R3 decision
  support only — it never grants, denies, or approves access, never revokes, disables,
  deprovisions, or removes an entitlement, never certifies or signs an attestation, and never
  closes the review or writes an IAM system of record; every revocation is staged for a human
  control owner to adjudicate and execute.
license: MIT
compatibility: Amazon Quick Desktop; requires IAM/IGA, HR-roster, SIEM/access-log, CMDB, and approved-config MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Cybersecurity & Operational Resilience"
  aws-fsi-skill-type: "Analysis and evaluation skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Analyze & review"
  aws-fsi-agent-pattern: "Interactive decision-support copilot"
  aws-fsi-delivery-wave: "Wave 3 - regulated casework"
  aws-fsi-action-mode: "Read-only analysis"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Confidential (security-sensitive)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "CISO / Operational Resilience"
  aws-fsi-primary-user: "IAM analyst / control owner"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Identity Access Reviewer

## Purpose and outcome
Given an org unit's identities, accounts, and entitlements, compute a set of **explainable,
rule-based access findings** (segregation-of-duties conflicts, dormant/unapproved privileged
access, orphaned accounts, stale certifications, privileged-without-MFA, over-entitlement),
attach cited evidence to each, **stage revocation candidates for approval**, and produce a
review-ready pack with a **suggested review priority**. A successful output lets an IAM
analyst or control owner adjudicate access exceptions and prepare a recertification with
consistent evidence — the access decision, the revocation, and the certification remain human.

## Use when
- "Run an access review / recertification prep for this org unit or application."
- "Screen these entitlements for segregation-of-duties conflicts."
- "Find dormant privileged accounts, orphaned accounts, or grants overdue for certification."
- "Which privileged access lacks MFA or an approval record?"
- A control owner needs a cited access-exception write-up to attach to a certification campaign.

## Do not use
- The user wants to **execute** the change — revoke/remove a grant, disable/deprovision an
  account, or sign a certification. Out of scope: produce evidence + staged candidates and
  route to the human control owner and IAM operations (see Human approval).
- **Active identity misuse / account takeover** needing alert enrichment or investigation →
  `security-alert-triage-assistant` or `phishing-and-bec-investigator`.
- **Cloud IAM misconfiguration** (over-broad policy, public role) rather than grant-level
  review → `cloud-security-posture-reviewer`.
- **Supplier / subcontractor** identity and access assurance → `third-party-cyber-risk-reviewer`.
- A confirmed **incident** needing coordinated response → `cyber-incident-response-coordinator`.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill emits an access-review pack
with a durable `review_id`; downstream triage/investigation/reporting skills consume it. The
actual revocation and certification sign-off are authorized human/IAM-operations actions
outside this skill — there is no catalog skill that executes writes. It must not duplicate a
downstream skill's decision or action steps.

## Inputs and prerequisites
- The **org unit / application scope** and an `as_of` date.
- An **access extract**: `identities` (user_id, HR status), `accounts` (owner, type,
  last_login, MFA state), and `entitlements` (grant, privileged flag, approval_ref,
  last_certified), each with a `source_ref`. Schema:
  [scripts/validate_input.py](scripts/validate_input.py).
- The versioned **access-control config**: SoD ruleset, inactivity/dormancy thresholds,
  certification interval, over-entitlement limit (see
  [references/domain-rules.md](references/domain-rules.md)); record its `config_version`.
- Read access to IAM/IGA, the HR roster, and access logs.

## Source hierarchy
See [references/source-map.md](references/source-map.md). The IAM/IGA entitlement record is
the position of record for what access exists; HR is the position of record for worker
status; access logs supply last-use and MFA signals. When IAM and HR conflict (active grant,
terminated owner) that conflict IS the finding — cite both, never resolve it silently.

## Workflow
1. **Scope & validate** — confirm the org unit, `as_of`, and config version; load the extract
   and validate it with `validate_input` (fails closed on structure; warns on data gaps that
   limit which findings are evaluable).
2. **Compute findings (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py) to compute the
   configured findings. Each fired finding returns its evidence rows with citations. Findings
   are **explainable rules**, not a black-box score; unevaluable rules are reported as
   `not_evaluable`.
3. **Stage revocation candidates** — for actionable findings the engine stages revocation
   **candidates** (`status: staged_for_approval`), deduplicated by grant, each tied to the
   fired finding. These are recommendations for a human, never executed changes.
4. **Suggest priority** — map the fired-finding profile to a review-priority band
   (Informational / Review / Elevated) per the documented deterministic mapping. This is a
   triage suggestion for a control owner, explicitly **not** an access decision.
5. **Write the pack** — plain-language explanation per finding + cited evidence + staged
   candidates + suggested priority + review-context prompts to weigh before adjudicating.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py)
after. The output check confirms: every fired finding has evidence + citation; the priority
maps deterministically from the fired set; **no decision / execution / closure / filing /
certification language** is present; every staged revocation is a candidate tied to a fired
finding (an executed status fails closed); the standing disclaimer is present; and context
prompts are included. Fail closed on any miss.

## Human approval
`required` (R3): a human control owner must **adjudicate every finding and approve every
staged revocation** before any access change, and the certification decision is theirs. The
skill never grants/denies access, never revokes/disables/deprovisions, never certifies, and
never closes the review or writes an IAM system of record. Approved removals are executed by
IAM operations through the provisioning / joiner-mover-leaver process, outside this skill.

## Failure handling
- **Missing `last_login`** → treat the account as inactive/dormant conservatively and flag
  it; never assume recent activity.
- **No SoD ruleset configured** → report `sod_conflict` as `not_evaluable`; do not invent
  toxic pairs.
- **Ambiguous scope / identity** → stop and confirm; never review the wrong org unit or map a
  grant to the wrong owner.
- **HR ↔ IAM conflict** → surface it as `orphaned_account` with both citations; do not resolve.
- **Stale / missing config version** → do not guess thresholds; record the version used and
  flag if unknown.
- **Tool timeout** → return the findings computed so far with a clear "incomplete" flag; page
  large org units as resumable stages.

## Output contract
1. **Summary** — org unit, `as_of`, config version, count of fired findings, suggested priority.
2. **Findings** — per fired finding: name, plain-language reason, criteria, evidence rows
   (cited), and the threshold/rule it breached.
3. **Staged revocation candidates** — grant, account, entitlement, related finding,
   `status: staged_for_approval` (for approval; not executed).
4. **Review-context prompts** — exceptions to weigh (break-glass, recent transfer, service
   account by design, planned leave, certification in progress).
5. **Not-evaluable findings** and data gaps.
6. **Machine-readable** — findings + evidence + staged candidates + `review_id` for downstream.
7. **Standing disclaimer** — "Access-review evidence and staged recommendations only; not an
   access decision. No entitlement has been revoked, disabled, or certified."
See [references/controls.md](references/controls.md).

## Privacy and records
Confidential, security-sensitive. Minimize output to the accounts/grants that evidence a
fired finding. Use worker **status** only from HR — do not expose broader HR PII. Retain the
review + citations + `config_version` per records policy; log the read and any control-owner
approval of staged revocations. Never exfiltrate identity or entitlement data.

## Gotchas
- **A finding is not a decision.** Many findings justify *review priority* and a *staged
  candidate*, never an access decision, a revocation, or a certification.
- **Missing `last_login` ≠ safe.** Absent activity data is treated as dormant/inactive, not
  ignored — an unmonitored privileged account is exactly the risk.
- **SoD is per-identity, across accounts.** A user can hold the two toxic entitlements on
  *different* accounts; evaluate conflicts at the identity level, not per account.
- **Break-glass / service accounts** legitimately look dormant, over-privileged, or MFA-exempt.
  The context prompts exist so the owner weighs approved exceptions before adjudicating.
- **Describe, don't accuse.** State a toxic pair or dormant privileged grant as a control
  exception with evidence; do not assert misuse or intent.
- **Config is a versioned contract.** Thresholds and SoD rules come from the approved config,
  never tuned to what "looks normal" for a person.
