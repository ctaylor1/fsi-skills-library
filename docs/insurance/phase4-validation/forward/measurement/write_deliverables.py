from pathlib import Path
import json,hashlib,shutil
P=Path('/tmp/insurance-p4-forward-measurement');R=Path('/Users/taylor/DevRepo/Skills/fsi-skills-library')
paths={'architecture':'enterprise-functions-technology/solution-architecture-planner','automation':'enterprise-functions-technology/workflow-automation-assessor','data':'data-ai-model-governance/data-product-value-evaluator','operations':'finance-operations/operations-performance-analyzer'}
for kind,path in paths.items():
 t=P/'package-snapshot'/kind;t.mkdir(parents=True,exist_ok=True)
 for name in ['SKILL.md','references/schema.md','references/domain-rules.md','scripts/domain.py','scripts/design_support.py','scripts/workflow_foundation.py']:
  s=R/'skills'/path/name
  if s.exists():shutil.copy2(s,t/name.replace('/','__'))
common='''Fictional Harbor Test Mutual; US-TEST / personal-auto-test. Review date: 2026-09-20. This is an internal draft for named owners, not legal, claims, procurement or deployment approval. Sources are synthetic supplied assertions and were not independently authenticated. No system connection, claim action, customer message or implementation occurred.\n\n'''
(P/'architecture-draft.md').write_text('# Assisted intake architecture — decision draft\n\n'+common+'''Mira Chen should review the proposed three-component sandbox design, its exact payload contract and its failure tests before any implementation decision. ARC-17 v3 (2026-09-18, raw-evidence.json#/architecture) provides component options, responsibility and monthly cost assumptions. SUP-1 v1 (2026-09-19, supplemental-evidence.json#/design_proposal) supplies a fictional design proposal; it does not describe an installed connector. PROFILE-architecture v1 governs only this sandbox method and scope.

```mermaid
flowchart LR
  P[Portal: capture deidentified intake] -->|I1 proposed draft write| D[Draft service: validate fields]
  D -->|I2 proposed draft write| Q[Review queue: hold for examiner]
  Q --> H[Examiner accepts or corrects draft]
```

| Component / owner | Proposed option / alternative | Tradeoff | USD per stated month |
|---|---|---|---:|
| Portal / Mira Chen | Web form / examiner keyed form | Faster capture; browser dependency | 280 |
| Draft service / Noah Vale | Stateless rules / manual checklist | Consistent checks; rules maintenance | 420 |
| Review queue / Elena Moss | Durable queue / shared task list | Replayable drafts; queue administration | 160 |

The supplied total is $860 per September 2026 budget month at the declared sandbox load, not a production quote or fully allocated cost. Edge, service and queue are named failure domains, not evidence that their infrastructure is independent.

Both proposed interfaces use intake-draft-v1: token, capture time, supplied fields and missing fields. I1 connects portal to draft service; I2 connects draft service to review queue. Contracts require mutual service identity, sandbox draft-create permission, TLS and encryption at rest, a five-second timeout, at-least-once delivery and no more than three attempts. The intake token is the trace and idempotency key. Elena Moss owns acceptance. Readback must return one matching draft ID; an uncertain receipt stops the producer until examiner reconciliation. Failed intake stays visible in the manual examiner queue. This defines a proposal; no endpoint is live or approved. RET-3 supplies a fictional 30-day sandbox deletion rule, not a real institution retention mandate.

R1 requires draft-service p95 response latency <=700 ms at sandbox-40-requests-per-minute-2KB-v1. The observed 640 ms on September 18 meets that one requirement; it says nothing about end-to-end latency, availability, production throughput or provider conformance. Native evidence: architecture-complete-output.json, results.requirement_fit and supplied_period_cost.

In the imperfect packet, the observed workload is 10KB, and the queue cost is unknown. Architecture-imperfect-output.json correctly leaves fit and total cost null. Do not reuse 640 ms as evidence for the 2KB requirement, or substitute zero for the quote.

Acceptance remains with Mira (component and workload scope), Noah (permission, replay and recovery tests), Elena (manual route and review operating procedure), and the institution's privacy owner (retention and data minimization). Test interrupted receipt, duplicate submission, full queue and unavailable identity service using the exact required workload. Provider selection and deployment remain open.
''')
(P/'automation-draft.md').write_text('# Assisted intake pilot economics — decision draft\n\n'+common+'''Elena Moss should defer an economic pilot recommendation on the supplied scenarios: both annual cash projections are negative, even though examiner capacity is freed. PAIR-11 v2 (2026-09-18, raw-evidence.json#/automation) is the full purposive four-case sample under assist-intake-v2. Same cases were replayed in fixed baseline-then-candidate order. Candidate labor includes review, exceptions and rework; nonlabor charges exclude that labor. Independent examiner labels are supplied. Learning and order effects remain possible; this is descriptive, not causal evidence.

| Observed mean per case | Baseline | Assisted candidate |
|---|---:|---:|
| Human minutes | 20 | 14 |
| Nonlabor USD | 1 | 3 |
| Elapsed seconds | 1,200 | 885 |
| Error fraction | 1/4 | 1/4 |

The mean six-minute saving includes P3, where candidate work takes 14 versus 10 minutes and introduces an error. The two error populations differ: baseline P2, candidate P3. Equal rates do not establish equal harm. The supplied ceiling is 25%; meeting it in four purposive cases is insufficient production quality evidence.

| Projection | Capacity only | 50% cash realization |
|---|---:|---:|
| Annual volume × eligibility | 12,000 × 50% = 6,000 | 6,000 |
| Capacity hours freed | 600 | 600 |
| Capacity value at $48/hour | $28,800 | $28,800 |
| Realizable labor cash assumption | $0 | $14,400 |
| Added nonlabor cost | $12,000 | $12,000 |
| Annual fixed cost | $6,000 | $6,000 |
| Annual cash net | **-$18,000** | **-$3,600** |
| Payback on $9,000 implementation | None | None |

The break-even realization assumption is $18,000/$28,800 = 62.5%; a positive net requires more than that at unchanged volume, costs and six-minute savings. This is sensitivity arithmetic, not evidence that layoffs, attrition or avoided hiring can realize it. Do not add capacity value again as a cash benefit. Native evidence: automation-complete-output.json; pilot_candidate=false.

SUP-1 v1 documents six supplied sandbox control categories: examiner review, privacy, permission scope, failure recovery, auditability and evaluation quality. PAIR-11 also records stop-routing and duplicate replay. All complete-case tests pass as fictional observations, not authenticated production control acceptance. In the imperfect packet, P3 rework timing is unknown and duplicate replay produces two drafts. The native artifact withholds means, scenarios and recommendation. Preserve the P3 record, repair duplicate handling, retime the whole paired candidate case and obtain owner review before reevaluation; do not drop failed cases.

A proposed next measurement is a larger balanced-order sandbox run with error severity and end-to-end examiner time recorded. Elena owns the decision to commission it; Ada Soto owns comparison design; Noah Vale owns failure/replay correction. No pilot activation is authorized here.
''')
(P/'data-draft.md').write_text('# Licensed enrichment benchmark — decision draft\n\n'+common+'''Ada Soto should request a broader time-correct benchmark before procurement evaluation. BENCH-9 v4 (2026-09-18, raw-evidence.json#/data) supplies six deidentified historical cases. The purpose is offline intake-completeness triage: a positive truth label means a completed examiner audit confirmed additional documentation was needed. Compare fixed rules-v5 against rules-plus-context-v1; predictions do not decide coverage or claim payment.

Fictional RoadContext license LIC-8-v2 permits this supplied purpose during September 1–30; Jo Lane is the named licensing steward. Licensed sandbox attributes are deleted after benchmark signoff under the supplied rule. The native usable-license flag is an assertion check, not legal validation or procurement permission. The review profile and license apply only to US-TEST personal-auto-test scope.

The four matched attributes were available September 9, before the September 10 decisions. Outcomes matured September 15, before this September 20 review. All six cases remain in the benchmark, including unmatched D5 and D6. Their augmented fallback predictions and costs are explicitly supplied, and identical to their baseline values; this was not assumed from nonmatch.

| Counts / measure | Baseline | Augmented |
|---|---:|---:|
| True positive | 1 | 2 |
| True negative | 2 | 2 |
| False positive | 1 | 1 |
| False negative | 2 | 1 |
| Precision | 50% | 66.67% |
| Recall | 33.33% | 66.67% |

Coverage is 4/6 = 66.67%. Supplied total outcome costs fall from $240 to $180, a $60 observed reduction ($10 per original case). D4 worsens by $30; D1 and D2 improve by $60 and $30 respectively. Costs exclude separate license/runtime charges. This is a paired descriptive comparison, not demonstrated causal uplift or fairness acceptance. Source and native result: data-complete-output.json.

Annual value is unknown. The sample is purposive; no representative annual volume or cost basis was supplied. The optional projection was explicitly declined (projection=null). The additional unknown-projection variant retains that unresolved projection record and correctly preserves observed metrics while leaving annual net null; its false license_usable_for_stated_purpose flag is misleadingly affected by unrelated projection gaps and must not be read as a license revocation.

In the imperfect packet, D1 availability is September 11, after its decision. Data-imperfect-output.json correctly blocks the comparison. Do not silently delete D1: reconstruct genuinely available attributes, rerun both frozen versions on the same six-case population, then rescore with Ada's review. Jo must verify real commercial rights before any real data access. Provider selection remains open.
''')
(P/'operations-draft.md').write_text('# Intake queue window review — decision draft\n\n'+common+'''Elena Moss should reconcile the episode snapshot with independent queue counts before using it for an operating decision. QUEUE-22 v1 (2026-09-19, raw-evidence.json#/operations) defines episode-v3 and the UTC window [September 18 00:00, September 19 00:00). It includes two episodes open at the start and every arrival. SUP-1 v1 separately supplies accrued cost/labor for unfinished episodes; those amounts do not enter completed-cohort means.

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
''')
