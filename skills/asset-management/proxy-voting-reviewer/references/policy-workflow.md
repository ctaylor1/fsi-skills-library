Read [references/policy-domain-rules.md](policy-domain-rules.md) for the supplied-input validation boundary and current deterministic limits before using the scripts.


# Voting Policy Consistency Checker

## Purpose and outcome
Given a ballot, a human analyst's **proposed vote** per agenda item, the firm's **versioned
voting policy**, and **analogous prior cases**, produce a cited **consistency review**: each
item is classified `aligned` / `deviation` / `case_by_case` / `no_policy`, the exact
effective policy guideline and analogous precedents are cited, and every non-aligned finding
lists the human-adjudication action it requires. A successful output lets a proxy-voting
analyst or the voting committee see exactly where a proposed vote departs from policy or
precedent — and what to document — **before** anyone decides or records the vote. The
decision, change, and submission of any vote remain human.

## Use when
- "Does my proposed vote on this ballot follow our voting policy?"
- "Is this vote consistent with how we voted on similar proposals before?"
- "Flag any deviations from policy or precedent on this meeting's agenda."
- A reviewer needs a consistent, cited deviation write-up to attach before adjudication.

## Do not use
- The user wants the skill to **decide, change, cast, submit, or finalize** a vote, or to
  confirm a proposed vote as "approved" → out of scope; this mode only evidences
  consistency. The decision and submission are a human/voting-committee action in the
  proxy-voting system of record.
- The user needs the underlying **evidence bundle assembled** (agenda, disclosures,
  ownership/entitlement, policy, precedent) → `proxy-voting-reviewer`.
- The deviation is really about an active **stewardship engagement** or firm position on the
  issuer → `issuer-engagement-reviewer`.
- The question is whether **portfolios/proposed trades breach mandate/guideline/ESG/
  restriction rules** (not vote-vs-policy) → `investment-mandate-reviewer`.
- The user wants **personalized investment advice** or a merits opinion on a proposal →
  out of scope for every skill in this library.

## Adjacent-skill handoffs
See [references/policy-handoffs.md](policy-handoffs.md). This mode consumes an upstream
evidence bundle (`packet_id`) and emits a cited review (`review_id`); it does not assemble
the bundle, choose a firm position, or cast/submit a vote. Deviations route to the human
analyst / voting committee for adjudication.

## Inputs and prerequisites
- The **ballot / meeting**: `meeting_id`, `issuer`, `meeting_date`, `policy_version`, and
  `agenda_items[]`, each with a `category` and the analyst's `proposed_vote`
  (`For|Against|Abstain|Withhold`).
- The **voting policy**: `policy_guidelines[]`, each with `category`, `default_position`
  (`For|Against|Abstain|Withhold|Case-by-case`), `policy_ref`, `version`, `effective_date`.
- **Precedents**: `precedents[]` of prior firm votes by category and `meeting_date`.
- Optional `packet_id` linking the upstream evidence bundle. Schema and evaluability rules:
  [scripts/policy_validate_input.py](../scripts/policy_validate_input.py).

## Source hierarchy
See [references/policy-source-map.md](policy-source-map.md). Firm **voting policy** (versioned,
effective-dated) is the position of record; the **precedent store** supplies analogous prior
votes; the **ballot** supplies the proposed votes under review; **research-provider** inputs
are advisory context only, never an override. Cite every finding to its guideline and
precedent rows.

## Workflow
1. **Scope & validate** — confirm the meeting and that each item has a `proposed_vote`; load
   policy and precedent; run `validate_input` (flags not-yet-effective guidelines,
   no-policy categories, and precedent-free categories).
2. **Select effective policy (deterministic)** — for each item, pick the guideline whose
   `effective_date ≤ meeting_date`, latest such; ignore future-dated guidelines
   ([references/policy-domain-rules.md](policy-domain-rules.md)).
3. **Classify (deterministic)** — run
   [scripts/policy_calculate_or_transform.py](../scripts/policy_calculate_or_transform.py) to compare the
   proposed vote to the policy position → `aligned` / `deviation` / `case_by_case` /
   `no_policy`, each with a policy citation.
4. **Precedent consistency** — count concordant/discordant analogous prior votes per item
   with `case_id` citations; report not-evaluable when no analogue exists.
5. **Roll up & list actions** — map findings to a deterministic `overall_disposition` and
   attach a human-adjudication `required_action` to every non-aligned finding.
6. **Write the review** — plain-language finding per item + citations + disposition +
   required actions + the standing disclaimer. Take no position on the merits.

## Validation loop
Run `validate_input` before and [scripts/policy_validate_output.py](../scripts/policy_validate_output.py)
after. The output screen confirms: every finding is cited, every non-aligned finding has a
human-adjudication action, the disposition maps deterministically from the findings, **no
vote-decision/action language is present**, and the disclaimer is included. Fail closed on
any miss (a review asserting a decided/cast/submitted vote MUST be rejected).

## Human approval
`required`: mandatory human adjudication before any vote is decided, changed, recorded, or
submitted. This mode never performs or recommends that step; it hands over a cited review
and the required-action list. No approval is needed for the analyst's own read of the review.

## Failure handling
- **Missing/not-yet-effective policy** for a category → classify `no_policy`; do not infer a
  position; route to the policy owner.
- **No analogous precedent** → report precedent consistency as *not-evaluable*, never
  "consistent".
- **Ambiguous meeting/issuer identity** → stop and confirm; never review the wrong ballot.
- **Policy vs precedent conflict** → cite both and flag; do not resolve silently.
- **Tool timeout** → return findings computed so far with a clear "incomplete" flag; page
  long agendas as resumable stages.

## Output contract
1. **Summary** — meeting (masked where needed), `policy_version`, item counts by status,
   `overall_disposition`.
2. **Findings** — per item: status, proposed vote, policy position + citation, precedent
   concordant/discordant counts + citations, and (non-aligned) the `required_action`.
3. **Machine-readable** — findings + `review_id` (+ upstream `packet_id`) for the reviewer
   and downstream steps.
4. **Standing disclaimer** — "Consistency findings and cited evidence only; not a voting
   decision or instruction. This review does not cast, change, or submit any vote; a human
   analyst adjudicates and records the vote in the system of record."
See [references/policy-controls.md](policy-controls.md).

## Privacy and records
MNPI / client-confidential. Voting intentions can be market-sensitive; minimize free-text,
and never disclose a client's voting intention outside the authorized workflow. Retain the
review, citations, and `policy_version` per records policy; log the read and any subsequent
human adjudication. Never exfiltrate ballot or client data.

## Gotchas
- **A deviation is not a decision.** Surfacing a departure justifies *documented review*,
  never a vote cast, changed, or submitted by this mode.
- **The proposed vote is the object under review**, not the authority — never treat it as
  "correct" or approve it.
- **Effective dating matters**: a future-dated guideline is not in force; a superseded
  prior-cycle guideline must not be applied. Selection is by `effective_date ≤ meeting_date`,
  latest.
- **Case-by-case ≠ deviation**: it flags that documented rationale and adjudication are
  required, not that the vote is wrong.
- **Proxy-advisor recommendations are context, not policy**: cite firm policy as the
  authority when they diverge.
- **No merits opinion**: describe consistency factually; do not argue for or against the
  proposal.
