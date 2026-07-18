---
name: best-execution-reviewer
description: >-
  Evaluate execution quality against the firm's best-execution policy and applicable
  obligations (e.g. MiFID II RTS 27/28, FINRA Rule 5310, SEC Reg NMS 605/606): price versus
  benchmark, arrival-to-execution speed, venue selection and routing, fill rate, explicit
  and implicit cost, and undocumented exceptions — then package the findings with cited
  evidence and a suggested review disposition for the best-execution committee. Use when a
  committee member or compliance analyst asks to review execution quality, check routing or
  venue selection, find execution outliers versus benchmark, or package best-ex exceptions
  with evidence. HARD BOUNDARY: decision-support findings and recommendations only; NEVER
  makes a best-execution or compliance determination, decides whether an execution was best
  execution, closes or dispositions an exception or case, files a regulatory report, or
  writes a system of record — those require human adjudication and approval.
license: MIT
compatibility: Amazon Quick Desktop; requires OMS/EMS, market & reference-data, post-trade/clearing, surveillance, communications-archive, and regulatory-reporting MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Capital Markets"
  aws-fsi-skill-type: "Analysis and evaluation skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Analyze & review"
  aws-fsi-agent-pattern: "Interactive decision-support copilot"
  aws-fsi-delivery-wave: "Wave 3 - regulated casework"
  aws-fsi-action-mode: "Read-only analysis"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Highly Confidential (customer NPI/PII)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Capital Markets operations & compliance"
  aws-fsi-primary-user: "Best-execution committee / compliance analyst"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Best-Execution Reviewer

## Purpose and outcome
Given a population of client executions and the firm's versioned best-execution policy
thresholds, run a **deterministic best-execution review** and produce a **findings pack**:
each finding (adverse price versus benchmark, material price miss, slow execution, low fill
rate, high cost, off-policy venue, undocumented exception) is named, explained in plain
language, and attached to cited OMS/EMS and market-data evidence. The pack carries a
**suggested review disposition** (Pass / Review / Escalate) derived deterministically from
the fired-finding set. A successful output lets a best-execution committee member or
compliance analyst decide what to escalate, remediate, or clear — the best-execution
determination, and any case, filing, or system-of-record action, **remains human**.

## Use when
- "Review execution quality for these orders / this desk / this period."
- "Check routing and venue selection against our approved-venue list."
- "Which executions are outliers versus the arrival benchmark (price, speed, cost)?"
- "Assess best execution for this sample and give me the evidence."
- "Package this month's best-ex exceptions with cited evidence for committee review."

## Do not use
- The user wants a **best-execution or compliance determination** ("were we best-ex?",
  "declare this compliant", "confirm no breach"), an **exception/case closure or
  disposition**, or a **regulatory filing/amendment** → out of scope. Provide evidence and
  route to the best-execution committee / a licensed compliance officer (see Human approval).
- The anomaly suggests **potential market abuse or manipulation** (spoofing, front-running,
  wash trades) rather than execution quality → `market-surveillance-alert-investigator`
  (first-line triage: `surveillance-alert-triager`).
- The real question is **regulatory transaction-report quality** (completeness, timeliness,
  identifiers, RTS 22 fields) → `transaction-reporting-quality-checker`.
- The concern is a **bond/OTC price reasonableness** valuation review, not execution quality
  → `fixed-income-pricing-reviewer`.
- The user just wants a **single trade confirmation explained** in plain language →
  `trade-confirmation-explainer`.
- The issue is a **settlement fail / trade break** across systems → `post-trade-settlement-monitor`
  (surface) or `trade-break-resolver` (approved repair).
- The review turns on **trader communications / conduct** evidence →
  `communications-compliance-reviewer`.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill emits a findings pack with a
durable `review_id`; downstream surveillance, reporting-quality, pricing, and settlement
skills consume it. It must not duplicate their determination, filing, or repair steps, and
it never performs the committee's adjudication.

## Inputs and prerequisites
- The **review scope** — desk / order-type / client-classification and an **as-of date** or
  period.
- **Executions** (front office / OMS as the position of record) — each with `execution_id`,
  `order_id`, `symbol`, `side`, `order_type`, `order_qty`, `executed_qty`, `arrival_ts`,
  `execution_ts`, `execution_price`, `benchmark_price` + `benchmark_type`, `venue`,
  `commission`, an `exception_flag` with an optional `exception_rationale_ref`, and a
  `source_ref` citation. Schema: [scripts/validate_input.py](scripts/validate_input.py).
- The **versioned best-execution policy config** — price tolerance and material bps,
  latency ceiling, minimum fill rate, cost cap, and the effective approved-venue list.
  See [references/domain-rules.md](references/domain-rules.md).
- Read access to OMS/EMS, market & reference data, and (for exception rationale) the
  communications archive.

## Source hierarchy
See [references/source-map.md](references/source-map.md). The **front-office execution
record** is the position of record for what was done; **market & reference data** supplies
the benchmark and venue taxonomy; the **versioned policy config** supplies thresholds and
the approved-venue list; the **communications archive** evidences a documented exception
rationale. When a record and market data conflict, cite both and flag it — never silently
trust one side. Every finding cites the specific execution rows and the rule it failed.

