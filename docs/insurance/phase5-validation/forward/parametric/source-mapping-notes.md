# Source mapping notes

All data is synthetic and supplied by the exercise, not independently authenticated. The original run preserves absent profile reviewer and basis-risk narrative as null. The clarified run adds the explicitly supplied Avery profile review and verbatim basis-risk statement; no professional decision was invented.

Local technical labels: case_id, profile_id, profile extraction version review-packet-v2, tier IDs, ledger entry IDs, and older-event (the single described prior event) are local labels used to map the packet, not claims about extra documentary identifiers. P77/E77 references are consistently normalized to the user-given P-77/E-77. The profile version identifies this extraction from packet v2, not an independently identified source profile revision. Calendar effective_to 2026-12-31 is derived from the exclusive coverage end 2027-01-01T00:00:00Z and the stated calendar-2026 validity.

The fallback variation supplies a final Y reading, but no explicit Y available=true assertion. Its availability is therefore null; a final publication is not assumed to supply a separate availability attestation.

Adverse 03 intentionally feeds the sender-requested R1 selection to check rejection; adverse 04 selects the actual terminal R2 to verify that its preliminary status also prevents use. They are diagnostic checks, not payment proposals.

Native recovery cases 06-09 change revision representations to strings. R1 and Y1 use original as a local original-reading designation; their revision numbers were not stated in the raw packet and the original numeric 1 was a mapping assumption, not an authenticated fact. R2 uses the supplied revision 2 as text. This recovery is explicit because the native schema does not document that revision must be a string, integer values passed structural validation, and the native method nevertheless withheld all measures as revision unresolved. Case 09 additionally uses the explicitly authorized appended availability clarification for both X and Y.

Final current-runtime cases 10–13 use the newly documented capacity slug parametric-claims-review. This is a schema representation of the same requested specialist review, not a change in represented party or professional authority. All original source facts and earlier results are retained.

Final cases 14–17 map the two original completeness assertions verbatim to data.inventory, bind contract_id P-77 / event_id E-77 / aggregate_period_id A26, and cite review-packet plus the supplied fictional signed-packet locator. No new source claim is introduced. Equality verification excluding inventory and local case_id confirms every other input field is unchanged from 10–13. Earlier input/native output hashes were verified unchanged.
