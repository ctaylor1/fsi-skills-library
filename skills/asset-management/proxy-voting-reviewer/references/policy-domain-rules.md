# Domain Rules — proxy-voting-reviewer

## Supplied-input validation boundary

The bundled scripts operate on supplied JSON. Connector access, source extraction, authenticated approvals and external delivery are not implemented by these scripts. Retain the original input separately and run `python -B scripts/policy_validate_output.py output.json --input input.json` (alias `--source`). Output includes `input_hash` and `source_truth: unverified`; validation reconstructs the native result and rejects changed figures, narrative, classifications, omitted fields and extra fields. A successful check proves correspondence with the supplied input, not source truth, legal applicability or permission to distribute. Never add a raw source snapshot to an outward-facing artifact. Source and approval strings remain supplied evidence for professional review.

Mandate-specific eligible policies override firm-wide policies; equally current competing policies produce no_policy. Policy availability is limited to the review as-of, with meeting-date expiration checks. Precedent requires matching mandate_id and an explicit comparability_key; category alone is insufficient. This is literal consistency with supplied policy, not adjudication of policy conditions or vote merits.


How a human analyst's **proposed vote** is compared against the documented **voting policy**
and **analogous prior cases**, and how per-item findings roll up to a review disposition.
The proposed vote is an input to be checked; policy and precedent are the authorities. This
skill surfaces deviations with citations. It never decides, changes, casts, or submits a
vote — that is a human/voting-committee action recorded in the proxy-voting system of record.

Orientation: the firm's proxy-voting policy and stewardship standard take precedence over
any general guidance here, and over any third-party research-provider recommendation.

## Vote and position vocabulary

- **Proposed vote** and **precedent vote** ∈ `For | Against | Abstain | Withhold`.
- **Policy position** (`default_position`) ∈ `For | Against | Abstain | Withhold | Case-by-case`.

## Version / effective-date rule (policy selection)

Policy is a **versioned, effective-dated contract**. For each agenda item:

1. Consider only guidelines whose `category` matches the item.
2. Keep those whose `effective_date` **≤ `meeting_date`** (guidelines effective *after* the
   meeting are ignored — they were not in force when the vote is cast).
3. Select the **latest** remaining guideline by `effective_date` (supersession).
4. If none remain, the item is `no_policy` (a coverage gap, not an implied position).

The output records `policy_version` and cites the exact guideline chosen, so a review is
reproducible. A guideline dated after the meeting, or an as-of policy version mismatch, is
surfaced by `validate_input` as a warning.

## Item classification (deterministic)

| Status | Condition |
| ------ | --------- |
| `aligned` | A directive guideline applies and `proposed_vote == default_position`. |
| `deviation` | A directive guideline applies and `proposed_vote != default_position`. |
| `case_by_case` | The applicable guideline's position is `Case-by-case` — no mechanical match; documented rationale is required. |
| `no_policy` | No guideline is effective for the category as of the meeting date (coverage gap). |

A `case_by_case` item is **not** a deviation; it is a flag that documented rationale and
human adjudication are required. A `no_policy` item is a gap to resolve with the policy
owner, not an implied approval.

## Precedent consistency (analogous prior cases)

For each item, gather precedents with the **same category** and a **strictly earlier**
`meeting_date`. Report `concordant` (precedent vote == proposed vote) and `discordant`
counts with `precedent:{case_id}@{meeting_date}` citations. `precedent_discordant` is true
when discordant precedents outnumber concordant ones. Precedent discordance is evidence for
the reviewer; it never, on its own, decides the vote. When no analogous precedent exists,
precedent consistency is reported **not-evaluable**, not "consistent".

## Overall disposition (deterministic roll-up)

| Disposition | Rule |
| ----------- | ---- |
| `deviations_present` | Any item classified `deviation`. |
| `review_recommended` | No deviation, but ≥1 `case_by_case`, ≥1 `no_policy`, or any `precedent_discordant` item. |
| `consistent` | Every item `aligned` with policy and no precedent discordance. |

`deviation` dominates; `consistent` requires the fully clean case. The disposition is a
**triage signal for a human**, never an instruction to vote.

## Hard boundaries (fail closed)

- Never state or imply the skill has **decided, changed, cast, submitted, or finalized** a
  vote, ballot, or voting instruction. `validate_output` rejects such language.
- Never treat the `proposed_vote` as authoritative or "correct"; it is the object under
  review.
- Never provide personalized investment advice or a merits opinion on the proposal.
- Every `deviation`, `case_by_case`, and `no_policy` finding must carry a mandatory
  human-adjudication `required_action`.

## Durable identifiers

- `review_id = vpcc-{meeting_id}-{meeting_date}-NNNN` binds the review to the exact ballot,
  policy version, and precedent set; re-running with the same inputs reproduces the findings
  and disposition.
- `finding_id = {meeting_id}-F###` per agenda item.
- `packet_id` links back to the upstream evidence bundle (see references/policy-handoffs.md).
