# Adjacent-Skill Handoffs — mandate-compliance-monitor

This skill is a **scheduled, read-only, alert-only** monitor. It produces a cited exception
pack (`run_id`) with per-alert `fingerprint`s and stops. It does **not** analyze root cause
to disposition, recommend or construct remediating trades, grant cures/waivers, or close
alerts. Those are human compliance / portfolio-management actions, supported by the
downstream skills below.

## Downstream (route the human reviewer to)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `portfolio-exposure-analyzer` | Reviewer needs deeper issuer/sector/factor/look-through exposure detail behind a concentration alert | `run_id` + portfolio + breached bucket |
| `liquidity-stress-analyzer` | A breach or proposed cure raises a liquidity/liquidation-horizon question | portfolio + positions in question |
| `counterparty-exposure-monitor` | The exception concerns counterparty/settlement/derivative limits rather than mandate holdings | portfolio + counterparty scope |
| `portfolio-rebalancing-assistant` | The portfolio manager decides to construct trades to bring the book within limits | breached buckets + limits (human-directed) |
| `best-execution-reviewer` | A flagged proposed trade needs best-execution review before it is worked | `oms` trade id(s) |
| `investment-committee-memo-builder` | An exception needs to be escalated into an IC decision memo | `run_id` + exception evidence |
| `regulatory-change-impact-analyzer` | A regulatory limit itself changed and the rule library must be re-baselined | affected `rule_id`(s) + config version |

Remediation itself — placing/blocking trades, granting a cure or waiver, or closing the
exception — is performed by the **investment-compliance officer and portfolio manager**
through their entitled systems, never by this monitor.

## Upstream (what invokes this skill)

This is a **scheduled monitor** (`aws-fsi-scheduled-agent: read-only-monitoring`): it is
triggered by its schedule (or an ad-hoc reviewer run), not by another skill. A portfolio
manager or compliance officer may also run it on demand against a specific mandate.

## Duplicate-execution prevention

- The monitor computes and evidences **exceptions only**; it must not reach a disposition,
  contact a manager as an instruction, or take/recommend a trade or cure — those belong to
  the human reviewer and the downstream skills.
- Cross-run **deduplication** (fingerprint vs `open_alerts`) prevents the same persistent
  breach from being re-raised every scheduled run; still-open items remain visible as open
  rather than being silently cleared.
- Downstream skills consume the `run_id` / alert evidence rather than re-deriving limits or
  re-screening the whole book.
