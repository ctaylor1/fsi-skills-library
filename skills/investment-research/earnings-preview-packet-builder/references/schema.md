# Native schema — 0.2.0

Require packet ID, preparer ID, review profile ID/version, issuer ID/name/ticker, economic as_of_date, aware `knowledge_cutoff`, event fiscal period/report date/comparable period and aware `event.release_at`. Cutoff must precede release, including within the same day. Require a versioned template, required sections, required review-role list and nonempty items. Item source bundles require aware `known_at` no later than cutoff; data-point vintages, when supplied, must also qualify. Numeric metric values are finite JSON numbers or null, with unit/fiscal-period/accounting-basis labels; any supplied consensus/guidance value requires a source and aware known_at. Economic forecast periods may lie in the future if their source vintage is eligible.

## Output and partial coverage

Ordered items retain source bundles/vintages, data points, supplied content-review records, readiness reasons, template coverage, consensus-versus-guidance table, explicit fiscal KPI comparators, role-assertion rollup and draft notices. `ready-for-control-review` means supplied content/role assertions are complete for further human control review. Incomplete sources, sections or role records yield `hold-for-approval`. Neither status authenticates an approver, proves entitlement or clears distribution.

All outputs include canonical `input_hash` over the complete original JSON and `source_truth: unverified`; no embedded `source_input` is accepted. Keep the original separately. Finite JSON, domain guards and input shape validation run before computation. Output validation requires `--input` (self-test retains its fixture original) and reconstructs every native field. Added narrative is a separate reviewed artifact, not a permitted unchecked field.
