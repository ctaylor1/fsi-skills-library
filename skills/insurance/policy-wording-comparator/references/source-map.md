# Source Map — policy-wording-comparator

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Filed / approved forms** repository (position of record) | Baseline form + its `filing_status` and edition | Read-only |
| 2 | **Policy-form & endorsement** repository | Subject form / manuscript / new edition under review | Read-only |
| 3 | **Document-intelligence** (clause parsing) | Clause boundaries, headings, defined terms, cross-references | Read-only |
| 4 | **Product-rules & materiality config** (versioned) | Escalation clause types, text-change threshold, required clause types | Read-only |
| 5 | **Legal / compliance references** | Orientation only; a licensed human adjudicates | Read-only |

Never substitute a drafter's change summary for the actual clause text. If a summary and the clause
text conflict, cite the clause `source_ref` and flag the discrepancy for the reviewer.

## Citation format

`{form}:{clause_id}@{source_ref}` on **both** sides — e.g.
`baseline:C-EXC-2@form=CGL-0001;ed=2024-04;cl=C-EXC-2` and
`subject:C-EXC-3@form=CGL-MS-77;ed=2026-07;cl=C-EXC-3`. Every material finding cites the specific
clause it came from on each side that exists (added findings cite the subject side; removed findings
cite the baseline side; modified findings cite both).

## Freshness / effective dates

- The materiality **config** (escalation types, text-change threshold, required clause types) is a
  **versioned contract**; the output records the `config_version` used so a comparison is reproducible.
- Record each form's `filing_status` and `edition_date`; a comparison against a non-`filed`/`approved`
  baseline is **not** a filed-form deviation check and must be labeled as such.
- Alignment is by stable `clause_id`. If forms renumber clauses between editions, the id mapping is a
  documented input, not a guess.

## Least-privilege operations (deployment)

- `forms.get(form_id, edition)` → the clause set + `filing_status` for a form of record.
- `docintel.parse(form_id)` → clause boundaries, headings, `defines[]`, `references[]`.
- `config.get('wording-materiality', version)` → escalation types, threshold, required clause types.
All read-only, deterministic, durable `comparison_id`, below the fixed timeout; page long forms as
resumable stages. No write, filing, or approval operation is ever bound to this skill.
