# Investment Research evidence reconciliation

Implemented 2026-10-20 under the request to close the remaining supplied-evidence
reconciliation gaps and preserve earlier phase and repair evidence. This updates
two existing native packages; the portfolio remains 42 methods and nine reviewed
adapters. The previous [repair record](control-repairs-implementation.md) is a
historical checkpoint and remains unchanged.

| Previously accepted inconsistency | Current bounded control |
|---|---|
| The same economic EBITDA cost repeated under different row IDs | A source-bound economic-event ledger, canonical issuer/event identity and explicit total/component selection prevent repeated or overlapping amounts from supporting adjusted EBITDA. |
| Instrument currency/principal disagreed with consolidated reported debt | Explicit accounting inclusion/exclusion, comparable context, complete supplied coverage and a cited principal-to-carrying-value bridge must reconcile exactly to reported debt. |
| Matching quote IDs could name an unrelated security | Selected quote evidence must bind the requested issuer/security and a dated instrument mapping covering both observations. |
| Quotes could cite financial-statement sources | Selected structured observations require market-data source roles and exact registered source block/version/citation, identity, value, basis and observation time. |

## Economic-event reconciliation

`issuer-credit-researcher` 0.2.0 selects adjustments from
`ebitda_adjustment_events`. Each ledger entry carries issuer, financial context,
economic identity/version, signed amount, additive treatment and source binding.
`source_binding` reconciles source ID/version, knowledge time, precise registered
block, target issuer and canonical `economic_event_key`. The canonical issuer/key
identity remains stable across source documents, locators and versions; changing a
row ID or provenance does not create a new additive cost.

An event total may be selected once, or its complete distinct additive components
may be selected once. Total/component overlap, component duplication, aliases,
multiple candidates, mismatched amounts/citations, missing identities or
incomparable context leave the reconciliation unavailable. Adjusted EBITDA and
its dependent ratios are then null; reported EBITDA remains separate. Genuine
distinct equal-valued events are permitted. No adjustments and no ledger means no
adjustments; unused supplied ledger events remain unresolved.

## Debt reconciliation

Every instrument declares a cited inclusion or exclusion in the target issuer's
reported perimeter. Included principal must have matching currency, unit, basis,
scope and reporting period, with an explicit contractual-principal measurement
basis. Excluded structural obligations retain their own identity and can differ
in currency/perimeter; a scoped exclusion does not determine legal priority.

`debt_reconciliation` binds complete supplied inventory coverage, its description
and financial context to source evidence. Its bridge identifies included
instruments, signed principal-to-carrying-value differences and canonical economic
identities. A documented zero bridge is required when principal and carrying value
coincide. Neither equality nor an unexplained balancing amount is inferred.

Included principal plus the bridge must equal reported gross debt exactly.
Event/component and debt tieouts use rational arithmetic on the finite JSON
numbers' decimal representations, without an epsilon or caller tolerance. No FX,
unit, perimeter or accounting conversion is provided. Missing or conflicting debt
evidence withholds gross/net leverage and FFO/debt while retaining supported
EBITDA, independent interest coverage and free cash flow. Reconciliation reasons,
inventories, selections, totals and lineage remain visible in the output.

## Quote evidence and issuer mapping

`issuer-credit-surveillance-reviewer` 0.4.0 selects each asserted quote by
`observation_id` from `spread_evidence`. The selected structured observation must
agree with the assertion's identity, finite value, basis, timestamp and exact
citation. Its source must be eligible market data with the matching registered
version and precise block, explicitly covering both security and issuer. A source
kind label without observation contents cannot supply missing evidence.

`instrument_evidence` supplies one source-bound security/issuer/currency mapping
whose inclusive effective period covers both observations. Security requests bind
the exact requested security and issuer; issuer requests bind the requested issuer.
Duplicate/conflicting observations, ambiguous mappings, wrong roles/versions/
blocks, unrelated identities and out-of-period mappings withhold the spread change
and widening alert. Existing cutoff, knowledge-time precision, observation order,
economic as-of and explicit current-age controls remain in force. The delta is
computed from reconciled evidence values, rather than accepting an asserted delta.

Only eligible selected evidence and mapping appear in successful spread context.
Withheld context contains no quote observations or mapping; financial metrics can
remain available in a partial result. The common cited-source gate still withholds
the entire projection when source eligibility fails.

## Migration, verification and boundaries

The common `ir-phase2/1.0` input envelope remains. Missing new reconciliation
metadata is a coverage gap with dependent results unavailable, not permission to
infer evidence from legacy IDs or old fixtures. Malformed structures, duplicate
technical IDs and invalid citations still reject. Source claims must be extracted
and reviewed independently; do not build a ledger by copying unsupported assertions.

Active examples, goldens, evals, manifests, package metadata and saved catalogs are
updated. Existing regression cases now carry the evidence needed to isolate their
original temporal, arithmetic and identity checks. Original tests and source bytes
are preserved in the new pre-edit snapshot. Earlier Phase 1–4 and control-repair
implementation/validation records remain byte unchanged. The canonical shared
runtime, routing registry and reviewed adapters are unchanged.

The [new validation checkpoint](evidence-reconciliation-validation/README.md)
retains actual before/after public-command cases, regression results, independent
fresh cases, source/package hashes and preservation/readback evidence. The four
recorded reconciliation gaps are now enforced as supplied-data controls. This does
not authenticate real-world economic keys, completeness, extraction accuracy,
source contents or permissions. Practitioner/institutional acceptance and live
source access, publication, credit approval or execution remain separate work.
