# Adjacent-Skill Handoffs — covenant-compliance-monitor

This skill is a **scheduled, read-only, alert-only** monitor. It produces a cited exception
pack (`run_id`) with per-alert `fingerprint`s and stops. It does **not** adjudicate a breach,
recommend or draft a waiver or amendment, declare default, change a risk rating, or close an
exception. Those are human credit / legal actions, supported by the downstream skills and
human roles below.

## Downstream (route the human reviewer to)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `loan-servicing-exception-resolver` | A confirmed or potential breach / overdue deliverable needs a servicing remedy (cure tracking, waiver or amendment request, reservation of rights) staged for authorized approval and execution | `run_id` + facility + covenant + evidence |
| `credit-memo-drafter` | The exception should be escalated into a credit memorandum / risk-rating re-underwrite for underwriter approval | `run_id` + facility + breached covenant evidence |
| `credit-risk-portfolio-analyzer` | The reviewer needs the portfolio-level credit-risk view (early-warning aggregation, migration, concentration) behind a covenant exception | facility + obligor + breached covenant |
| `financial-spreading-assistant` | The underlying approved spread is stale, disputed, or must be re-spread before the covenant test can be recomputed | facility + test period + line items in question |
| `cashflow-forecaster` | The reviewer wants a forward view of whether headroom will hold next period given the cash-flow trajectory | facility + drivers + current headroom |
| `relationship-manager-client-briefer` | Covenant status must be folded into the commercial relationship brief and borrower outreach planning | `run_id` + facility covenant status |

## Human / specialist handoffs (no catalog skill — route to the right role)

- **Ambiguous or disputed covenant definition** (calculation mechanic, add-back, or defined
  term is unclear, or an amendment changed it) → **loan-documentation and legal counsel** to
  re-interpret the executed agreement and re-baseline the parsed covenant library. The monitor
  never resolves ambiguous legal wording itself.
- **Disposition of a breach** — waiver, amendment, reservation of rights, default declaration,
  risk-rating action, borrower notice → the **credit officer / portfolio manager and credit
  committee** through their entitled systems, never this monitor.

## Upstream (what invokes this skill)

This is a **scheduled monitor** (`aws-fsi-scheduled-agent: read-only-monitoring`): it is
triggered by its schedule (typically at quarter-end / certificate cadence) or an ad-hoc
reviewer run against a specific facility or portfolio — not by another skill. Approved spreads
(often produced upstream by `financial-spreading-assistant`) are an **input**, not a caller.

## Duplicate-execution prevention

- The monitor computes and evidences **exceptions only**; it must not reach a disposition,
  instruct the borrower or a servicer, or take/recommend a waiver, amendment, or default
  action — those belong to the human reviewer and the downstream skills.
- Cross-run **deduplication** (fingerprint vs `open_alerts`) prevents the same persistent
  breach (e.g., one under a negotiated cure period) from being re-raised every scheduled run;
  still-open items remain visible as open rather than being silently cleared.
- Downstream skills consume the `run_id` / alert evidence rather than re-computing covenant
  tests or re-parsing the credit agreement.
