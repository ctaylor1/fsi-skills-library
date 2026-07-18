# Source Map — financial-spreading-assistant

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | Borrower **financial statements** (audited/reviewed/prepared) | Position of record for spread line items and reported subtotals | Read-only |
| 2 | Borrower **tax returns** (business/personal, as applicable) | Alternate/attest basis; cross-check to statements | Read-only |
| 3 | **Document intelligence / OCR** | Extract line labels, amounts, and page citations from the documents | Read-only |
| 4 | Approved **template & classification map** (versioned) | Which raw label maps to which standard taxonomy line | Read-only |
| 5 | Spreading **config** (versioned) | Ratio definitions, tolerance, add-back policy | Read-only |
| 6 | **Loan origination** context | Borrower identity, obligor/period scoping | Read-only |

The prepared statements are authoritative for what the borrower reported. A tax return is a
separate basis — when it disagrees with the statement, **cite both and flag**; never silently
blend the two. The classification map and ratio formulas are versioned contracts, not per-deal
judgments.

## Classification & provenance (required)

Every spread line resolves to exactly one outcome:

- **classified** — the proposed `code` is a valid taxonomy code, or the `raw_label` resolves via
  the versioned classification map. The line's amount enters the subtotal; its `source_ref` is
  retained.
- **ambiguous** — no valid code and no map hit. The line is routed to `ambiguous_mappings` with
  its citation and `requires_human_mapping` is set. It is **not** bucketed or guessed.

Every analyst **adjustment** (add-back) carries a `provenance` and a `citation`; the normalized
view differs from as-reported only by the documented adjustments.
`scripts/validate_output.py` fails closed on a missing provenance/citation or a phantom add-back.

## Citation format

`{system}:{ref}` — e.g. `doc:acme-fs-2025.pdf#p3` for a statement line, or
`doc:acme-notes-2025.pdf#p2` for the note supporting an add-back. Every classified line and every
adjustment cites the document and page it came from.

## Freshness / reproducibility

- The template, classification map, and config are **versioned contracts**; the output records
  `template_version`, `classification_map_version`, and `config_version` so a spread is
  reproducible.
- `spread_id` binds the output to the inputs + the three versions. Re-running the same inputs and
  versions reproduces every subtotal, ratio, tie-out, and normalized figure.

## Least-privilege operations (deployment)

- `docintel.extract(document)` → line labels, amounts, and page citations.
- `template.get('spread', version)` → the approved template lines and subtotal structure.
- `classmap.get(version)` → raw-label → taxonomy-code mappings.
- `config.get('spreading', version)` → ratio definitions, tolerance, add-back policy.
- `origination.context(borrower_id)` → obligor identity and period scoping.

All read-only, deterministic, durable `spread_id`, below the fixed timeout; page long documents
as resumable stages. No write path exists in this skill.
