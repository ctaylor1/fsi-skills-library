# Insurance data source map

1. Supplied policy, claim, premium, exposure or actuarial snapshots provide record values and source references.
2. A supplied definition registry establishes metric meaning, unit, gross/net/ceded basis, date basis and versions.
3. The supplied reconciliation configuration establishes expected periods/series and movement thresholds.

The scripts read local JSON only. References to data stores or APIs describe deployment needs; no connector, source authentication, data correction or production integration is implemented here. Hashes bind supplied JSON content, not external source truth. Use [insurance-contract.md](insurance-contract.md) for context, statuses and receiver validation.

Citations identify both observations involved in a comparison. Missing-period findings cite the declared expectation rather than inventing a missing source row. Duplicate findings retain every member's source reference, supplied value and basis; no duplicate row is selected as the authoritative value. Independently observable basis conflicts remain reported alongside duplicate ambiguity.

[ASOP 23 and other current actuarial standards](https://www.actuarialstandardsboard.org/standards-of-practice/) are authoritative reference anchors for qualified actuarial use. The package's numeric threshold and break taxonomy are repository conventions, not requirements asserted by the ASB. Reviewed September 18, 2026.
