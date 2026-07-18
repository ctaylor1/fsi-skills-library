# Adjacent-Skill Handoffs — financials-normalizer

This skill produces a cited **normalized, model-ready dataset** (`normalization_id`) with
provenance and tie-outs, and stops. It does not build the downstream model, spread borrower
financials into a bank credit template, reconcile to the ledger, or judge/post anything. It
routes the human/analyst to the right next step.

## Downstream (route the human/analyst to)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `three-statement-model-builder` | The normalized data feeds a three-statement operating model | `normalization_id` + normalized accounts |
| `dcf-modeler` | The normalized data feeds a DCF | `normalization_id` + normalized accounts |
| `lbo-model-builder` | The normalized data feeds an LBO model | `normalization_id` + normalized accounts |
| `merger-model-builder` | The normalized data feeds a merger/accretion-dilution model | `normalization_id` + normalized accounts |
| `comps-analysis-builder` | Normalized figures across a peer set feed a comparable-companies analysis | `normalization_id` per entity |
| `valuation-reviewer` | A valuation built on these normalized inputs must be reviewed for correctness/control | `normalization_id` + normalized inputs |
| `management-reporting-packager` | The normalized figures are assembled into a management-reporting pack | `normalization_id` + normalized accounts |
| `audit-evidence-packager` | The normalized dataset + provenance must be indexed, redacted, and packaged for audit | `normalization_id` + cited provenance |

## Sideways / not-this-skill (route away)

| Skill | When |
| ----- | ---- |
| `financial-spreading-assistant` | The task is **borrower credit spreading** into a bank credit template (a separate workflow with credit-analysis intent) |
| `gl-reconciler` | The figures **don't tie to the ledger/subledger** — a reconciliation break, not a source-to-model normalization |
| `earnings-results-analyzer` | The user wants an **analysis of earnings quality / results**, not a standardized dataset |
| `regulatory-reporting-data-validator` | The data is destined for a **regulatory return** and needs validation against that return's rules |
| `financial-statement-audit-assistant` | The user wants **audit procedures / testing** over the statements, not normalization |
| `company-profile-builder` | The user wants a **company profile** narrative, not a normalized dataset |

## Upstream (may produce this skill's inputs)

Document-intelligence extraction and entity resolution supply the source line items and the
mapping pack; a scheduled monitor is **not** used here (this skill is interactive,
`aws-fsi-scheduled-agent: no`).

## Human / governance handoffs (no skill performs these)

- **Reviewer / preparer acceptance** — a human must accept the mapping and resolve any
  tie-out or identity break before the normalized dataset is used in a model, report, or
  system of record. This skill suggests a readiness band; it never signs off.
- **Controller / Finance & Controllership** — owns the chart-of-accounts standard, the
  normalization/adjustment policy, and any posting to a system of record.
- **Licensed specialist** — any accounting, audit, investment, or credit **opinion** on the
  entity is out of scope entirely and belongs to a qualified human.

## Duplicate-execution prevention

- This skill maps, rolls up, adjusts-with-rationale, and tie-out-checks **only**; it must not
  build the downstream model, spread borrower financials, reconcile to the ledger, judge, or
  post — those belong to the human and the downstream skills above.
- Downstream skills reuse the `normalization_id` dataset and its provenance rather than
  re-normalizing the source.
