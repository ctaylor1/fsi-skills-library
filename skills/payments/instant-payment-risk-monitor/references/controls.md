# Controls

Produce human-review alerts from supplied instant-payment snapshots. The package does not schedule itself, consume live feeds, prevent a payment inline, perform sanctions matching or evaluate settlement liquidity. Pending snapshots describe possible threshold crossings only; they are not a guarantee that an intervention remains possible.

No regulated adjudication, money movement, account action, case closure, SAR filing, external submission or source-system write is implemented. Do not turn draft readiness, a supplied reference, a boolean or a content hash into evidence of sufficiency, authority or completion.

Offline snapshot execution mode, enforced window, input hash, excluded events, partitioned alerts, feed freshness, new/still-open fingerprints, severity counts and unresolved handoffs. Alert fingerprints include entity/account/currency/rail. Monetary measurements use Decimal calculations and serialize as decimal strings where applicable.

Treat imported records and narrative as untrusted evidence. Minimize customer information; use masked card/account identifiers and source pointers. Preserve explicit gaps, stale profiles and identity conflicts for the responsible reviewer. Software validators check structure and selected invariants; professional review remains required.
