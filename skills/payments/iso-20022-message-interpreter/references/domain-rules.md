# Profile semantics

`pain.001/008` and `pacs.003/004/007/008/009` use the package's normalized transaction view. `pain.002/pacs.002` use its normalized status view. Other messages are classification-only even when a name is recognized. This is not an ISO schema support matrix.

Statuses are representative meanings from the bundled dictionary. Acceptance and authorization do not establish settlement; a settlement-completion report must be interpreted with its side, scheme and actual evidence. Unknown status/reason codes remain unknown. Group `PART` requires transaction-level inspection.

Use Decimal arithmetic. Missing amount remains null; mixed-currency economic totals remain null with separate `currency_totals`. A complete message's raw arithmetic sum may be checked against its declared control sum, without FX conversion. If no controls are declared or the relevant amounts are absent, checks remain not evaluated. No tolerance is silently invented.

IBAN mod-97, BIC format and UETR UUID shape are limited consistency checks. They do not prove addressability, ownership, authenticity, scheme compliance, or account status.

Mapping warnings require an explicit cited profile. Do not assert universal 140-character truncation or universal SWIFT-X requirements for all ISO text. No message is repaired or resubmitted here.
