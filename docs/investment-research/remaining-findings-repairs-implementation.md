# Investment Research remaining findings repairs

Repair checkpoint for the three findings in the follow-up architecture review.
The portfolio remains 42 native packages and nine reviewed adapters. Earlier
phase, control-repair and evidence-reconciliation records retain their original
bytes and source versions. [Validation](remaining-findings-repairs-validation/README.md)
records fresh checks and before/after public-command evidence.

| Finding | Correction |
|---|---|
| P1: Live legacy surveillance bypassed temporal and quote-evidence controls | Public surveillance entrypoints require the explicit `ir-phase2/1.0` contract. Legacy requests and legacy output packets fail with a controlled migration-required error; they cannot calculate or validate through the older path. |
| P2: Missing issuer-credit evidence could claim completeness or fail after successful intake | Omitted and null nullable financial values are consistently unavailable. Affected cash-flow results create explicit unresolved issues and a partial status; independent supported measures remain available. Null debt reconciliation is incomplete evidence, including in calculation lineage. |
| P3: Capability versions disagreed with installed packages | Current canonical and bundled capability versions match installed skill metadata. Structural validation and regression tests enforce agreement and reject missing, malformed or stale version declarations. |

## Live legacy surveillance migration

Surveillance 0.4.1 accepts new computation only through its documented analytical
contract. No flag re-enables the old calculations. Merely adding a schema label
does not migrate evidence: the request must satisfy the current financial periods,
source register, permission context, structured observations, dated issuer/security
mapping and explicit freshness policy. Missing evidence is not synthesized from
legacy IDs, assertions or source labels. Eligible analytical requests still return
useful partial results when the current contract permits missing evidence.

The retained old inputs, outputs, source snapshots and validation logs remain
historical artifacts. Exact historical reconstruction uses the corresponding frozen
source in the evidence checkpoint; a past successful result is not accepted as a
current native output. Active instructions, selftests and eval commands distinguish
the current contract from legacy rejection cases. Active Phase 1 test coverage is
updated to exercise the current supported surveillance API; its earlier source is
also retained in this checkpoint.

Asset Management's historical surveillance alias resolves to the same current
package and therefore cannot bypass migration. Its retained historical maturity
and source-coverage assertions run explicitly against frozen source; separate live
alias checks require the repaired contract. The older generic Asset Management
adapter does not automatically translate legacy evidence into that contract.

## Issuer-credit missingness

Issuer credit 0.2.1 keeps omitted and null input representations in their detached
originals and hashes. Calculations treat both as unknown; no original is filled in
or rewritten. Missing operating cash flow or capex withholds free cash flow. Missing
FFO, missing usable debt or a nonpositive debt denominator withholds FFO/debt.
Explicit zero cash flow, capex and FFO remain real values; unavailable ratios never
become zero. Nullable debt evidence and missing principal retain reconciliation
issues without an exception after valid intake.

## Version parity and preservation

The router is 0.4.2. All 42 installed capabilities, including the router and dossier
foundation entries, declare their actual native package version. Current catalogs
and router resources are refreshed; historical phase inventories are unchanged.
Catalog regeneration from the saved catalog proves local reproducibility only;
the external authoritative workbook remains a separate reconciliation task.

The new source baseline captures 20,387 files from the initially dirty checkout.
The ownership audit protects all 1,926 earlier phase and repair evidence files.
Pre-edit copies retain the three changed packages, active IR tests, current catalogs
and affected integration sources. The new checkpoint contains its own replays,
regressions, independent review and validation results instead of overwriting an
earlier report.

This repair does not implement the broader blueprint's remaining workflow,
practitioner, institutional or deployment acceptance work. Supplied identities,
source contents, completeness and permissions remain unauthenticated assertions.
