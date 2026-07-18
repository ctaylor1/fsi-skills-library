# Source Map — third-party-ai-due-diligence-assistant

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **AI governance policy & due-diligence rubric** (versioned) | Required domains per criticality, evidence types, freshness windows, risk-flag rubric, hard gates | Read-only |
| 2 | **Model registry** | The registered model/agent record, criticality/materiality tier, intended use, version | Read-only |
| 3 | **Data catalog** | Data classification, residency, lineage, retention for data shared with the provider | Read-only |
| 4 | **Evaluation harness** | Model evaluation, bias/fairness, red-team, and benchmark results (evidence, not authored here) | Read-only |
| 5 | **Agent / tool logs** | Declared tool scope and observed calls for an external agent under assessment | Read-only |
| 6 | **Provider evidence room** (questionnaire responses, SOC 2/ISO, model/system cards, DPAs, contracts) | The submitted due-diligence artifacts | Read-only |
| 7 | **Risk & issue systems** | Existing findings, open issues, prior assessments, concentration data | Read-only |
| 8 | **Controlled template & content library** | Approved due-diligence package template and standing disclaimer | Read-only |

The due-diligence rubric (required domains, evidence types, freshness windows, risk-flag
points, hard gates) is a **versioned contract** (`rubric_version`). Never hard-code a domain,
threshold, or gate that contradicts the current governance policy; record the version on
every package.

## Citation format

`{system}:{ref}@{date/version}` — e.g. `rubric:tpaidd-2026.07`,
`registry:model=M-1042@v4`, `evidence:EV-6:soc2-type2-2025@2026-01-20`,
`datacatalog:dataset=cust-notes;residency=EU@2026-04`, `risk:issue=ISS-88@open`.

## Freshness / effective dates

- Evidence freshness is judged per domain against the rubric's `max_age_days` (e.g., SOC 2 /
  security certifications within 365 days; model evaluations within 180 days). A required
  domain whose freshest evidence is out of window is flagged `stale-evidence` — not packaged.
- Contractual clauses (`max_age_days: None`) do not expire but must reflect the executed
  agreement version.
- Compute against a stated `as_of_date`; if none is supplied the system date is used and the
  package must say so.

## Least-privilege operations (deployment)

- `rubric.get('tpaidd', version)` → required domains, evidence types, windows, risk-flag and
  hard-gate rubric — read-only.
- `registry.get_model(model_id)` / `datacatalog.get(dataset_id)` — read-only.
- `evalharness.get_results(model_id, version)` — read-only (results are evidence, not authored
  here; benchmark *construction* is `ai-evaluation-benchmark-builder`).
- `agentlogs.get_scope(agent_id)` — read-only (scope *review* is `agent-permission-scope-reviewer`).
- `templates.get('tpaidd-package', version)` — read-only controlled content.
No mutation from this skill. Recording an onboarding decision, accepting risk, or updating an
inventory record is **out of scope** — performed by an authorized human / the routed skill
after review.
