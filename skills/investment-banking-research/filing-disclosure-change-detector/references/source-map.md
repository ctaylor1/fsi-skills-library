# Source Map — filing-disclosure-change-detector

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Filed-form retrieval** (EDGAR / regulator filing store) | The as-filed prior and current documents — the position of record | Read-only |
| 2 | **Document intelligence** | Section/item segmentation, exhibit index parsing, page/clause anchors | Read-only |
| 3 | **Entity resolution** | Issuer/CIK/ticker resolution; matching a filing to the correct issuer and prior baseline | Read-only |
| 4 | Change-detection **config** (versioned) | Risk-section prefixes, restatement/non-reliance markers, material-contract exhibit prefixes | Read-only |

The **as-filed document is authoritative.** A press release, transcript, investor deck, or
draft is *not* a substitute for the filed text. If a filed section and a non-filed source
conflict, cite the filed text and flag the discrepancy for the human reviewer — never
silently reconcile.

## Choosing the comparison baseline (version rules)

A filing is identified by `(issuer/CIK, form_type, period, filing_date, accession, amendment
number)`. The **prior** input must be the correct like-for-like baseline:

- **Annual/interim like-for-like** — compare a 10-K to the prior-year 10-K, a 10-Q to the
  immediately prior comparable 10-Q (same fiscal quarter for narrative sections; sequential
  for balance-sheet continuity — state which).
- **Amendments** — a `10-K/A` / `10-Q/A` compares to the **original** it amends (same period
  and accession family), not to the prior year. `validate_input` warns on cross-form
  comparison; confirm the baseline.
- **Section alignment** — sections are matched by a stable `section_id` (Item number or a
  normalized heading key). If items were renumbered between filings, align them before
  running or the diff will report spurious add/remove findings.

## Citation format

- Section finding: `{form}:{period}:§{section_id}@{filing_date} (acc {accession})` — e.g.
  `10-K:FY2025:§1A-02@2026-02-18 (acc 0000000000-26-000034)`.
- Exhibit finding: `{form}:{period}:EX-{exhibit_no}@{filing_date} (acc {accession})`.
- `changed_language` evidence rows cite the **version each span came from** (prior for
  removed text, current for added text), so every quoted span is traceable to one filing.

## Freshness / effective dates

- Record `config_version`; detection markers and prefixes are a **versioned contract** so a
  comparison is reproducible.
- Record each filing's `filing_date` and `accession`; the output pins both versions compared.
- The `current` filing must not predate the `prior` baseline (`validate_input` fails closed
  on inverted ordering).

## Durable identifiers

- `job_id` — the durable comparison-job id (`fdcd-…`); supply it or it is derived
  deterministically from issuer + both filing dates. Re-running the same two versions with
  the same config reproduces the same `finding_id`s.
- `finding_id` — `{job_id}-{NNN}`; stable across re-runs for downstream reference.

## Least-privilege operations (deployment)

- `filings.get(cik, form_type, period|accession)` → the as-filed document.
- `docintel.segment(document)` → sections keyed by Item/heading; exhibit index rows.
- `entity.resolve(issuer|cik|ticker)` → canonical issuer + prior-baseline candidates.
- `config.get('fdcd', version)` → markers, prefixes, thresholds.

All read-only, deterministic, durable `job_id`, below the fixed timeout; page long filings
into resumable per-section stages. No writes, no publication, no external delivery.
