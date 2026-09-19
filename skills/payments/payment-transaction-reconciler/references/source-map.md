# Source responsibilities

| Source | Evidence role | Limits |
| --- | --- | --- |
| Gateway / merchant order record | Observed attempt/capture/order amount and mapped state | Does not establish cash received |
| Processor / acquirer record | Processing/clearing result and its stated amount | Does not establish bank cash or ledger correctness |
| Bank record | Observed cash amount and value date | Does not by itself explain fee, timing or upstream differences |
| Internal ledger | What was recorded | Does not justify itself or supply missing bank evidence |
| Versioned matching configuration | Expected sources, tolerance and comparison basis | Cannot override source facts |

Cite every supplied record as source:source_ref@date and retain its source ID. Scope source
retrieval by legal entity, account, currency, settlement cycle and as-of. Investigate
conflicting observations; do not silently pick a higher-ranked amount as a balancing target.
The scripts use local JSON only; read-only retrieval, lifecycle mapping, entity resolution
and evidence authentication are deployment integrations, not implemented connectors.
