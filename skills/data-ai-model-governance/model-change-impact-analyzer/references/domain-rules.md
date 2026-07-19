# Domain Rules — model-change-impact-analyzer

Explainable change-impact **findings** and how they map to an **impact band**, a
**recommended revalidation scope**, and a **governance path**. Thresholds are configuration
(versioned, owned by Model Risk Governance), not hard-coded judgments, and are never tuned to
a desired outcome. Orientation references: the firm's model-risk-management standard
(SR 11-7-aligned), its AI/agent governance standard, and applicable fair-lending
(ECOA/Reg B) requirements take precedence.

## Change dimensions

| Dimension | Fires when | Evidence attached |
| --------- | ---------- | ----------------- |
| `scope` | Intended use, population, materiality, or decision authority changes | before/after + registry/policy ref |
| `data` | Training/input source, features, window, or provenance changes | before/after + data-catalog ref |
| `tools` | (Agents) a tool/integration is added or its scope broadened | before/after + tool-log ref |
| `behavior` | Algorithm, architecture, prompt, parameters, or output behavior changes | before/after + registry ref |
| `controls` | Guardrails, thresholds/cutoffs, human oversight, or monitoring change | before/after + policy ref |
| `testing` | Evaluation coverage, benchmarks, or acceptance thresholds change | before/after + eval-harness ref |
| `users` | User population, roles, or autonomy change | before/after + registry/policy ref |
| `regulatory` | Regulatory classification, jurisdiction, or fair-lending surface changes | before/after + policy ref |

Findings are **additive and independent**; each fired dimension reports its own evidence.
There is no opaque composite "risk score". A dimension not supplied in the change record is
reported `not_evaluable` — it is never assumed unchanged.

## Critical risk flags

A **changed** dimension carrying any of these flags forces the **Critical** band, because it
weakens a control, broadens autonomy, or moves the regulatory surface:

`control_weakened`, `oversight_removed`, `autonomy_increased`, `regulatory_surface_changed`,
`threshold_loosened`.

Other typed flags (`data_provenance_changed`, `scope_expanded`, `new_tool_added`,
`permission_broadened`, `eval_coverage_reduced`) are recorded as context but do not by
themselves force Critical.

High-weight dimensions (tend to require independent revalidation on a material model):
`data`, `behavior`, `scope`, `regulatory`.

## Impact banding (deterministic, documented)

Let `n` = number of fired dimensions and `high_weight_hit` = any fired dimension in the
high-weight set.

| Impact band | Rule |
| ----------- | ---- |
| **Critical** | Any critical flag fired, OR (materiality = high AND high_weight_hit AND `n` ≥ `high_materiality_min_dims` [default 2]) |
| **High** | `n` ≥ `band_high_min_dims` (default 3), OR (materiality = high AND high_weight_hit) |
| **Moderate** | `n` ≥ 1 |
| **Low** | `n` = 0 (no material change declared) |

Banding is evaluated top-down; the first matching rule wins. It is a **finding for the human
adjudicator**, not a decision, and never triggers a change action.

The banding thresholds (`band_high_min_dims`, `high_materiality_min_dims`) come from the
change record's versioned `config` (defaults above when omitted). The engine records the
effective config on the pack (`pack.config`), and `validate_output.py` recomputes the band
with that **same** config — it never re-derives the band from hard-coded thresholds, so a
legitimately tuned config validates rather than false-failing.

## Recommended revalidation scope + governance path (by band)

| Band | Recommended revalidation scope | Recommended governance path |
| ---- | ------------------------------ | --------------------------- |
| **Critical** | Full independent revalidation before deployment | Independent model validation + change-governance adjudication before any deployment |
| **High** | Targeted independent revalidation of affected components before deployment | Independent model-risk review + change-governance adjudication before any deployment |
| **Moderate** | Owner-led revalidation with independent model-risk review before deployment | Model-risk notification + owner review before any deployment |
| **Low** | Revalidation not triggered under configured thresholds; record change and enhance monitoring | Record in model inventory and monitor; route to periodic review |

All entries are **recommendations for a human adjudicator**. The skill never approves,
waives, deploys, or closes a change.

## Hard boundaries (fail closed)

- Never state or imply the change **is approved**, cleared, waived, deployed, closed, or
  attested — attribute all decisions to the human adjudicator.
- Never infer a change on a dimension the requester did not declare.
- Never tune banding thresholds to a desired outcome or to a specific change.
- Threshold/cutoff and oversight changes are **control changes** (critical flags), not
  cosmetic tweaks.

## Items the adjudicator must weigh (always include when any dimension fired)

In-scope change vs. net-new use case (intake); independent validation coverage per changed
component; fair-lending/adverse-action impact of any threshold change; data-lineage and
provenance review; monitoring and rollback readiness; recording the human decision and
rationale in the change record.
