# Adjacent-Skill Handoffs — key-risk-indicator-monitor

This skill is a **scheduled, read-only, alert-only** monitor. It produces a cited exception
pack (`run_id`) with per-alert `fingerprint`s and escalation commentary, then stops. It does
**not** adjudicate a breach, accept a risk, grant a waiver, change a limit/appetite, change a
risk or control rating, or close an incident. Those are human risk-governance actions,
supported by the downstream skills and human roles below.

## Downstream (route the human reviewer to)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `operational-risk-event-analyzer` | An operational KRI breach is linked to a loss event / incident that needs deep analysis and an event record | `run_id` + KRI + linked incident id |
| `credit-risk-portfolio-analyzer` | A credit KRI breach (delinquency, PD migration) needs the portfolio-level credit-risk view behind it | `run_id` + KRI + affected book |
| `liquidity-risk-scenario-analyzer` | A liquidity KRI breach (e.g., LCR floor) needs a liquidity/liquidation scenario modeled | `run_id` + KRI + observation |
| `third-party-risk-assessor` | A third-party/vendor KRI breach warrants a vendor (re)assessment | `run_id` + KRI + third-party id |
| `stress-test-scenario-designer` | A deteriorating KRI trend should motivate a stress scenario for the appetite review | KRI + trend evidence |
| `enterprise-risk-assessment-builder` | A cluster of KRI breaches should be folded into the enterprise / board risk assessment | `run_id` + exception evidence |
| `risk-control-self-assessment-assistant` | A breach should be linked to the control whose weakness it evidences (RCSA) | KRI + linked control |
| `regulatory-change-impact-analyzer` | A regulatory or appetite change altered a KRI threshold and the library must be re-baselined | affected `kri_id`(s) + config version |

## Human / specialist handoffs (no catalog skill — route to the right role)

- **Disposition of a breach** — risk acceptance, breach waiver, limit/appetite change, risk- or
  control-rating change, appetite-breach declaration, incident/case closure, or regulatory
  filing → the **risk committee, accountable executive, and second-line risk function** through
  their entitled systems, never this monitor.
- **Ambiguous or disputed threshold** (band, direction, or seasonal baseline is unclear, or an
  appetite change moved it) → the **risk-appetite / register owner** to re-confirm and
  re-baseline the versioned KRI library. The monitor never resolves ambiguous thresholds
  itself.

## Upstream (what invokes this skill)

This is a **scheduled monitor** (`aws-fsi-scheduled-agent: read-only-monitoring`): it is
triggered by its schedule (typically at the KRI reporting cadence) or an ad-hoc reviewer run
against a specific KRI set or business unit — not by another skill. The KRI observation feed
and the versioned threshold library are **inputs**, not callers.

## Duplicate-execution prevention

- The monitor computes and evidences **exceptions only**; it must not reach a disposition,
  instruct a risk owner, or take/recommend a risk acceptance, waiver, limit change, or rating
  action — those belong to the human reviewer and the downstream skills.
- Cross-run **deduplication** (fingerprint vs `open_alerts`) prevents the same persistent
  breach (e.g., one under a governance-approved watch) from being re-raised every scheduled
  run; still-open items remain visible as open rather than being silently cleared.
- Downstream skills consume the `run_id` / alert evidence rather than re-deriving thresholds or
  re-screening the whole KRI set.
