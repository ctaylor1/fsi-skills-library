# Source-backed profile preparation

The public summaries in [consumer-error-profiles.json](consumer-error-profiles.json)
and [scheme-stage-profiles.json](scheme-stage-profiles.json) are reviewed as of
2026-09-18 with a 2026-10-18 refresh date. They identify scope, clock basis, exceptions
and evidence needs; they do not supply universally applicable deadlines.

Input to scripts/prepare_profile.py: kind consumer-error or scheme-stage; profile_id;
as_of ISO date; scope {case_id, participant, jurisdiction, product, rail, and network/
stage for scheme review}; review {owner, source_ref, applicability_rationale,
effective_from, review_due, scope_hash, required_clock_names}. scope_hash is
payment_contract.stable_hash(scope), a linkage check only. Applicable clock names
are selected by the supplied specialist from the profile with its exceptions.

An incomplete, stale or mismatched review yields a draft. A complete consumer-error
review yields a supplied profile for the native issuer case's statutory_profile.
Clocks still require exact triggers, source evidence, reviewed due dates and named
calendar/cutoff references. Future investigation-completion triggers must remain
unknown until the event occurs; do not fabricate due dates to satisfy a schema.

Scheme profiles are always orientation-only until the native merchant reviewer is
given authorized current condition/eligibility rules and the actual case notice.
No evidence-count shortcut, generic 120-day deadline or automated filing is supplied.

Case scope fields in prepared profiles must stay attached when handing off. Source
hashes and reviewer references do not authenticate authority or legal correctness.
