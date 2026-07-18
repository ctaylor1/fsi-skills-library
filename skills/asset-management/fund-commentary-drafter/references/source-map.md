# Source Map — fund-commentary-drafter

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Reconciled performance** (perf book of record) | Fund/benchmark return, excess return — the headline numbers | Read-only |
| 2 | **Attribution** (attribution engine, reconciled) | Effect decomposition (allocation, selection, currency, ...) that must tie to excess | Read-only |
| 3 | **Holdings / positioning** | Over/underweights and changes | Read-only |
| 4 | **Flows** | Net subscriptions/redemptions | Read-only |
| 5 | **Market data / desk commentary** | Period market backdrop | Read-only |
| 6 | **Approved messaging library** (controlled content, versioned) | Outlook and thematic statements — the ONLY basis for opinion/forward text | Read-only |
| 7 | **Disclosures & templates** (controlled content, versioned) | Required disclosure IDs, template version | Read-only |
| 8 | **Prior commentary** | Period-over-period consistency | Read-only |

Performance and attribution are the **systems of record** for the numbers; the approved
messaging library and disclosure set are **versioned contracts**. Forward-looking or
thematic language may come only from approved messaging — never invented.

## Citation format

`{system}:{ref}@{date/version}` — e.g. `perf:GLEQ:I-Acc:Q2-2026@2026-07-05`,
`attrib:GLEQ:Q2-2026#selection`, `pos:GLEQ:Q2-2026#it`, `MSG-OUTLOOK-2026Q2`
(messaging id), `flows:GLEQ:Q2-2026@2026-07-03`. Every claim in the ledger carries at least
one such citation, or it is flagged unsupported and excluded.

## Freshness / effective dates

- Performance and attribution must be **reconciled** (`reconciled: true`) and read for the
  exact commentary period; un-reconciled numbers block drafting.
- Messaging and disclosures use **versioned/effective-dated** content; expired or
  non-`approved` messaging must not be used as a claim basis.
- Prior commentary is used only for consistency, not as a source of facts for the period.

## Least-privilege operations (deployment)

- `perf.read(fund_id, share_class, period)`, `attrib.read(fund_id, period)` — read-only.
- `holdings.read(fund_id, period)`, `flows.read(fund_id, period)` — read-only, bounded.
- `content.get('messaging'|'disclosures', version)` — read-only, versioned.
- `commentary.read(fund_id, prior_period)` — read-only.
No mutation from this skill. It produces a **draft package**; recording approvals and any
delivery are separate, human-performed actions outside this skill's tools.
