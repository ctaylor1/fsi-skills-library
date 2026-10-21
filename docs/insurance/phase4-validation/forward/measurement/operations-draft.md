# Intake queue window review — decision draft

Fictional Harbor Test Mutual; US-TEST / personal-auto-test. Review date: 2026-09-20. This is an internal draft for named owners, not legal, claims, procurement or deployment approval. Sources are synthetic supplied assertions and were not independently authenticated. No system connection, claim action, customer message or implementation occurred.

Elena Moss should reconcile the episode snapshot with independent queue counts before using it for an operating decision. QUEUE-22 v1 (2026-09-19, raw-evidence.json#/operations) defines episode-v3 and the UTC window [September 18 00:00, September 19 00:00). It includes two episodes open at the start and every arrival. SUP-1 v1 separately supplies accrued cost/labor for unfinished episodes; those amounts do not enter completed-cohort means.

| Flow | Episodes |
|---|---:|
| Opening | 2 |
| Arrivals | 3 |
| Completed | 2 |
| Cancelled | 1 |
| Closing | 2 |

Conservation is 2+3−2−1=2. Independent complete-case opening and closing counts agree. E1 completes after 24 elapsed calendar hours including pre-window age; E3 completes after six hours. Their mean is 15 hours, nearest-rank p95 is 24 hours and both meet the supplied 24-hour illustrative SLA. Two observations provide little tail assurance. This is an operating illustration, not a legal deadline calculation.

Completed-cohort cost is ($36+$12)/2=$24 per completion, and labor is (45+15)/2=30 minutes. Cancelled E4 and open E2/E5 are excluded. These are not fully allocated costs. E2 has aged 30 hours at close and E5 eight hours; neither is silently counted as a completed SLA success. Window-level labor utilization is 12 worked /16 available hours =75%; its basis is the full same-window labor record, distinct from completed-episode direct labor. Native evidence: operations-complete-output.json.

The imperfect packet's supervisor tally says three closing episodes, while the extract still computes two. Operations-imperfect-output.json retains the above extract metrics, emits closing_control_difference=-1, and marks needs-review. They are extract-only calculations until Elena reconciles the discrepancy; the actual queue's completeness is unresolved. Investigate the unmatched closing item, late capture and reopening linkage before claiming the population reconciles. No causal staffing or process-improvement conclusion follows.

A separate realistic variant preserves unknown costs and labor on the two unfinished episodes. Despite complete timing and completed-case costs, the current tool suppresses all window aggregates, including queue counts and utilization. Do not fill unknowns with zero to obtain output. The complete-case run uses separately supplied fictional accrual records instead; it does not repair the raw packet invisibly. This is a practical dependency limitation for real queues with unfinished accounting.
