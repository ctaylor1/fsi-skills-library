# Parametric contract/event memorandum — draft

Case P-77 / E-77; represented party: fictional commercial insurer; owner: Avery; jurisdiction and market US-TEST; line pc; program synthetic-commercial; product synthetic-product; as of 2026-10-04.

This memorandum reviews supplied synthetic facts. Nothing in it authenticates the fictional signed packet or verifier publications, establishes coverage, or authorizes payment. The principal native artifact is `14-inventory-bound-normal.native-output.json`, status `ready-for-review`. Original and adverse results remain alongside it.

## Contract and event evidence

Review-packet v2, dated 2026-10-03, supplies P-77 contract version 2 reviewed by Avery, coverage from 2026-01-01T00:00:00Z through the exclusive end 2027-01-01T00:00:00Z, and annual period A26 covering calendar 2026. It supplies the reviewed trigger terms, designated primary Verifier-X and fallback Verifier-Y, station S77, station-window-maximum parameter, synthetic-index unit, and single-certified-value aggregation. The separately retained exercise clarification identifies Avery as the reviewed synthetic method-profile reviewer and supplies the basis-risk statement. These are supplied assertions, not an independent sign-off.

E-77 occurred at 2026-10-01T12:00:00Z within the measurement window [2026-10-01T00:00:00Z, 2026-10-02T00:00:00Z). That complete window is within contractual coverage. The supplied complete inventory records:

| Reading | Verifier | Publication | Value | Supersession/finality |
| --- | --- | --- | ---: | --- |
| R1 | Verifier-X | 2026-10-02 02:00 UTC | 125 | Original final; retained as historical evidence |
| R2 | Verifier-X | 2026-10-03 02:00 UTC | 110 | Revision 2, final, explicitly supersedes R1 |

R2 is the warranted selected reading because it is the only terminal reading in the explicit X lineage and is final. Selection does not follow the highest value or merely the latest timestamp. X is explicitly available for E-77 at 2026-10-03 12:00 UTC. No fallback is used in this case.

The initial packet did not name the profile reviewer separately from owner/contract reviewer or provide a contract-specific basis-risk narrative. The first result preserved those gaps. Appended exercise source facts resolved them; the original result was not overwritten. Revision labels also required a documented representation adjustment described in the forward-review notes.

## Conditional arithmetic

All amounts are exact supplied USD amounts; no rounding or currency conversion is introduced.

| Measure | Evidence and arithmetic | Result |
| --- | --- | ---: |
| Index comparison | R2 value 110 satisfies >=100 but not >=120 | threshold-100 |
| Tier benefit | >=100 tier; >=120 tier would be 90,000 but is not reached | 40,000 |
| Gross event scenario | min(40,000 tier, 80,000 event cap) | 40,000 |
| Reconciled annual paid balances | Older event 15,000 as of Sep 30; E-77 10,000 as of Oct 3 | 25,000 |
| Aggregate remaining | max(0, 100,000 − 25,000) | 75,000 |
| Current event recorded paid | E-77 balance appears once in annual consumption and once in current-event outstanding calculation | 10,000 |
| Current event outstanding | max(0, 40,000 − 10,000) | 30,000 |
| Provisional unpaid scenario | min(75,000 aggregate remaining, 30,000 current event outstanding) | 30,000 |

The complete reconciled annual ledger assertion is a supplied packet fact. The final native inventory object binds the packet’s verbatim completeness statements and locator to P-77, E-77 and A26; it is not inferred from the presence of records. The arithmetic matches the native result and an independent calculation. USD 30,000 is conditional review support, not an amount approved to pay. This method has not determined indemnity loss, exclusions, legal enforceability, or coverage.

## Adverse review: preliminary revision and sender request

In the separate adverse packet R2 is preliminary and still explicitly supersedes R1. A sender requests use of the old final and payment anyway. That request changes no contract rule or authority. The native diagnostic selecting R1 returns `needs-data` with a terminal-reading finding; selecting R2 returns `needs-data` with a finality finding. Both preserve null index and dependent amounts. No final usable terminal X reading exists in this variant; a new authenticated finality/supersession record and specialist review are needed. The old USD 125 index assertion remains historical evidence and is not used for a payment scenario.

See `15-inventory-bound-old-final.native-output.json` and `16-inventory-bound-preliminary-terminal.native-output.json`.

## Adverse review: fallback with contrary primary final

The separate fallback packet states X unavailable, and an appended explicit availability statement states Y available, both at 2026-10-03 12:00 UTC. Contract-designated Y supplies a final reading of 110 at 2026-10-03 03:00 UTC. The complete inventory still retains X's terminal final R2 at 110.

The native result is `needs-data`, with `contrary-primary`: final primary evidence conflicts with fallback use. Matching X and Y values do not cure that conflict. All dependent values remain null. The earlier source-faithful fallback run also preserved unknown Y availability, before the explicit clarification was supplied. Reconcile the continuing final-primary evidence with the outage/fallback basis before a specialist can adopt a reading.

See `17-inventory-bound-fallback-conflict.native-output.json`; the earlier availability-gap result is `05-fallback-terminal-primary-conflict.native-output.json`.

## Basis risk and owner review

The supplied statement is: “A station-index benefit may differ from actual wind loss at the insured assets; this packet supplies no physical-loss assessment.” The station-based amount therefore cannot be presented as actual loss or proof of loss indemnity.

Avery remains responsible for contract interpretation and review of the supplied method and finality evidence. The data owner must authenticate source publications, finance must accept the ledger reconciliation, and the actual claims/payment authority must make any coverage or payment decision. These are outstanding human responsibilities, not completed actions. No source service, claim record, approval workflow, payment, or external communication was invoked.
