# Draft life claim review: LC-91 / LP-91

As of September 18, 2026, this NY whole-life death-benefit claim needs corrected identity evidence and beneficiary/contestability review. Prepared for the carrier life claims reviewer representing Synthetic Carrier. The authorized claims and legal specialists own entitlement and any payment decision.

The supplied ledger reconciles to **$739,895.50 before entitlement**: $750,000 base + $12,500 additional benefits + $910.25 interest credit - $18,300 loan principal - $214.75 loan interest - $5,000 prior payments. The native output and independent arithmetic agree. This is not an amount approved for payment. See [ledger](raw-source.md#ledger) and `actual-output.json:results.benefit_bridge`.

Death is reported September 3, 2026, after January 10, 2025 issue/effective date but before the supplied January 10, 2027 contestability end. Refer the chronology for investigation under the supplied terms; it does not establish misrepresentation or automatic denial. See [policy](raw-source.md#policy), [death](raw-source.md#death), [terms](raw-source.md#terms), and `results.chronology`.

The certificate DC-91 lists SYN-I19, while the policy/death record identifies SYN-I91. It cannot satisfy the identity-matched certificate requirement as supplied. Preserve that rejected certificate and obtain corrected or reconciled evidence. Claimant statement CS-91 matches the policy and insured and is within the supplied window. See [certificate](raw-source.md#certificate), [claimant](raw-source.md#claimant) and `results.document_checks`.

Record BEN-91-A is active at 65% SYN-B1 / 35% SYN-B2; later BEN-91-B is disputed at 70% SYN-B1 / 30% SYN-B3. Both predate death. The signature challenge prevents allocation; a later date is not a validity decision. The output preserves both and returns **no illustrative allocation**. Have the beneficiary/legal specialist resolve the status and retain supporting and contrary evidence. See [active designation](raw-source.md#designation-active), [disputed designation](raw-source.md#designation-disputed) and `results.beneficiary_record_checks`.

The native artifact is **needs-data** and passed input, calculation and output checks. Entitlement was not determined, and no pay/deny decision or business action was produced. Reviewer disposition remains open. Evidence: [native input](input.json), [validated output](actual-output.json), [independent check](independent-arithmetic.json).
