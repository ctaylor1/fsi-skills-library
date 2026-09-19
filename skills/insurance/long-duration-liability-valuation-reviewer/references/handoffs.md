# Routing and durable handoffs

| Adjacent skill | Routing boundary |
| --- | --- |
| `insurance-experience-study-builder` | Route underlying mortality/lapse experience investigation. |
| `life-annuity-pricing-modeler` | Route prospective product cashflow pricing; valuation balances are not automatically pricing cashflows. |
| `insurance-alm-scenario-analyzer` | Map appropriate liability payments into consistent ALM scope; premiums need separate treatment because ALM accepts payments only. |

Triage is selection and gap identification; investigation is the source-bound native analysis in this package. Never execute a second skill's workflow merely because its source artifact is attached. Transfer case_id, as_of, source/version/section inventory, original artifact, method, unit/currency/basis, population/horizon, unresolved issues and requested receiver output. Map actual receiver fields and invoke its actual validator. The evidence contract retains upstream uncertainty. Changed capacity, object, represented party, jurisdiction or product requires a source-bound context mapping as documented in insurance-foundation.md. A mapping does not convert intensity to annual probability, premiums to liability payments, ceded to assumed economics, or cashflow margin to a reserve. No authority is granted by handoff.
