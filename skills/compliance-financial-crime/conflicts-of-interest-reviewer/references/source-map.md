# Source Map — conflicts-of-interest-reviewer

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Case management** — the disclosure of record | What was disclosed, to whom, when; recorded controls and approvals | Read-only |
| 2 | **Regulatory corpus / conflicts policy + code of ethics** (versioned) | Required disclosures, controls, and approvals per conflict type; de-minimis and materiality thresholds | Read-only |
| 3 | **KYC/AML + entity resolution** | Resolve subject, counterparties, beneficial owners, related parties | Read-only |
| 4 | **Sanctions / PEP + adverse-media reference** | Enrich counterparty risk context (not adjudication) | Read-only |
| 5 | **Records archive** | Prior disclosures, prior reviews, register history | Read-only |
| 6 | Conflicts-policy **config** (versioned) | Thresholds + per-type requirement sets | Read-only |

Never substitute a subject's assertion for the disclosure record. If the disclosure record and
an email/CRM note conflict, cite both and flag for the adjudicator; do not resolve silently.

## Citation format

`{system}:{ref}@{date}` — e.g. `coi:matter=COI-2026-0148;item=I-2@2026-07-15`. Every fired
finding cites the specific disclosure/control/approval rows and the config version behind the
required-control check.

## Freshness / effective dates

- The policy config (thresholds, per-type requirements) is a **versioned contract**; the
  output records the `config_version` used so a review is reproducible.
- Disclosures older than `disclosure_staleness_days` (default 365) are treated as **stale** and
  count as an open gap until refreshed.
- Record the `as_of` date; residual risk and gaps are evaluated as of that date.

## Least-privilege operations (deployment)

- `cases.get(matter_id)` → the disclosure record, recorded controls, approvals (masked PII).
- `policy.requirements('conflicts', version)` → per-type disclosure/control/approval sets.
- `entity.resolve(subject|counterparty)` → normalized identities, related-party links.
- `refdata.risk(counterparty)` → sanctions/PEP/adverse-media flags (context only).
- `config.get('conflicts', version)` → thresholds + requirement sets.

All read-only, deterministic, with a durable `review_id`, below the fixed timeout; page long
matter histories as resumable stages. This skill performs **no writes** and stages nothing for
execution — the adjudication, waiver, closure, and any filing are separate, human-authorized
operations owned by the case-management and approval-broker services.
