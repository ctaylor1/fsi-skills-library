# Adjacent-Skill Handoffs — catastrophe-exposure-monitor

This skill runs on a schedule, produces a deduplicated **alert-queue package** (`run_id`)
with cited exposure/modeled-loss breaches, and stops. It does not decide, price, cede,
reserve, or close anything — those are human and downstream-skill responsibilities.

## Downstream (route the human/reviewer to)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `insurance-underwriting-risk-reviewer` | An accumulation or single-location breach needs an underwriting response (capacity, limit, terms) on a new or renewal risk | `run_id` + breached `alert_key`s + exposed locations |
| `insurance-submission-preparer` | A zone is at/over appetite and new inbound submissions in that zone need tighter intake screening | zone + peril + accumulation status |
| `reinsurance-contract-reviewer` | The manager needs treaty attachment/retention/recovery implications of the modeled event loss (interpretation only) | event modeled-loss range + treaty reference |
| `pc-reserving-analysis-assistant` | A landfalling event's modeled loss should inform reserving/IBNR | `run_id` + event modeled-loss range |
| `claims-triage-assistant` | The event has made landfall and a claims surge needs first-line triage | event id + affected zones |

## Upstream (may trigger this skill)

A **scheduler** invokes this monitor on its cadence (or ad hoc on a new event bulletin);
policy administration, the event feed, and the cat model provide the read-only snapshot.
This is a scheduled monitor (`aws-fsi-scheduled-agent: read-only-monitoring`); no other skill
delegates a decision to it.

## Human / operations handoffs (no skill exists — route in prose)

- **Buying or ceding reinsurance, moving capacity, or committing catastrophe budget** →
  the catastrophe-risk committee and the treaty reinsurance team. The monitor never places,
  binds, or recommends-as-instruction any reinsurance.
- **Binding, declining, or amending a specific policy** → the licensed underwriter via
  `insurance-underwriting-risk-reviewer`; the monitor only flags the exposure.
- **Setting or changing appetite, zone limits, or model assumptions** → the cat-risk model /
  actuarial owner, as a versioned config change — never tuned inside a run.

## Duplicate-execution prevention

- The monitor computes and evidences **breaches only**; it must not reach a disposition,
  contact a producer/insured, or take/recommend an underwriting, reinsurance, or reserving
  action — those belong to the human queue and the named downstream skills.
- Downstream skills consume the `run_id` / `alert_key` package rather than re-monitoring the
  portfolio. Ongoing alerts are carried by `alert_key`, not re-raised as new each run.

## Typed receiver validation

Prepare native receiver input together with `make_handoff` from the bundled insurance contract. Preserve source artifact, object/context and unresolved issues. Invoke `validate_handoff` with the actual receiver input validator; a producer claim of passed validation is insufficient. The receiver separately assesses its domain prerequisites and carries any upstream partial state. This is content binding and schema validation, not permission to act.
