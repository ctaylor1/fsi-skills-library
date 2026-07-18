# Adjacent-Skill Handoffs — valuation-reviewer

This skill produces a cited **valuation-review pack** (`review_id`) and stops. It does not
sign off a valuation, approve an override, post a value, or validate the pricing model
itself. It routes the human reviewer to the right next step.

## Downstream (route the human/reviewer to)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `fixed-income-pricing-reviewer` | The instrument is fixed income and needs a deep pricing review of marks, comparables, spreads, and liquidity adjustments | `review_id` + instrument + IPV evidence |
| `model-validation-assistant` | The concern is the **pricing/valuation model itself** (conceptual soundness, data, performance, limitations) rather than one mark | `review_id` + model reference |
| `model-risk-documenter` | A governed model / validation-evidence documentation pack must be assembled or updated | `review_id` + findings |
| `gl-reconciler` | The reported/carrying value does not tie to the subledger or system-of-record balance (a break, not a valuation question) | instrument + period + balances |
| `audit-evidence-packager` | The reviewed valuation evidence must be indexed, redacted, and packaged for audit with chain of custody | `review_id` + cited evidence |

## Upstream (may produce this skill's inputs)

`dcf-modeler`, `three-statement-model-builder`, `merger-model-builder`, and
`lbo-model-builder` build the models whose outputs this skill reviews; `financials-normalizer`
standardizes issuer/deal financials into the inputs a valuation consumes. This skill reviews
those outputs — it does not rebuild the model.

## Human / governance handoffs (no skill performs these)

- **Valuation Control Committee / independent price-verification governance** — the only
  authority that may *sign off* a valuation, accept an IPV breach, or set the fair-value-
  hierarchy classification. Escalate high-severity findings here.
- **Model Risk Management** — owns formal model approval and revalidation decisions.
- **Controller / CFO delegate** — authorizes any override or adjustment and any posting to
  the system of record.

## Duplicate-execution prevention

- This skill computes and evidences **findings only**; it must not reach a sign-off, approve
  an override, or post a value — those belong to the human reviewer, the committee, and the
  authorized system.
- Downstream skills reuse the `review_id` evidence rather than recomputing the findings.
