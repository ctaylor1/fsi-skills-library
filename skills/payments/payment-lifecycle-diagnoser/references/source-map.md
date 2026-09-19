# Sources and normalized input

The shipped scripts accept local JSON only. No gateway, processor, ledger, case-system, or external code-set integration is included. A reference describes supplied evidence; it does not mean a connector retrieved or authenticated it.

Required: `payment_id`, `as_of` (ISO date), `rail` (`card`, `ach`, `iso20022`, `wire`, `rtp`), `legs` (nonempty list). Each leg requires positive unique integer `seq`, `stage`, `status`, and `source_ref`; optional `reason_code` and timestamp. Optional monetary values require explicit finite `amount` and uppercase three-letter `currency`.

For wire/instant code interpretation, declare `code_system: iso20022` only when the source actually uses it. The bundled dictionaries are a representative subset; input `codeset_version` is source metadata, not a loaded implementation version.

Settlement recognition requires a settlement-stage `SETTLED` or `ACCC` leg with `settlement_evidence: {status: confirmed, payment_id: <same payment>, source_ref: <settlement record>}`. This records supplied evidence, not an authenticated connector result. Authorization-stage approval never satisfies it.

Output preserves `source_trace`, its stable hash, a content-derived diagnosis ID, interpreted trace and cautions. Sequence gaps and missing timestamps limit completeness; a pending state remains pending without a scheme timeout assessment. Keep payment/attempt identity separate when preparing the input; do not combine unrelated attempts into a fabricated lifecycle.
