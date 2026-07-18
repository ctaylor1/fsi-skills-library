# Source Map — next-best-action-assistant

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Approved action catalog** + eligibility rules (versioned) | The ONLY actions that may be recommended; eligibility, consent, disclosure, and specialist-routing metadata | Read-only |
| 2 | **Approved knowledge** base | Citations for education/service actions; procedures; current service status | Read-only |
| 3 | **Product terms** / rate & fee schedules (effective-dated) | Citations for product-related actions; disclosure text | Read-only |
| 4 | **CRM** | Customer profile, products held, tenure, segment, consent flags, do-not-contact, vulnerability flag | Read-only |
| 5 | **Contact-center transcripts** | Intent and context signals from the interaction | Read-only |
| 6 | **Case management** | Open cases/tasks; interaction history | Read-only |
| 7 | **Complaint system** | Open-complaint status (routes to complaint handling instead of an offer) | Read-only |

The action catalog, knowledge, and product terms are **versioned contracts**. The catalog is
the allow-list: an action absent from it can never be recommended.

## Citation format

`{system}:{ref}@{date|version}` — e.g. `crm:cust=****4821@2026-07-16`,
`transcript:call=CT-8890@2026-07-16`, `kb:overdraft-protection@v2026.05`,
`terms:dda-fee-schedule@2026-06-01`, `config:nba-catalog@nba-2026.07`.

## Freshness / effective dates

- CRM consent, do-not-contact, and vulnerability flags must be read **fresh** for every
  package; a stale consent read can gate or wrongly permit an outbound action.
- Product terms and rate/fee schedules are effective-dated; cite the effective version.
- The action catalog and eligibility rules carry `config_version`, recorded on every package.

## Least-privilege operations (deployment)

- `catalog.get('nba-catalog', version)`, `rules.get('nba-eligibility', version)` — read-only.
- `crm.profile(customer_id)`, `crm.consent(customer_id)` — read-only, bounded fields only.
- `kb.read(article_id, version)`, `terms.read(doc_id, effective_date)` — read-only.
- `transcript.read(interaction_id)`, `case.read(case_id)`, `complaints.status(customer_id)` — read-only.
- No mutation from this skill. It produces a **draft package** only; external delivery and any
  system-of-record change happen elsewhere, after human approval, via the approval broker.
