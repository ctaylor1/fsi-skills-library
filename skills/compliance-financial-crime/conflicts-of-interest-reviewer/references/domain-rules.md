# Domain Rules — conflicts-of-interest-reviewer

Explainable conflict **indicators**, the **required-control** check, and the **deterministic
residual-risk** mapping. Thresholds and per-type requirements are configuration (versioned,
owned by Compliance), never hard-coded judgments and never tuned to an individual. The firm's
conflicts-of-interest policy, code of ethics, and applicable regulation (e.g. SEC/FINRA
rules on outside business activities, private securities transactions, gifts and gratuities,
personal trading, and information barriers) take precedence over these defaults.

## Conflict taxonomy

| `conflict_type` | Covers | Base inherent severity |
| --------------- | ------ | ---------------------- |
| `personal_financial_interest` | Ownership/economic interest in a counterparty or outcome | Medium (High if material) |
| `outside_business_activity` | Outside directorship, board seat, employment, business | Medium (High if material) |
| `gift_entertainment` | Gifts / entertainment given or received | Low (Medium/High by value) |
| `personal_relationship` | Family or close personal relationship with a counterparty/supervisor/client | Medium |
| `personal_trading` | Trading in a security connected to a matter | High if `mnpi_access`, else Medium |
| `dual_role` | Acting on both sides / advising competing clients | High |
| `related_party_transaction` | Transaction with a related entity/person | High |
| `incentive_misalignment` | Compensation/incentive that could bias advice | Medium (High if material) |
| `information_barrier` | MNPI access / wall-crossing | High |

## Inherent severity (deterministic)

Ordinal scale `Low=1, Medium=2, High=3`. From the base above, apply the magnitude escalation:

- `gift_entertainment`: `gift_value >= 5 × gift_deminimis` → High; `>= gift_deminimis` → at
  least Medium; below `gift_deminimis` → **not fired** (informational only).
- `personal_financial_interest` / `outside_business_activity` / `incentive_misalignment`:
  material (`ownership_pct >= ownership_material_pct` **or** `annual_value >=
  annual_value_material`) → High; otherwise base Medium.
- `personal_trading`: `mnpi_access` true → High; otherwise Medium.
- All other types use their base severity.

An item **fires** as a manageable conflict unless it is an explicitly de-minimis gift. This is
deliberately conservative (fail toward flagging) — a false positive is reviewed and dismissed
by a human; a false negative is an unmanaged conflict.

## Required-control check (per type, from config)

For each fired indicator, compare the recorded `disclosures[]`, `controls[]`, and `approvals[]`
against the configured requirement set for that `conflict_type`:

| `conflict_type` | Required disclosure to | Required control | Required approval |
| --------------- | ---------------------- | ---------------- | ----------------- |
| `personal_financial_interest` | compliance | recusal | compliance |
| `outside_business_activity` | compliance | recusal | supervisor + compliance |
| `gift_entertainment` | compliance | — | supervisor |
| `personal_relationship` | supervisor | reassignment | supervisor |
| `personal_trading` | compliance | preclearance + restricted_list | compliance |
| `dual_role` | clients + compliance | information_barrier + separate_teams | compliance |
| `related_party_transaction` | compliance + board | independent_review | board |
| `incentive_misalignment` | clients | supervisory_review | compliance |
| `information_barrier` | compliance | wall_cross_log + restricted_list | compliance |

- **disclosure_status**: `complete` if every required recipient is covered by a disclosure
  that is not older than `disclosure_staleness_days`; `stale` if covered but expired;
  `missing` otherwise.
- **control_status**: `complete` if every required control is present with `status: active`;
  `partial` if some present; `missing` if none.
- **approval_status**: `complete` if every required approver is present; `missing` otherwise.
- An **open gap** exists when any of the three is not `complete`.

## Residual-risk mapping (deterministic)

Per fired indicator:

- If **no open gap** (all required disclosure + control + approval present and current):
  `residual = max(Low, inherent − 1)` (one band of mitigation credit).
- If **any open gap**: `residual = inherent` (no mitigation credit) and `open_gap = true`.

**Matter residual** = the maximum residual band across fired indicators (Low if none fired).

## Recommended review path (deterministic — a recommendation, not a decision)

Let `has_gap` = any fired indicator has an open gap.

| Recommended path | Rule |
| ---------------- | ---- |
| Escalate to the conflicts/ethics committee (or designated compliance officer) for adjudication | matter residual = High, **or** `has_gap` |
| Route to a compliance officer for review and disposition | matter residual = Medium |
| Supervisor attestation and retention in the conflicts register | matter residual = Low and no gap |

This is a triage **recommendation for the human adjudicator**. It is never a clearance,
waiver, approval, closure, or filing.

## Hard boundaries (fail closed)

- Never **clear, approve, or waive** a conflict, or state that a matter **is cleared /
  approved / waived**.
- Never **close** the matter or say "no further action required" / "final disposition".
- Never **file or submit** a disclosure, U4/U5, attestation, or regulatory form.
- Never assert **insider dealing, MNPI misuse, or intent** — describe facts and route to
  surveillance.
- Never state a binding **"there is no conflict"** determination — report that no indicator
  fired and leave the determination to the adjudicator.
- Never tune thresholds to the individual; use only the versioned config.

## Mitigation prompts (include when any indicator fires or a gap exists)

Recusal from the affected matter, reassignment of coverage, an information barrier / wall-cross
log, restricted-list addition, a refreshed or missing disclosure, independent/second-level
review, divestment or holding limits, and enhanced supervisory review. The pack presents these
as **options for the adjudicator**, never as directives or completed actions.
