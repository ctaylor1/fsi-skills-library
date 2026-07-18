# Source Map — reinsurance-treaty-interpreter

Every statement and figure in the interpretation must cite one of the sources below, ranked.
See the shared platform services in [`docs/SHARED-SERVICES.md`](../../../../docs/SHARED-SERVICES.md).

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | Reinsurance-contract **system of record / treaty register** | Placed treaty, endorsements, layer terms (attachment, limit, reinstatements), effective dates | Read-only |
| 2 | The **executed treaty wording / slip / cover note** for the period (document-intelligence) | Clause-by-clause wording, article/line/clause citations | Read-only |
| 3 | **Claims & policy-administration** (loss bordereaux, cessions) | Occurrence and gross-loss figures for the recovery illustration | Read-only |
| 4 | **Actuarial / catastrophe data** | Exposure and event context only (background, never a treaty term) | Read-only |
| 5 | User-provided copy of the treaty/slip | Only when 1–4 unavailable; label as unverified | Read-only |

Never let a user assertion override the treaty of record. If the slip and the treaty register
conflict, or the wording and an endorsement conflict, present both with citations and stop for
human review — do not silently pick one.

## Citation format

Each clause and figure carries a citation of the form `{system}:{ref}@{as_of}` — e.g.
`treaty:TRTY-9001;art=III;cl=1@2026-01-01` (register), `slip:p2;line=Attachment@2026-01-01`
(document), or `bordereau:occ=O-2;row=14@2026-08-01` (loss data). The machine-readable output
stores a citation per clause and per illustrated occurrence; the narrative references them
inline where a term or figure is stated.

## Freshness / effective dates

- Interpret the treaty **as placed** for the stated underwriting year; state the inception and
  expiry dates verbatim and the underwriting year in force.
- A treaty can be endorsed mid-term (e.g. a limit or reinstatement change); interpret the
  version in force for the period and flag any endorsement that is referenced but not provided.
- Occurrence/loss figures used in the illustration carry their own bordereau/cession as-of date;
  cite them separately from the treaty wording and label the recovery **illustrative**.

## Least-privilege operations (deployment)

- `treaty.read(treaty_id)` → placed treaty, layer terms, endorsements, effective dates.
- `document.extract(treaty_doc_id)` → clause text with page/article/line citations.
- `claims.read_bordereau(treaty_id, period)` → occurrence and gross-loss rows (masked).
All read-only, deterministic schemas, durable `interpretation_id`, below the fixed timeout.
