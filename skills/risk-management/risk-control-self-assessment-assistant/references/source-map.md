# Source Map — risk-control-self-assessment-assistant

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **GRC / risk register** (system of record) | Risk statements, taxonomy, control library, prior RCSA, appetite | Read-only |
| 2 | **ERM policy & RCSA standard** (controlled content) | Rating scales, methodology, appetite thresholds (versioned) | Read-only |
| 3 | **Control testing / assurance results** | Design & operating effectiveness evidence | Read-only |
| 4 | **Loss / operational-risk events** | Corroborating/contradicting evidence for control effectiveness | Read-only |
| 5 | **Key risk indicators (KRIs) & limits** | Quantitative effectiveness signals, breaches | Read-only |
| 6 | **Third-party / vendor inventory** | Coverage of outsourced processes and their controls | Read-only |
| 7 | **Finance & operational data** | Volumes, exposure, materiality for impact anchoring | Read-only |

The GRC register is the **system of record** for risk/control state and for the final RCSA.
This skill reads from it and drafts into the template; it never writes back. Methodology and
appetite are **versioned contracts** — record the version on every package.

## Citation format

`{system}:{ref}@{date/version}` — e.g. `grc:risk=R-002@2026-07-15`,
`assurance:test=CT-2026-Q2-021@2026-06-25`, `loss:event=LE-2026-031@2026-05-03`,
`policy:rcsa-standard@v2026.07`. Every credited control conclusion cites at least one
evidence source; the evidence map lists them.

## Freshness / effective dates

- Risk/control state and prior RCSA read fresh from the GRC register (avoid drafting over a
  newer assessment).
- Effectiveness evidence must fall within (or be justified relative to) the assessment
  period; stale evidence is flagged as a challenge, not silently credited.
- Scoring methodology and appetite use the **versioned** standard; the version is recorded on
  every package for reproducibility.

## Least-privilege operations (deployment)

- `grc.read(entity|risk_id)`, `grc.controls(risk_id)`, `grc.prior_rcsa(entity)` — read-only.
- `assurance.tests(control_id, period)`, `loss.events(entity, period)`,
  `kri.read(entity, period)` — read-only, bounded to the assessment scope.
- `policy.get('rcsa-standard'|'risk-appetite', version)`, `tpr.inventory(entity)` — read-only.

No mutation from this skill. Finalizing an RCSA (sign-off, attestation, GRC write) is a
**human** action performed via the GRC platform under the approval broker — never by this
skill. The bundled `scripts/` are self-contained and operate on de-identified fixtures under
`evals/files/`; they open no network connections.
