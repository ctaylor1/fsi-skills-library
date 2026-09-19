# Sources and applicability — reviewed 2026-09-17

## Supplied evidence hierarchy
1. Current engagement records establish the capacity and jurisdiction. The applicable
   versioned service and priority policy specifies cadence, effort and escalation owner.
2. Dated household roster and assignment records support population and ownership;
   completed-review records support history; client statements support attributed signals.
3. Owner working-time and unrelated-commitment records establish available minutes,
   with explicit completeness and overlap review for the selected horizon.
4. Practice accounting and custodian period records support economic components and
   a reconciled bridge. Record definitions, scope and period before combining data.

The program has no approved live connector. All registry sources require source_id,
reference, owner, as_of and valid_until; `source.as_of <= request.as_of <= valid_until`.
Use a current certified snapshot for historical observations: a September 17 snapshot
can contain a June completed-review date. Do not relabel an old source as current.
Every material row and policy rule cites its source IDs. Missing item citations are
findings; stale/future/malformed source registry entries stop processing. Supplied
metadata demonstrates attribution and reproducibility, not authenticity or approval.

Preserve discrepancies as upstream issues with originating artifact IDs and source
links. A resolved issue needs attributed resolution evidence and nonfuture date;
changing a status string alone cannot clear it. The fixture policy and sources are
explicitly synthetic and must never be adopted as a firm's policy.

## Primary professional context
These sources inform the boundary; they do not prescribe this package's cadence,
priority ranks, staffing minutes or accounting definitions.

| Source | Relevant context | Applicability limit |
| --- | --- | --- |
| [SEC Commission Interpretation Regarding Standard of Conduct for Investment Advisers, IA-5248](https://www.sec.gov/rules/interp/2019/ia-5248.pdf), issued June 5, 2019 | Adviser care and loyalty; the nature of an advisory relationship affects monitoring obligations. | Do not turn an illustrative service interval into a universal legal frequency. Qualified reviewers determine the actual engagement obligations. |
| [FINRA Rule 2090, Know Your Customer](https://www.finra.org/rules-guidance/rulebooks/finra-rules/2090) | Member firms use diligence to know and retain essential customer facts, including those relevant to servicing accounts. | Member-firm context; this tool does not perform KYC, approve accounts or assert that every relationship has an annual-review rule. |
| [SEC staff bulletin on conflicts of interest](https://www.sec.gov/about/divisions-offices/division-trading-markets/broker-dealers/staff-bulletin-standards-conduct-broker-dealers-investment-advisers-conflicts-interest), August 3, 2022 | Compensation and other incentives may create conflicts requiring attention under applicable conduct standards. | Staff guidance, not a standalone new rule. Practice economics cannot establish that an action serves a client. |

Recheck applicable sources and firm policies before production release and whenever
the jurisdiction, capacity or service agreement changes. The metadata recertification
date is a future review target, not evidence that a compliance reviewer signed off.
