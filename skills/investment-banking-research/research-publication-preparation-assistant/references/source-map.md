# Source Map — research-publication-preparation-assistant

## Source hierarchy (highest first)
| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | Research note draft | Rating, target, prior values, disclosures present | Read-only |
| 2 | Disclosure config (versioned) | Required disclosures | Read-only |
| 3 | Restricted list (versioned) | Restricted tickers | Read-only |
| 4 | Pre-publication checklist config (versioned) | Required review items, rating scale | Read-only |

The note is the draft; compliance configs are the authority. The assistant checks and records
config versions; it never edits the note or the configs.

## Citation format
`{system}:{ref}@{version}` — e.g. `note:note=RN-88;field=target_price`,
`config:disclosures@v2026.05`, `config:restricted_list@2026-07-18`. Every gap/flag cites its
source.

## Freshness / effective dates
- Disclosure/restricted-list/checklist configs are **versioned contracts**; the output records the
  versions and the restricted-list as-of.

## Least-privilege operations (deployment)
- `note.read(note_id)` → draft fields — read-only, bounded.
- `config.get('disclosures'|'checklist', version)` and `restricted.read(as_of)` — read-only.
Durable `prep_id`; below the fixed timeout; no mutation; no publication.
