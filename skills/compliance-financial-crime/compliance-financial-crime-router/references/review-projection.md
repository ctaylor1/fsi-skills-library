# Two explicit review projections

The `compliance-review-projection/1.0` method supports exactly two offline pairs:
transaction-monitoring-scenario-designer → transaction-monitoring-effectiveness-reviewer,
and financial-crime-case-investigator → financial-crime-case-quality-reviewer.
Use scripts/project_review.py with separately retained producer input/packet, receiver
input, field mappings, scoped projection-basis claim and named supplemental records.
The command revalidates both actual installed native packages. `--verify` reconstructs
against those detached inputs; duplicate JSON keys and non-finite values are rejected.

The producer and receiver retain the same subject ID, institution, legal entity,
represented party, jurisdiction, business line, assessment date, knowledge cutoff,
classification, audience, permitted audiences, source versions and full producer
fact registry. All producer open issues survive. Capacity, purpose, responsibility
role and native object type may change only through an exact source-bound review
assertion. Every receiver field has an exact JSON pointer mapping and supplied mapping
reviewer/basis; the subject maps directly from the producer original.

A review ID alone is insufficient. Monitoring transfers retain sourced underlying
scenario/design version, engine/version, population/unit, identifier namespace,
mapping dataset/ref/version and graph/ref/version. Receiver observation and benchmark
scenario/engine IDs must agree. Scenario aggregation windows and evaluation periods
are different concepts; receiver evaluation dates and separate observed labels remain
explicit receiver evidence. No design claim becomes an observed engine outcome.

Investigation-to-QA is limited to one case. Population, selection, native case and all
QA evidence rows identify the producer case; the upstream native version identifies
the retained producer original by its canonical hash. Batch QA, another case, later
assessment, a different audience or a new jurisdiction requires a separately reviewed
adapter; it is not supported by this method. SAR drafting/filing and adjacent architecture,
data, privacy, model or AI schemas are not automatic projection targets.

Use `expected_basis` to obtain the exact assertion value. The review claim has exactly
`value`, `source_refs`, `fact_ids`, supported by a dated, accessible receiver source
record. Its value records the pair, original input/output hashes, both contexts and
roles, assessment/cutoff and native subject link. It cannot confer appointment,
independence, disclosure permission or operational authority. It does not authenticate
the reviewer or sources, or prove that receiver reasoning substantively follows from
the evidence. Human semantic review remains required; the output explicitly records
`source_truth=unverified`, `authority_granted=false`, `execution=not_performed` and
`semantic_evidence_sufficiency=human-review-required`.
