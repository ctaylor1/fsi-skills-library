# Card lifecycle assessment

Work item: {{request_id}} · As of: {{as_of}} · Participant/jurisdiction: {{scope}}
Draft status: {{status}} · Input digest: {{input_hash}}

## What the evidence establishes

State the actual question and observed outcome. Distinguish recorded events from
verified operating state. Explain which profile/source authority is supplied and
which remains unverified.

| Object type | Opaque identity and links | Reported state | Evidence | Contradiction or gap |
| --- | --- | --- | --- | --- |
| Account / card / token | {{identity}} | {{state}} | {{source}} | {{gap}} |

## Transaction timeline and amounts

| Event and offset time | Authorization / hold / presentment link | Kind | Amount and currency | Source and authority |
| --- | --- | --- | --- | --- |
| {{event}} | {{links}} | {{kind}} | {{amount}} | {{source}} |

For each transaction/currency, explain distinct stage totals. Authorization approval
is not clearing, settlement, funding or posting. Show explicit recorded holds and any
profile-dependent remaining-hold scenario, including allocation or reversal uncertainty.
Do not replace missing amounts with zero or imply a verified available balance.

## Controlled next steps

Describe the proposed action scope and required identity, policy, eligibility,
reviewer and runtime evidence. Show card replacement and token handling separately.
Keep issuer consumer-error, merchant chargeback and normal servicing routes distinct.
Record unresolved issues and native target inputs. Nothing has been changed or executed.
