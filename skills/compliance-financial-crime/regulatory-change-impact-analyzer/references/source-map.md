# Source Map — regulatory-change-impact-analyzer

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Authoritative regulatory corpus** (approved-source retrieval) | Instrument text, citation, authority level, jurisdiction, publication & effective dates | Read-only |
| 2 | **Firm profile** (entity resolution / governance registry) | Business lines and jurisdictions the firm operates in (applicability inputs) | Read-only |
| 3 | **Policy / control / system / data / training inventory** (controlled registers) | Mapping each obligation to owning policies, controls, systems, data elements, training, and owners | Read-only |
| 4 | **Obligations taxonomy & change register** (controlled content library) | Obligation typing, prior dispositions, issue/owner tracking | Read-only |
| 5 | **Change-management config** (versioned) | Lead-time windows and mapping-completeness rules | Read-only |

The **primary regulatory text is the position of record** for authority, citation, and
effective date. Never substitute a summary, a secondary tracker, or a vendor alert for the
primary source; if a secondary source and the primary text conflict, cite both and flag for
the human analyst. A conflicting requirement across instruments/jurisdictions is **surfaced,
never resolved silently** (route to legal/compliance).

## Citation format

`reg:{source_ref}@{effective_date}` — e.g.
`reg:reg-corpus:cfpb;doc=1033-amend-2026;sec=1033.201@2026-08-10`. Every raised finding
cites the specific obligation/instrument evidence row and the effective date used.

## Freshness / effective dates

- **Effective date and authority level drive urgency and precedence** — capture publication,
  comment-close, and effective dates exactly; record retroactive or already-effective
  instruments as findings (`overdue_or_retroactive`).
- Config (lead-time windows, mapping rules) is a **versioned contract**; the output records
  the config version so an assessment is reproducible.
- Re-run when the instrument text, effective date, firm profile, or inventory changes; the
  `assessment_id` binds the output to those inputs.

## Least-privilege operations (deployment)

- `regcorpus.get(instrument_id)` → instrument metadata + obligation text (read-only).
- `firm.profile()` → business lines + jurisdictions.
- `inventory.mappings(obligation_ids[])` → policy/control/system/data/training/owner rows.
- `config.get('rcia', version)` → lead-time windows + mapping-completeness rules.
All read-only, deterministic, durable `assessment_id`, below the fixed timeout; page a large
obligation set as resumable stages. No write, filing, or attestation operation is bound.
