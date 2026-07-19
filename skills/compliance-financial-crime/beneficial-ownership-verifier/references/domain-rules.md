# Domain Rules — beneficial-ownership-verifier

How effective ownership is computed, how candidate beneficial owners are identified, how the
declaration is reconciled, and how the gap set maps to a **recommended readiness band**.
Thresholds and the control-prong rule are **jurisdiction configuration** (versioned, owned by
policy), never hard-coded judgments and never tuned to an entity. The firm's KYC/CDD standard
and the applicable jurisdiction rule take precedence; the US default reflects the CDD Rule
(31 CFR 1010.230): a 25% ownership prong plus a control prong.

## Effective-ownership computation

For the root legal entity `R` and a natural person `P`, `P`'s effective ownership of `R` is
the sum, over **every** directed ownership chain from `P` up to `R`, of the product of the
edge percentages along that chain:

```
effective(P, R) = Σ_paths(P→…→R)  Π_edges (pct / 100)
```

- Chains through intermediate entities are followed transitively; **multiple chains to the
  same person are summed** (`aggregate_across_chains`, default true). Example from the golden
  fixture: Jane Doe holds 30% of the root directly and 20% of Gamma (which holds 30% of the
  root) → 30 + 0.20×30 = **36%**.
- **Circular ownership** is detected; the affected chain is skipped and a blocking
  `circular_ownership` data-quality gap is raised (ownership is never silently dropped).
- Percentages are rounded to 4 decimals before the threshold comparison.

## Prong identification

| Prong | Fires when (default config) | Evidence attached |
| ----- | --------------------------- | ----------------- |
| **Ownership** | `effective(P, R) ≥ ownership_threshold_pct` (default 25%) | The ownership edges on `P`'s contributing chains |
| **Control** | `P` appears in `control_edges` as a senior managing official | The officer/control record |

Both prongs are reported independently. A person just below threshold (the fixture's Lena
Ortiz at 24%) is **not** a UBO; a control-prong person **is** a UBO regardless of ownership.

## Reconciliation gap taxonomy

| Gap type | Meaning | Severity |
| -------- | ------- | -------- |
| `undeclared_owner` | Computed ownership-prong UBO not on the declared list | blocking |
| `undeclared_control` | Control-prong person identified from records but not declared | blocking |
| `control_prong_unsatisfied` | Config requires a control person and none is identified | blocking |
| `declared_not_supported` | Declared party's ownership computes below threshold with no control basis | blocking |
| `circular_ownership` | A cycle was detected in the ownership graph | blocking |
| `pct_mismatch` | Declared vs computed percentage differ beyond `pct_tolerance` | remediable |
| `missing_document` | Identified & declared UBO with no supporting document | remediable |
| `expired_document` | Supporting document expired or older than `doc_max_age_days` | remediable |
| `ownership_over_100` | Direct ownership of an entity sums above 100% (data quality) | remediable |

## Readiness mapping (deterministic, documented)

| Recommended band | Rule |
| ---------------- | ---- |
| **Escalate** | Any **blocking** gap fired |
| **Remediation-needed** | No blocking gap, but ≥ 1 **remediable** gap fired |
| **Complete-for-review** | No gaps fired |

The readiness band is a **triage recommendation for a human adjudicator**. It is not an
onboarding approval, not a beneficial-ownership determination, and it never triggers a case
action or a filing. `validate_output.py` recomputes this mapping and fails closed if the pack
disagrees with it.

## Hard boundaries (fail closed)

- Never state or imply that a person **is** / **is confirmed** / **is verified** as a
  beneficial owner — the skill identifies *candidates* and the human decides.
- Never approve/reject onboarding, close the case, or file a BOI/SAR report.
- Never tune the threshold or control-prong rule to the entity; use only the versioned config.
- Never treat the customer's declaration as evidence of itself; reconcile it against the
  authoritative records.

## Jurisdiction packs & effective dates

The `config` block is a versioned jurisdiction pack: `ownership_threshold_pct`,
`require_control_prong`, `min_control_persons`, `document_required_for_ubo`,
`doc_max_age_days`, `pct_tolerance`, `requirements_effective_date`, and `authority`. Deploy
additional packs (e.g. a 10% threshold, or an EU AMLD "plus one share" indirect rule) as new
versioned configs; the output records the version so a verification reproduces exactly.
