# Source Map — policy-procedure-gap-analyzer

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Regulatory corpus / approved-source retrieval** (laws, regulations, supervisory guidance, standards) | Authoritative requirements, obligations, effective dates, versions | Read-only |
| 2 | **Controlled content library** (internal policies & procedures) | Policy/procedure controls, owners, effective/review dates, versions | Read-only |
| 3 | **Case management / records archive** | Operational evidence pointers (testing artifacts, filings, training records) | Read-only |
| 4 | Operational systems context: **KYC/AML, sanctions & PEP data, transaction monitoring** | Whether the documented procedure matches actual operations | Read-only |
| 5 | Gap-analysis **config** (versioned) | Review-cycle window, parameter comparators, severity/priority mapping | Read-only |

The **regulatory corpus is the requirement of record**; an internal policy never overrides
what the requirement says. When a policy and the requirement conflict, cite both and raise a
finding — never silently reconcile. When the documented procedure and observed operations
conflict, cite both; the reviewer adjudicates which is authoritative.

## Citation format

`{system}:{ref}@{date}` — e.g. `reg:31 CFR 1010.311 (paraphrased)@2020-01-01` for a
requirement, `policy:AML-POL-SAR#7.1@2026-02-10` for a policy/procedure control. Every
finding cites the requirement and/or the control it is drawn from. Quote regulatory text
only in short paraphrase; the corpus reference is the authority, not a reproduced passage.

## Freshness / effective dates

- Requirements carry an `effective_date` and `version`; a requirement whose `effective_date`
  is after `as_of` is **not yet in effect** and is reported as informational, not a gap.
- The output records the `config_version` (comparators, review window, mapping) so an
  analysis is reproducible.
- A control's `last_reviewed` older than `config.review_max_days` (default 365) is stale.

## Least-privilege operations (deployment)

- `regcorpus.requirements(framework, jurisdiction, as_of)` → in-effect obligations + versions.
- `policylib.controls(framework)` → policy/procedure controls, mappings, review dates.
- `records.evidence(control_id)` → evidence pointers (no document contents beyond the ref).
- `config.get('ppga', version)` → comparators, review window, severity/priority mapping.

All read-only, deterministic, durable `analysis_id`, below the fixed timeout; page long
requirement/control sets as resumable stages.
