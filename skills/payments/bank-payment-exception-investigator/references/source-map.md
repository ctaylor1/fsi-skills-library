# Supplied bank-payment case evidence

No case persistence, network query, XML parser, account-resolution service, or communication adapter is shipped. The local JSON must declare `scope: bank-payment`, `message_format: iso20022-normalized`, `config_version`, `as_of`, and nonempty `exceptions`.

Each exception supplies `exception_id`, `exception_type`, `scheme`; optional existing `case_id`, `case_ref`, `lead_owner`; identifiers; `amount: {value, currency}`; masked parties; and messages containing `msg_type`, timezone-aware `timestamp`, `msg_ref`, optional status/reason/direction. Missing messages or identifiers yield needs-data. Uncited or malformed supplied messages fail input validation. Native ACH/card/merchant records are unsupported.

`disposition_evidence` is required before any proposed repair/return/recall action. Fields: `source_ref`, `scheme_rule_ref`, `rule_profile_version`, `assessment_owner`, `assessed_at`, `scheme`, `operation` (`repair`, `return`, `recall`), `window_valid`, `eligibility`, and `finality_state` (`not_settled`, `settled`, or unknown). Recall additionally needs an explicit consent requirement and available-funds evidence. Repair needs `repair_evidence: {confirmed_defect: true, field, new_value, verification_source}`.

These are cited supplied assessments, not implemented legal analysis or authenticated approvals. Preserve conflicting reports; an apparently complete schema does not prove accurate facts. A reason-code label never replaces scheme/finality assessment.

Priority configuration includes threshold currency; unmatched currency amounts contribute no amount points. Calendar-day age is a triage input, not a processing deadline. Configuration/version labels do not retrieve live rulebooks.
