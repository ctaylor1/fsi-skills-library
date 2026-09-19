# Domain rules and limits

## Calculation contract
Opening available = balance - held - outstanding reservations. At an outgoing event, subtract obligation × stress multiplier, then release its linked reservation. At an eligible incoming event, add its amount unless the scenario removes it. Held amounts must exclude the separately supplied reservations. Peaks preserve chronological path; an ending surplus cannot hide an earlier shortfall. Same-instant obligations precede inflows conservatively.

Firm events are caller assertions with source lineage, not authenticated commitments. All outflows, including forecasts, consume capacity conservatively; forecast inflows do not fund it. Opening snapshot covers events at or before window_start, so separately supplied events at/before start are flagged as potential double counting. Events after window_end are not included but any opening reservations remain held. Unknown balance/holds/event amounts, misbound reservations, duplicate economic IDs or entity/currency conflicts suppress positions for affected accounts.

This is payment funding decision support, not institution-wide ALM, intraday credit approval or a liquidity regulatory ratio. Stress scenarios are deterministic assumptions. Profiles are orientation only and expire under their review dates; no specific contractual cap, bank holiday window or intraday-credit entitlement is built into the model.
