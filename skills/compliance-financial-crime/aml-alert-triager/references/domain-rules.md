# Domain rules and current authority

Three bounded suppression candidates remain: exact duplicate (SUP-DUP-01), internal legs on the supplied whitelist (SUP-WL-INTERNAL), and scoped seasonal approval (SUP-SEASONAL-01). Without matching authorization, preserve the alert for duplicate review or escalation. Do not manufacture approval evidence. Scoring uses supplied configuration; absence is never evidence of low risk. Escalation bundles are extracts, not a completed investigation or professional disposition.

## Sources checked 2026-09-21

[FinCEN SAR FAQs, October 9, 2025](https://www.fincen.gov/system/files/2025-10/SAR-FAQs-October-2025.pdf) clarify existing institution-specific rules: near-threshold cash alone is insufficient for a structuring SAR. Suppression policy and priority weights here are institutional choices, not regulatory safe harbors.

Guidance is distinguished from binding underlying law; illustrative implementation choices are not legal safe harbors. Phase 1 does not certify professional adequacy.


## Independent forward-test correction

Before suppression consideration, validate the assessment date and every alert, open-case and authorization scope period as real dates with start <= end <= as_of. Invalid/future chronology fails the public intake boundary and produces no native result, even when the same invalid period appears in all supplied records. Missing evidence that raises only warnings continues to produce a partial review.
