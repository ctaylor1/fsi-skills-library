# Adjacent-Skill Handoffs — concentration-risk-monitor

This skill is a **scheduled, read-only, alert-only** monitor. It produces a cited exception
pack (`run_id`) with per-alert `fingerprint`s and stops. It does **not** assess a vendor to a
criticality rating, analyze credit-portfolio quality, design a stress scenario, adjudicate a
breach, waive a limit, or close alerts. Those are human risk-management actions, supported by
the downstream skills below (all present in the catalog).

## Downstream (route the human reviewer to)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `third-party-risk-assessor` | A cloud / AI / technology-provider or operational-dependency concentration needs a full vendor criticality, subcontractor, resilience, and exit-plan assessment | `run_id` + book + provider/dependency bucket |
| `credit-risk-portfolio-analyzer` | A counterparty / sector concentration needs credit-portfolio quality, migration, delinquency, and vintage analysis | `run_id` + book + breached bucket |
| `operational-risk-event-analyzer` | A concentration has materialized (or nearly) as a loss / near-miss and needs root-cause and control-theme analysis | book + affected dependency / event |
| `stress-test-scenario-designer` | The concentration needs a severe-but-plausible scenario, transmission channels, or reverse-stress threshold | breached buckets + limits |
| `liquidity-risk-scenario-analyzer` | A funding / collateral / survival-horizon question arises from a concentration | book + positions in question |
| `market-risk-limit-monitor` | The exception concerns market VaR / sensitivity / position limits rather than concentration buckets | book + market scope |
| `key-risk-indicator-monitor` | A concentration should be tracked as a KRI with trend, seasonality, and threshold commentary | `run_id` + indicator scope |
| `enterprise-risk-assessment-builder` | The exceptions feed a periodic enterprise risk assessment linking risks, controls, and treatment actions | `run_id` + exception evidence |
| `risk-control-self-assessment-assistant` | A control theme behind repeated concentrations needs RCSA design/effectiveness scoring | affected control(s) + evidence |

Remediation itself — reducing/exiting/hedging exposures, blocking or approving onboarding,
migrating or terminating providers, granting or changing limits or waivers, adjudicating or
closing an exception, or filing a regulatory return — is performed by the **enterprise-risk /
credit-risk / resilience officer and the accountable business** through their entitled
systems, never by this monitor.

## Upstream (what invokes this skill)

This is a **scheduled monitor** (`aws-fsi-scheduled-agent: read-only-monitoring`): it is
triggered by its schedule (or an ad-hoc reviewer run), not by another skill. A risk officer
may also run it on demand against a specific book or dimension.

## Duplicate-execution prevention

- The monitor computes and evidences **exceptions only**; it must not reach a disposition,
  assess a vendor to a rating, or adjudicate a breach — those belong to the human reviewer and
  the downstream skills.
- Cross-run **deduplication** (fingerprint vs `open_alerts`) prevents the same persistent
  concentration from being re-raised every scheduled run; still-open items remain visible as
  open rather than being silently cleared.
- Downstream skills consume the `run_id` / alert evidence rather than re-deriving limits or
  re-aggregating the whole exposure book.
