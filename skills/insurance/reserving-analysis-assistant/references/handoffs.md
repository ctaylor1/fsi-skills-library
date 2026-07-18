# Adjacent-Skill Handoffs — reserving-analysis-assistant

This skill is **actuarial analysis drafting**. It prepares source-linked reserve-development,
severity, frequency, large-loss, and uncertainty analyses for a qualified actuary to review,
select, and approve. It does not select or book reserves, opine on adequacy, review
individual claims, model catastrophe accumulation, or interpret reinsurance terms — those
are separate control activities with distinct entitlements.

## Upstream (feeds this skill)

| Upstream source / skill | Provides | Handoff artifact |
| ----------------------- | -------- | ---------------- |
| Claims data mart | Paid & incurred loss triangles by segment | `segment_id` triangles + `valuation_date` |
| `claims-file-reviewer` | Claim-level context and completeness for large or disputed claims that affect a triangle | reviewed claim references |
| `catastrophe-exposure-monitor` | Catastrophe / large-loss exposure tags and accumulation context | large-loss register + cat tags |
| Actuarial parameter set | Approved methods, tail factors, large-loss thresholds (versioned) | `dataset_version` |

## Adjacent — do NOT use this skill for (route instead)

| If the request is… | Route to |
| ------------------ | -------- |
| Reviewing an **individual claim** file, its reserve adequacy, or completeness | `claims-file-reviewer` |
| **Catastrophe** PML / accumulation modelling or monitoring cat exposure | `catastrophe-exposure-monitor` |
| Interpreting **reinsurance treaty** terms or ceded-reserve logic | `reinsurance-treaty-interpreter` |
| Independent **control / valuation review** of the reserve estimate | `valuation-reviewer` |
| Packaging the reviewed results into **management or board reporting** | `management-reporting-packager` |
| **Booking** the selected reserve at close / journalising to the GL | `month-end-close-orchestrator` |

## Downstream (human, not a skill)

The draft exhibit goes to a **qualified (appointed) actuary**, who reviews the method and
factors, **selects** the carried reserve, assesses adequacy, and — under separate authority
— issues any Statement of Actuarial Opinion. Booking of the selected reserve and any
regulatory filing are performed by finance / the appointed actuary outside this skill. This
skill emits a `segment_id`-keyed draft with `actuarial_review_required` and
`reviewer_signoff_required` flags; it must not perform selection, booking, opinion, or filing.

## Duplicate-execution prevention

- This skill **does not** select reserves, book, opine, review individual claims, or model
  catastrophe accumulation — those belong to the routes above or to the appointed actuary.
- An exhibit carries the `dataset_version` and `valuation_date` so a reviewer works one
  authored draft rather than re-deriving the triangles.
- A `needs-data` or `anomaly-flagged` segment is resolved by a human (obtain data / review
  the anomaly), never force-packaged into an indication.
