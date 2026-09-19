# Domain rules — Claim Cost Reconciliation

- Comparable identity = category + whitespace/punctuation-normalized description + currency + service date + provider + unit + quantity. An amount match alone is not enough.
- Amounts must be finite nonnegative numbers; quantity positive and finite. Currency is explicit, uppercase three-letter; dates are calendar dates. No currency conversion or universal two-decimal rounding is applied.
- Document source, version and date are required. Duplicate identifiers and superseded documents are excluded from comparison and preserved as unresolved history.
- Within a comparable identity, the same exact amount across distinct documents is a duplicate candidate; distinct amounts across distinct documents are a difference. Human review determines whether two charges concern the same service or are payable.
- Required supporting references must resolve to supplied current documents with source references. A nonempty dangling ID is not support.
- Any unevaluable item yields not-evaluable; otherwise findings yield items-for-review, else clean. Clean means only that these bounded reconciliation checks found no exception.

## Scope limit
No damage causation, price reasonableness, depreciation, medical necessity, coverage, reserve or settlement judgment. Same-description matching is a review heuristic, never proof of duplicate billing.
