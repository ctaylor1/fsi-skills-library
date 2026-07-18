# Adjacent-Skill Handoffs — best-execution-reviewer

This skill produces a cited **best-execution findings pack** (`review_id`) and stops. It does
not adjudicate best execution, close or disposition an exception, file or amend a regulatory
report, repair trade records, or investigate conduct.

## Downstream (route the human/reviewer to)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `market-surveillance-alert-investigator` | A finding points to potential market abuse (spoofing, front-running, wash trades) rather than execution quality — first-line `surveillance-alert-triager` | focal executions + evidence |
| `transaction-reporting-quality-checker` | The real defect is regulatory transaction-report quality (completeness, timeliness, RTS 22 fields), not execution quality | executions + period |
| `fixed-income-pricing-reviewer` | The concern is bond/OTC price reasonableness / valuation, not order execution | instrument + price refs |
| `trade-confirmation-explainer` | The user actually wants a single execution/confirmation explained in plain language | execution ref |
| `post-trade-settlement-monitor` | Likelihood-of-settlement or a settlement fail is the driver, not price/venue | executions + settlement refs |
| `trade-break-resolver` | A finding is really a trade-record break across systems needing an approved, lineage-tracked repair (R4) | `review_id` + break refs |
| `communications-compliance-reviewer` | The exception turns on trader communications / conduct evidence | order_id + exception refs |

## Upstream (may call this skill)

`transaction-reporting-quality-checker` routes here when the true question is execution quality
rather than reporting quality; a best-execution committee member or compliance analyst also runs
this skill interactively against a sampled population. A scheduled monitor is **not** used here
(this skill is interactive, `aws-fsi-scheduled-agent: no`).

## Human / licensed-specialist handoff (no catalog skill)

The **best-execution determination itself**, any **exception/case closure or disposition**, any
**remediation instruction** to a desk or a routing change, and any **regulatory filing,
amendment, or self-report** are performed by the firm's **best-execution committee** and a
**licensed compliance officer** — there is no skill in the library that adjudicates best
execution or files a regulatory report, and this skill must never do so. It supplies cited
evidence and a suggested disposition for that human adjudication.

## Duplicate-execution prevention

- This skill computes and evidences **findings only**; it must not adjudicate, close, file,
  repair, or investigate conduct — those belong to the humans and the downstream skills above.
- Downstream skills and the committee reuse the `review_id` evidence rather than recomputing the
  best-execution checks.
