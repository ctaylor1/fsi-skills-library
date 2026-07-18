# Source Map — claims-fraud-referral-assistant

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Claims administration** (claim system of record) | Claim state, FNOL, loss/report dates, adjuster notes, `claim_id` | Read-only |
| 2 | **Policy administration** | Policy inception, coverage changes, lapse/reinstatement, limits | Read-only |
| 3 | **Underwriting rules / reference data** | Peril classification, reportable-loss rules, thresholds | Read-only |
| 4 | **Document intelligence** | Loss reports, police/fire reports, estimates, statements (field/version citation) | Read-only |
| 5 | **Producer / third-party systems** | Prior-claims history, prior SIU referral flag, party resolution | Read-only |
| 6 | **Actuarial / catastrophe data** | Event context for post-event loss patterns (enrichment only) | Read-only |
| 7 | Approved **fraud-indicator config** (versioned weights/thresholds) | Deterministic scoring | Read-only |

Claims administration is the system of record for claim state; policy administration for
coverage facts. The indicator config is a **versioned contract** — its version is recorded on
every referral for reproducibility and review.

## Citation format

`{system}:{ref}@{date/version}` — e.g. `claimsys:claim=CLM-3001@2026-07-10`,
`poladmin:policy=POL-7712;inception=2026-05-15`, `config:claims-fraud@v2026.06`.

## Freshness / effective dates

- Claim and policy state must be read fresh (avoid drafting a referral off a superseded FNOL
  or a coverage position that has since changed).
- Indicator weights/thresholds use a **versioned** config; the version is stamped on every
  referral record so the score is reproducible and reviewable.

## Least-privilege operations (deployment)

- `claims.read(claim_id)`, `claims.notes(claim_id)` — read-only.
- `policy.read(policy_ref)` → inception, coverage changes, lapse/reinstatement — read-only.
- `refdata.get(peril)` → reportable-loss classification — read-only.
- `docintel.read(claim_id)` → loss/police reports, estimates — read-only, cited.
- `history.read(insured_id)` → prior claims count, prior SIU flag — read-only.
- `config.get('claims-fraud-indicators', version)` — read-only.

No mutation from this skill. The referral is a **draft artifact**; routing to SIU is a
*proposed* handoff recorded via the approval broker, never an autonomous case action.
