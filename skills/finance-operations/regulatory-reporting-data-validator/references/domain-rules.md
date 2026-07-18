# Domain Rules — regulatory-reporting-data-validator

Explainable validation **checks** for a regulatory-report package and how the fired set maps
to a **filing-readiness band**. Thresholds, tolerances, and required roles are configuration
(versioned, owned by the regulatory-reporting control team), not hard-coded judgments, and
are never loosened to clear an exception. The firm's reporting-instruction spec (e.g., FFIEC
Call Report / FR Y-9C / FR 2052a instructions, or COREP/FINREP DPM for EU deployments) takes
precedence over any default here.

## Check taxonomy

| Check | Class | Fires (fail/warn) when (default config) | Evidence attached |
| ----- | ----- | --------------------------------------- | ----------------- |
| `completeness` | blocking | A cell in `required_cells` is absent or blank | Missing cell ids |
| `lineage_completeness` | blocking | A reported cell has no `source_refs` (not filing-traceable) | Cell ids without lineage |
| `edit_checks` | blocking | A declared arithmetic relationship (e.g., subtotal = Σ components) does not hold within `tolerance` | check_id, expected, reported, delta |
| `reconciliation_tie_out` | blocking | `|reported_value − source_value|` > `tolerance` for a reconciliation | recon_id, cell, source, reported, delta, tolerance |
| `range_checks` | blocking | A configured cell value falls outside `[min, max]` (sign/bounds) | cell, value, min, max |
| `sign_off_completeness` | blocking | A required role in `required_sign_off_roles` has no dated sign-off | Missing roles |
| `segregation_of_duties` | blocking | Preparer is also the approver (when `enforce_segregation_of_duties`), or a sign-off predates the data `as_of` | Role/name collision, timing |
| `timeliness` (overdue) | blocking | `as_of` is after `due_date` | due_date, as_of, days_overdue |
| `variance_vs_prior` | advisory | `|current − prior| / max(|prior|, 1)` > `variance_pct` for a comparable cell | cell, prior, current, pct |
| `timeliness` (due-soon) | advisory | `0 ≤ days_to_due ≤ due_soon_days` | due_date, as_of, days_to_due |

Checks are **additive and independent**; the output reports each fired check with its own
evidence. There is no opaque composite "quality score".

## Readiness mapping (deterministic, documented)

| Band | Rule |
| ---- | ---- |
| **Blocked** | ≥ 1 **blocking** finding fired |
| **Review** | 0 blocking findings, ≥ 1 **advisory** finding fired |
| **Clear** | 0 findings fired |

The band is a **triage state for a human preparer/approver**. `Clear` means "no deterministic
exceptions were found" — it is **not** an approval to file, a certification, or a sign-off.
Human sign-off and authorized submission are always still required.

## Hard boundaries (fail closed)

- Never state or imply that the report **is** accurate, complete, or compliant, "approved for
  filing", or "ready to file" — describe exceptions factually and attribute the filing
  decision to the human/authorized system.
- Never **certify, attest, sign off, file, or submit** — those are human controls.
- Never **post or propose a GL correction** here; route breaks to `gl-reconciler`.
- Never loosen a **tolerance/threshold** to clear an exception, or net offsetting breaks.
- `variance_vs_prior` describes a **change**, not an error — keep it advisory and invite an
  explanation.

## Remediation prompts (always include when a finding fired)

Route reconciliation breaks to `gl-reconciler` for a proposed correction; confirm mandatory
cells and their lineage with the reporting instructions; obtain the missing/mis-timed
sign-off from the correct role; document the variance driver (acquisition, reclassification,
restatement, seasonality); re-run this validator after remediation. The pack must invite the
preparer to resolve each exception before any human sign-off.
