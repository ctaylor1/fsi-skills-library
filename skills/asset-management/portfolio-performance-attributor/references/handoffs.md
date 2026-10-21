# Adjacent-Skill Handoffs — portfolio-performance-attributor

Building the performance attribution (this skill) is a **separate activity** from writing the
portfolio narrative, from assembling a client/committee deliverable, and from the methodology
sign-off and compliance/marketing review. This skill emits a durable `attribution_id` and a cited
attribution manifest; it does not perform the downstream authors' or a human reviewer's work, and
it never issues advice, a performance claim, or a delivery.

## Downstream (this skill hands off to)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `investment-commentary-builder` | The attribution feeds a written performance/portfolio commentary | `attribution_id` + effect totals + segment attribution + citations |
| `fund-fact-sheet-builder` | The attribution / performance figures populate a fund fact sheet | `attribution_id` + portfolio/benchmark returns + effect totals |
| `investment-committee-memo-builder` | The attribution is included in an IC review pack | `attribution_id` + rendered attribution section + citations |
| `client-review-preparer` | The attribution is placed in a client review pack | `attribution_id` + rendered attribution section + open items |

## Upstream (feeds this skill)

| Upstream skill | Provides |
| -------------- | -------- |
| `portfolio-holdings-summarizer` | Position holdings and segment weights for the period |
| `portfolio-exposure-analyzer` | Sector/factor/currency exposure and classification used for the segmentation |
| `investment-mandate-reviewer` | Mandate / benchmark policy context and disclosure requirements |

## Non-catalog handoffs (human / licensed)

- **Performance-methodology sign-off** → the Head of Performance Measurement / performance team
  approves the model, segmentation, and reconciliation. No catalog skill signs off attribution
  methodology.
- **Compliance / marketing review (SEC Marketing Rule, Rule 206(4)-1)** → compliance and marketing
  review and approve before any advertising, client, or external use. This skill never delivers or
  makes a performance claim.
- **Risk-model estimation and unsupported attribution/linking conventions** → the quant / risk performance team. The no-extension method covers single-period arithmetic Brinson-Fachler. Use the explicit specialist extension for supplied-factor contributions and its documented chronological linking method.
- **Investment recommendations / advice** → the portfolio manager and the client's licensed
  advisor. Attribution explains realized return; it never advises.

## Duplicate-execution prevention

- This skill **does not** write the commentary, build the fact sheet or committee/client pack, sign
  off the methodology, run the compliance/marketing review, or estimate a risk model —
  those belong to the named skills or to a human.
- Downstream skills consume this skill's `attribution_id` / manifest rather than recomputing the
  attribution.
- A segment missing returns is left as a `needs-data` open item (its weight unattributed) for human
  resolution, never silently dropped or filled with an assumed return.