## Workflow
1. **Scope & load** — confirm the desk/period, client classification, and policy version;
   load the executions and the benchmark/venue reference data; validate structure with
   `validate_input`.
2. **Evaluate (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py) to evaluate each
   execution against the policy thresholds and compute the findings: price-vs-benchmark and
   material price miss, arrival-to-execution latency, fill rate, explicit + implicit cost,
   venue-policy, and undocumented exception. Each fired finding returns its evidence rows and
   citations. Findings are **explainable**, not an opaque score.
3. **Assemble evidence** — for each finding, attach the specific execution rows, the
   benchmark used, and the threshold/rule it failed, with citations.
4. **Suggest disposition** — map the fired-finding set to a review band
   (Pass / Review / Escalate) per the documented deterministic mapping. This is a triage
   suggestion for the committee, explicitly **not** a best-execution determination.
5. **Write the pack** — plain-language explanation per finding + the evidence + the suggested
   disposition + the **false-positive checks** to run before escalating + `not_evaluable`
   gaps + the standing disclaimer.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py)
after. The output check confirms: every fired finding has evidence + citation, every fired
finding type is recognized, the disposition maps deterministically from the fired findings,
**no regulated decision / closure / disposition / filing / attestation language is present**,
the standing disclaimer is present, and false-positive prompts are included when any finding
fired. **Fail closed** on any miss.

## Human approval
`required` (R3 decision support). Human adjudication by the best-execution committee (and, for
any regulatory step, a licensed compliance officer) is **required before** any best-execution
or compliance determination, exception/case closure or disposition, remediation instruction to
a desk, regulatory filing or amendment, or system-of-record change. The skill only reads and
evidences; it stages nothing for execution and never records a decision. No approval is needed
for the analyst's own read of the pack.

## Failure handling
- **No benchmark on an execution** → price and cost checks for that row are `not_evaluable`;
  never assert an execution beat or missed the benchmark without one.
- **Missing arrival/execution timestamps** → latency is `not_evaluable`; do not assert a speed
  finding without the timestamps to prove it.
- **No effective approved-venue list** → `venue_off_policy` is not enforced; say so rather than
  implying every venue is on-policy.
- **Ambiguous / duplicate `execution_id` or `order_id`** → surface the ambiguity; do not guess
  the pairing or the order the fills belong to.
- **Stale reference data or policy config** → cite the version used; if the effective version
  is uncertain, fail closed and ask.
- **Tool timeout** → return the findings computed so far with a clear "incomplete" flag and the
  unprocessed remainder; do not imply the untested executions are clean.

## Output contract
1. **Summary** — scope, as-of/period, population count, fired-finding count, and the suggested
   disposition band.
2. **Findings** — per fired finding: name, plain-language reason, the threshold/rule, and cited
   evidence rows (execution + benchmark).
3. **Not evaluable** — checks that could not run and why (missing benchmark, timestamps, venue
   list, commission).
4. **False-positive checks** — items to verify before escalating (benchmark timing/source,
   order type & client instruction, market conditions, venue-list version, documented
   exception, order size / working strategy).
5. **Machine-readable** — findings + evidence + `review_id` for downstream skills and the
   committee record.
6. **Standing disclaimer** — "Best-execution review evidence only; not a best-execution or
   compliance determination. No case has been closed, no exception has been dispositioned, no
   filing has been made, and no system of record has been updated."
See [references/controls.md](references/controls.md).

## Privacy and records
Execution and order data is **Highly Confidential** and can include client identifiers (NPI/
PII). Minimize client identifiers in output to what evidences a finding; mask or reference
rather than reproduce account/client numbers. Retain the findings pack + citations + policy
version per records policy; log the read and any approval to deliver into the committee record.
Never exfiltrate execution or client data.

## Gotchas
- **A finding is not a determination.** A high finding count justifies review *priority*, never
  a "we did / did not achieve best execution" conclusion — that is the committee's decision.
- **Benchmark choice drives everything.** Arrival mid, NBBO/EBBO, and interval VWAP answer
  different questions; a price "miss" versus the wrong benchmark is a false positive. Confirm
  the benchmark matches the order's decision time and instrument convention.
- **Best execution is multi-factor, not price-only.** For retail, price/cost weigh heavily; for
  professional/illiquid orders, size, likelihood of execution/settlement, and speed can justify
  a worse headline price. Do not reduce best-ex to a single bps number.
- **Client instructions and order type change the standard.** A limit or client-directed order
  may legitimately show partial fills or off-touch prices; the false-positive checks exist for
  this.
- **An exception is not misconduct.** An undocumented exception is a *records* finding — it
  means the rationale was not on file, not that the route was wrong. Route conduct questions to
  the communications reviewer, not a conclusion here.
- **Config is a versioned contract.** Thresholds and the approved-venue list come from the
  versioned policy effective on the trade date, never hard-coded to one desk or day.
