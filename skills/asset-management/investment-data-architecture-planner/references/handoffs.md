# Reuse and adjacent ownership

The native adapter requires `solution-architecture-planner` input/output for generic components, interfaces, requirements and cost basis. It optionally consumes `data-product-value-evaluator` for supplied commercial/utility evidence. Canonical implementations are generated into this package with version/hash pins; they are not separately maintained AM copies. Any shared findings remain open in the AM draft. The original shared artifact stays detached from the AM outward-facing result.

AM additions are semantic grain, source namespace, investment book/benchmark contracts, point-in-time assertions and access/monitor evidence. Use the following receivers only with their actual native schema and explicit field mapping:

| Receiver | Handoff |
| --- | --- |
| investment-data-quality-reviewer | Source snapshot or vendor-comparison input and open data-quality issues; this planner does not choose authoritative field values. |
| investment-reference-data-reviewer | Exact instrument attributes and disputed identifiers; production identity matching remains outside this planner. |
| investment-platform-modernization-planner | Validated semantic contract, point-in-time tests, source/permission requirements and recovery obligations for parallel-run planning. |
| investment-ai-workflow-designer | Eligible licensed sources, intended use/audience and known-history constraints for model/tool evaluation. |
| data-lineage-documenter | Reviewed source-to-field transformation mapping with versions and owner; run that receiver's real input validator. |

Do not forward only a hash or wrap this output as if it were the receiver's input. Preserve object, review/knowledge dates, units, source links, unresolved issues and requested decision. A differing object/date/currency requires a separately reviewed mapping; the bounded shared adapter deliberately rejects mismatched contexts. A draft architecture does not grant source access, permission to disclose, production deployment or booking authority.
