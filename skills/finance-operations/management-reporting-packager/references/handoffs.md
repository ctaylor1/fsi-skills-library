# Adjacent-Skill Handoffs — management-reporting-packager

Packaging is a **separate control activity** from the analysis it presents, from close
certification, and from delivery. This skill consumes cited, approved inputs and assembles a
DRAFT pack; it does not recompute the analysis or perform delivery.

## Upstream (feeds this skill)

| Upstream skill | Provides | Handoff artifact |
| -------------- | -------- | ---------------- |
| `fpa-variance-analyzer` | Driver-level variance explanations and management commentary | Cited variance commentary → KPI `commentary_source_ref` |
| `gl-reconciler` | Subledger-to-GL reconciliations, break classification, lineage | Tie-out results + citations → reconciliation section |
| `financials-normalizer` | Inconsistent statements standardized to model-ready data | Normalized figures + provenance → KPI values |
| `regulatory-reporting-data-validator` | Validated regulatory-report inputs and controls | Validated metrics + sign-off evidence → KPI/exception rows |

This skill packages the **cited results** of the above; it never re-derives a variance,
re-runs a reconciliation, or re-validates a regulatory metric. If commentary or a tie-out is
missing or uncited, route back to the relevant upstream skill rather than inventing it.

## Downstream / adjacent (this skill routes to)

| Skill / actor | When | Handoff artifact |
| ------------- | ---- | ---------------- |
| `month-end-close-orchestrator` | The request is to certify the close and post sign-offs/journals (a gated write) | `package_id` + assembled draft |
| `audit-evidence-packager` | The request is an audit evidence bundle with chain of custody, not a management report | Requested evidence list |
| `financial-statement-audit-assistant` | External financial-statement audit support (tie-outs, sampling) is wanted | Draft pack + source lineage |
| `valuation-reviewer` | A KPI depends on a fair-value/mark question needing review | Instrument/position reference |
| **Human / operations (no skill)** | External delivery to the board/committee/regulator, or posting to a system of record | Approved final pack (human-owned) |

**Delivery is deliberately not a skill.** There is no distribution skill in the catalog:
sending, submitting, filing, or posting the pack is a human/operations action that occurs
after the named approvals — this skill stops at a draft.

## Duplicate-execution prevention

- This skill **does not** compute variances, run reconciliations, form an audit opinion,
  certify the close, or deliver the pack — each belongs to the skill/actor above.
- Downstream consumers use the `package_id` and its cited lineage rather than re-assembling.
- A blocked package is returned to the relevant upstream skill or the human preparer to
  resolve the gap; it is never force-marked `ready-for-review` here.
