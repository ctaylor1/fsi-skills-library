# Offline request schema and source limits

All inputs are local supplied evidence. There is no live payment, screening, directory, approval, or execution adapter. The runnable fixture `evals/files/case_example.json` shows the full contract.

Top-level: `case_id`, `payment_id`, `type`, timezone-aware `as_of`, `catalog_version: offline-field-repair-v1`, `exception_confirmation`, `payment_snapshot`, `policy`, `screening`, `proposed_repair`, `evidence`.

- `exception_confirmation`: matching case ID, status `confirmed`, and source reference.
- `payment_snapshot`: matching payment ID, end-to-end ID, legal entity ID (`entity_id`), rail, explicit amount/currency, held/rejected state, source reference/time, and original `fields` dictionary. Explicit null is allowed for a genuinely absent field; omission is not proof of absence.
- `proposed_repair`: `action: repair_and_resubmit`, field, exact `old_value` and nonempty different `new_value`, and unchanged amount/currency.
- `policy`: ID/version/source; entity; rails; currency and positive max amount; allowed fields/types; required approver role; effective and expiry timestamps.
- `screening`: clear/false-positive-cleared status, disposition ID, source reference, matching payment ID, screened timestamp, and `repair_binding` computed from `{payment_snapshot, proposed_repair}` using shared `stable_hash`.
- `evidence.verification_source`: source supporting the replacement value.

The screening hash binds the supplied disposition to the exact proposed instruction. It does not authenticate that disposition. Policy scope is checked against the supplied request, but the offline planner cannot authenticate the policy owner or verify live approver authority.

Output embeds the complete source request, exact change, unchanged-field hash, policy/screening, proposed steps and stable idempotency scopes. Data must be masked consistently without losing the identifiers needed for operator verification.
