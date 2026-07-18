<!--
Approved management-report package template for management-reporting-packager.
Every section header below is REQUIRED and is enforced by scripts/validate_output.py
(the section titles must match exactly). Fill each bracketed field from CITED, approved
sources only — never assert a figure or a claim that is not backed by a source_ref.
This is a DRAFT for human review; it is never delivered, submitted, or posted by the skill.
-->

# Management Report Package — DRAFT

- **Package ID:** [MRP-<entity>-<period>]
- **Entity / scope:** [entity]
- **Reporting period:** [period]
- **Config / policy version:** [config_version]
- **Package status:** [ready-for-review | blocked]
- **Delivery status:** draft (never sent/submitted/posted by this skill)

## Cover & reporting scope
State the entity, consolidation scope, period, currency, basis of preparation, and the
close/data cut-off used. Note any entities or segments excluded and why. List the source
systems the pack draws on (ERP/GL, subledgers, consolidation, FP&A, regulatory reporting).

## Executive takeaways
3–6 bullet takeaways. Each takeaway must be traceable to a KPI or exception below and must
carry a citation. State facts and cited variances only — no forward-looking guarantees, no
investment advice, no "board-approved"/"final" language. Flag anything uncertain explicitly.

## KPI scorecard & commentary
| KPI | Value | Unit | vs Budget | vs Prior | Commentary (cited) | Support | Citation |
| --- | ----- | ---- | --------- | -------- | ------------------ | ------- | -------- |
| [name] | [value] | [unit] | [Δ / %] | [Δ / %] | [driver commentary] | supported | [source_ref(s)] |

Every row needs a `source_ref` for the figure and a `commentary_source_ref` for the
narrative. A row lacking either is `unsupported` and BLOCKS the package.

## Reconciliation & tie-out summary
| Reconciliation | Ledger | Subledger | Difference | Tolerance | Tie-out | Citation |
| -------------- | ------ | --------- | ---------- | --------- | ------- | -------- |
| [name] | [ledger_balance] | [subledger_balance] | [difference] | [tolerance] | tie / break | [recon source_ref] |

Any `break` (difference beyond tolerance) BLOCKS the package. Do not net, override, or
explain away a break — route it to `gl-reconciler` and record it here as unresolved.

## Source lineage & citations
List every source underpinning the pack: system, reference, and effective date/version, in
the format `{system}:{ref}@{date/version}`. Each KPI, commentary line, reconciliation, and
exception must map to at least one entry here.

## Exceptions & data gaps
| ID | Description | Severity | Citation |
| -- | ----------- | -------- | -------- |
| [id] | [description] | [low/medium/high] | [source_ref] |

Include unresolved reconciliation breaks, unsupported KPIs, missing baselines, and any data
not yet available. If a required input is missing, say so here — do not infer it.

## Approvals & sign-off log
| Role | Approver | Status | Citation |
| ---- | -------- | ------ | -------- |
| preparer | [name/id] | recorded | [source_ref] |
| reviewer | [name/id] | recorded | [source_ref] |
| delivery | (human/operations) | pending | — |

`preparer` and `reviewer` must be recorded before `ready-for-review`. `delivery` approval is
a **human/operations** action and stays **pending** — this skill never obtains it.

## Standing note & distribution control
> DRAFT management report package for human review only. No pack has been delivered,
> submitted, distributed, or posted to a system of record, and no figure has been approved
> as final. External delivery and any posting require the named human approvals above.
